"""Orchestrator — manages the full pipeline lifecycle for a benchmark run."""

from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import time
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from harnessa.agents.contract import ContractNegotiator
from harnessa.agents.evaluator import EvaluationResult, EvaluatorAgent, Verdict
from harnessa.agents.generator import GeneratorAgent
from harnessa.agents.isolation import IsolationManager
from harnessa.agents.planner import PlannerAgent
from harnessa.config import RunConfig, RunMode
from harnessa.criteria.loader import CriteriaLoader
from harnessa.reconciler import ScoreReconciler
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    ContractMetrics,
    RunManifest,
    RunValidity,
)

logger = logging.getLogger(__name__)

_RUN_SUBDIRS = ("planner", "generator", "evaluations", "telemetry")


class RunStatus(StrEnum):
    """Status values written to the .status file."""

    RUNNING = "running"
    ERROR = "error"
    DONE = "done"


class Orchestrator:
    """Manages the pipeline lifecycle for a single benchmark run.

    Responsibilities:
    - Create run directories and prepare worktrees
    - Execute solo or trio mode pipelines
    - Collect telemetry and write RunManifest
    - Handle cleanup on success and failure
    """

    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self._run_dir = (Path("runs") / config.run_id).resolve()
        self._isolation = IsolationManager()
        self._original_sigint: signal.Handlers | None = None
        self._reconciled_result: Any = None
        self._last_eval_result: EvaluationResult | None = None

    def start_run(self) -> RunManifest:
        """Execute the full pipeline and return the RunManifest."""
        started_at = datetime.now()
        run_start = time.monotonic()

        logger.info(
            "Starting run %s (benchmark=%s, mode=%s)",
            self.config.run_id,
            self.config.benchmark,
            self.config.mode,
        )

        # 1. Create run directory structure
        self._create_run_dirs()
        self._install_signal_handler()
        self._write_status(RunStatus.RUNNING)

        # 2. Load criteria
        criteria = CriteriaLoader().load(self.config.criteria_path)

        # 3. Prepare worktrees
        benchmark_path = (Path("benchmarks") / self.config.benchmark).resolve()
        gen_worktree = self._isolation.prepare_generator_worktree(
            benchmark_path, self._run_dir
        )
        eval_worktree = self._isolation.prepare_evaluator_worktree(
            benchmark_path, self._run_dir
        )

        all_agent_metrics: list[AgentMetrics] = []
        final_scores: list[BenchmarkScore] = []
        final_bugs: list = []
        verdict = "FAIL"
        sprints: list = []
        contract_metrics: ContractMetrics | None = None
        self._last_eval_result = None

        try:
            if self.config.mode == RunMode.TRIO:
                verdict, final_scores, final_bugs, sprints, all_agent_metrics, contract_metrics = (
                    self._run_trio_mode(gen_worktree, eval_worktree, criteria)
                )
            else:
                verdict, final_scores, final_bugs, all_agent_metrics = (
                    self._run_solo_mode(gen_worktree, eval_worktree, criteria)
                )

            self._write_status(RunStatus.DONE)

        except Exception:
            self._write_status(RunStatus.ERROR)
            logger.exception("Run %s failed", self.config.run_id)
            raise

        finally:
            self._restore_signal_handler()
            try:
                self._isolation.cleanup_worktrees(self._run_dir)
            except Exception:
                logger.warning("Worktree cleanup failed")

        # 6. Build manifest
        total_cost = sum(a.cost_usd for a in all_agent_metrics)
        total_duration = time.monotonic() - run_start

        # Extract cross-model reconciliation data if available
        evaluator_agreement_rate: float | None = None
        evaluator_disagreements: list[dict] | None = None
        if self._reconciled_result is not None:
            evaluator_agreement_rate = self._reconciled_result.agreement_rate
            evaluator_disagreements = [
                {
                    "criterion": d.criterion,
                    "score_a": d.score_a,
                    "score_b": d.score_b,
                    "delta": d.delta,
                }
                for d in self._reconciled_result.disagreements
            ]

        manifest = RunManifest(
            run_id=self.config.run_id,
            benchmark=self.config.benchmark,
            mode=self.config.mode.value,
            agents=all_agent_metrics,
            scores=final_scores,
            bugs=final_bugs,
            sprints=sprints,
            contract_metrics=contract_metrics,
            visible_tests=self._last_eval_result.regression_result if self._last_eval_result else None,
            eval_tests=self._last_eval_result.test_suite_result if self._last_eval_result else None,
            run_validity=self._derive_run_validity(self._last_eval_result),
            cost_usd=total_cost,
            duration_s=round(total_duration, 2),
            verdict=verdict,
            started_at=started_at,
            finished_at=datetime.now(),
            evaluator_agreement_rate=evaluator_agreement_rate,
            evaluator_disagreements=evaluator_disagreements,
        )

        # 7. Write manifest
        telemetry_dir = self._run_dir / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = telemetry_dir / "run-manifest.json"
        self._atomic_write(
            manifest_path, manifest.model_dump_json(indent=2)
        )
        logger.info("Wrote manifest to %s", manifest_path)

        return manifest

    # ------------------------------------------------------------------
    # Mode implementations
    # ------------------------------------------------------------------

    def _run_solo_mode(
        self,
        gen_worktree: Path,
        eval_worktree: Path,
        criteria: list,
    ) -> tuple[str, list[BenchmarkScore], list, list[AgentMetrics]]:
        """Solo mode: generator → evaluator(s) (no planner, no iteration)."""
        all_metrics: list[AgentMetrics] = []

        # Read task prompt
        task_prompt = self._read_task_prompt()

        # Run generator directly with task prompt
        generator = GeneratorAgent(
            model_id=self.config.evaluator_models[0],
            work_dir=gen_worktree,
        )
        spec_path = self._run_dir / "planner" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(task_prompt, encoding="utf-8")

        gen_result = self._launch_agent(
            generator, "run",
            spec_path=spec_path,
            working_dir=gen_worktree,
            output_dir=self._run_dir,
        )
        all_metrics.append(generator.get_metrics())

        # Save artifact snapshot
        self._save_artifact_snapshot(gen_worktree)

        # Run evaluator(s)
        eval_dir = eval_worktree / "_eval"
        eval_results: list[EvaluationResult] = []
        for model_id in self.config.evaluator_models:
            evaluator = EvaluatorAgent(
                model_id=model_id,
                work_dir=eval_worktree,
            )
            eval_result: EvaluationResult = self._launch_agent(
                evaluator, "grade",
                code_dir=gen_worktree,
                eval_dir=eval_dir,
                criteria_path=self.config.criteria_path,
                output_dir=self._run_dir,
            )
            eval_results.append(eval_result)
            all_metrics.append(evaluator.get_metrics())

        # Cross-model reconciliation
        if len(eval_results) > 1:
            reconciler = ScoreReconciler()
            reconciled = reconciler.reconcile(eval_results[0], eval_results[1])
            self._reconciled_result = reconciled
            self._last_eval_result = eval_results[0]
            return (
                reconciled.verdict.value,
                reconciled.final_scores,
                reconciled.final_bugs,
                all_metrics,
            )

        self._reconciled_result = None
        self._last_eval_result = eval_results[0]
        return (
            eval_results[0].verdict.value,
            eval_results[0].scores,
            eval_results[0].bugs,
            all_metrics,
        )

    def _run_trio_mode(
        self,
        gen_worktree: Path,
        eval_worktree: Path,
        criteria: list,
    ) -> tuple[str, list[BenchmarkScore], list, list, list[AgentMetrics], ContractMetrics | None]:
        """Trio mode: planner → contract negotiation → (generator ↔ evaluator) loop."""
        all_metrics: list[AgentMetrics] = []
        sprints: list = []

        # a. Run PlannerAgent
        task_prompt = self._read_task_prompt()
        planner = PlannerAgent(
            model_id=self.config.evaluator_models[0],
            work_dir=self._run_dir,
        )
        spec_path: Path = self._launch_agent(
            planner, "run",
            prompt=task_prompt,
            output_dir=self._run_dir,
        )
        all_metrics.append(planner.get_metrics())
        spec_text = spec_path.read_text(encoding="utf-8")

        # b. Contract negotiation
        contract_metrics: ContractMetrics | None = None
        generator_for_contract = GeneratorAgent(
            model_id=self.config.evaluator_models[0],
            work_dir=gen_worktree,
        )
        evaluator_for_contract = EvaluatorAgent(
            model_id=self.config.evaluator_models[0],
            work_dir=eval_worktree,
        )
        negotiator = ContractNegotiator(generator_for_contract, evaluator_for_contract)

        contract_start = time.monotonic()
        proposal, agreement = negotiator.negotiate(spec_text, self._run_dir)
        contract_duration = time.monotonic() - contract_start

        contract_metrics = ContractMetrics(
            negotiation_rounds=negotiator.rounds_completed,
            approved=agreement.approved,
            features_proposed=len(proposal.features),
            criteria_proposed=len(proposal.acceptance_criteria),
            criteria_added_by_evaluator=len(agreement.added_criteria),
            duration_s=round(contract_duration, 2),
        )

        # c. Iteration loop
        eval_dir = eval_worktree / "_eval"
        feedback_path: Path | None = None
        final_eval: EvaluationResult | None = None

        for iteration in range(1, self.config.max_iterations + 1):
            iter_start = time.monotonic()

            # Generator
            generator = GeneratorAgent(
                model_id=self.config.evaluator_models[0],
                work_dir=gen_worktree,
            )
            self._launch_agent(
                generator, "run",
                spec_path=spec_path,
                working_dir=gen_worktree,
                output_dir=self._run_dir,
                feedback=feedback_path,
            )
            all_metrics.append(generator.get_metrics())

            # Evaluator(s)
            eval_results: list[EvaluationResult] = []
            for model_id in self.config.evaluator_models:
                evaluator = EvaluatorAgent(
                    model_id=model_id,
                    work_dir=eval_worktree,
                )
                result: EvaluationResult = self._launch_agent(
                    evaluator, "grade",
                    code_dir=gen_worktree,
                    eval_dir=eval_dir,
                    criteria_path=self.config.criteria_path,
                    output_dir=self._run_dir,
                    iteration=iteration,
                )
                eval_results.append(result)
                all_metrics.append(evaluator.get_metrics())

            # Cross-model reconciliation
            if len(eval_results) > 1:
                reconciler = ScoreReconciler()
                reconciled = reconciler.reconcile(eval_results[0], eval_results[1])
                self._reconciled_result = reconciled
                current_scores = reconciled.final_scores
                current_bugs = reconciled.final_bugs
                current_verdict = reconciled.verdict.value
            else:
                self._reconciled_result = None
                current_scores = eval_results[0].scores
                current_bugs = eval_results[0].bugs
                current_verdict = eval_results[0].verdict.value

            final_eval = eval_results[0]
            self._last_eval_result = final_eval

            from harnessa.telemetry.models import SprintMetrics
            sprints.append(SprintMetrics(
                iteration=iteration,
                scores=current_scores,
                bugs_found=len(current_bugs),
                duration_s=round(time.monotonic() - iter_start, 2),
            ))

            # Check verdict
            if current_verdict == "PASS":
                # Save artifact snapshot on success
                self._save_artifact_snapshot(gen_worktree)
                return (
                    "PASS",
                    current_scores,
                    current_bugs,
                    sprints,
                    all_metrics,
                    contract_metrics,
                )

            # FAIL: write feedback for next iteration
            feedback_path = self._run_dir / "generator" / f"feedback_iter{iteration}.md"
            feedback_path.parent.mkdir(parents=True, exist_ok=True)
            feedback_lines = []
            for s in current_scores:
                feedback_lines.append(
                    f"- {s.criterion}: {s.score}/10 — {s.justification}"
                )
            for b in current_bugs:
                feedback_lines.append(
                    f"- BUG [{b.severity}] {b.description} ({b.file}:{b.line})"
                )
            feedback_path.write_text("\n".join(feedback_lines), encoding="utf-8")

        # Max iterations reached — FAIL
        self._save_artifact_snapshot(gen_worktree)
        return (
            "FAIL",
            current_scores,
            current_bugs,
            sprints,
            all_metrics,
            contract_metrics,
        )

    def _derive_run_validity(self, result: EvaluationResult | None) -> RunValidity:
        """Determine whether the final verdict is backed by trustworthy test evidence."""
        if result is None:
            return RunValidity.TAINTED

        suites = [result.test_suite_result]
        if result.regression_result is not None:
            suites.append(result.regression_result)

        if any(suite is not None and not suite.execution_ok for suite in suites):
            return RunValidity.HARNESS_ERROR
        return RunValidity.CLEAN

    # ------------------------------------------------------------------
    # Agent launcher
    # ------------------------------------------------------------------

    def _launch_agent(self, agent: Any, method: str, **kwargs: Any) -> Any:
        """Run an agent method with timing and error capture."""
        start = time.monotonic()
        try:
            fn = getattr(agent, method)
            result = fn(**kwargs)
            elapsed = time.monotonic() - start
            logger.info(
                "[%s] %s completed in %.2fs",
                getattr(agent, "agent_id", "unknown"),
                method,
                elapsed,
            )
            return result
        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error(
                "[%s] %s failed after %.2fs: %s",
                getattr(agent, "agent_id", "unknown"),
                method,
                elapsed,
                exc,
            )
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_run_dirs(self) -> None:
        """Create run directory with standard subdirectories."""
        for subdir in _RUN_SUBDIRS:
            (self._run_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _read_task_prompt(self) -> str:
        """Read TASK.md from the benchmark directory."""
        task_path = Path(f"benchmarks/{self.config.benchmark}/TASK.md")
        if not task_path.exists():
            raise FileNotFoundError(f"TASK.md not found: {task_path}")
        return task_path.read_text(encoding="utf-8")

    def _save_artifact_snapshot(self, gen_worktree: Path) -> None:
        """Copy the generator worktree to artifacts/ for replay."""
        artifacts_dir = self._run_dir / "artifacts"
        if artifacts_dir.exists():
            shutil.rmtree(artifacts_dir)
        shutil.copytree(gen_worktree, artifacts_dir)
        logger.info("Artifact snapshot saved to %s", artifacts_dir)

    def _write_status(self, status: RunStatus) -> None:
        """Write run status atomically."""
        status_file = self._run_dir / ".status"
        self._atomic_write(status_file, status.value)
        if status in (RunStatus.DONE, RunStatus.ERROR):
            done_marker = self._run_dir / ".done"
            done_marker.touch()

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write content atomically: write to temp file, then rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.rename(path)

    def _install_signal_handler(self) -> None:
        """Install Ctrl+C handler for graceful shutdown."""
        self._original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _restore_signal_handler(self) -> None:
        """Restore the original SIGINT handler."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """Gracefully shut down on Ctrl+C."""
        logger.warning("Ctrl+C received — shutting down")
        self._write_status(RunStatus.ERROR)
        try:
            self._isolation.cleanup_worktrees(self._run_dir)
        except Exception:
            pass
        raise KeyboardInterrupt
