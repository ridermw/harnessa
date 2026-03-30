"""Tests for orchestrator pipeline wiring — all agents mocked, no real API calls."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from harnessa.agents.evaluator import EvaluationResult, Verdict
from harnessa.config import RunConfig, RunMode
from harnessa.orchestrator import Orchestrator, RunStatus
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    BugReport,
    RunManifest,
    Severity,
    SprintMetrics,
)


@pytest.fixture()
def benchmark_dir(tmp_path: Path) -> Path:
    """Create a minimal benchmark directory structure."""
    bench = tmp_path / "benchmarks" / "test-bench"
    bench.mkdir(parents=True)
    (bench / "TASK.md").write_text("# Test Task\nBuild a test app", encoding="utf-8")
    (bench / "app.py").write_text("print('hello')", encoding="utf-8")
    eval_dir = bench / "_eval"
    eval_dir.mkdir()
    (eval_dir / "test_app.py").write_text("def test_pass(): assert True", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def criteria_file(tmp_path: Path) -> Path:
    """Create a minimal criteria YAML file."""
    criteria_path = tmp_path / "criteria" / "backend.yaml"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(
        "criteria:\n"
        "  - name: Functionality\n"
        "    weight: HIGH\n"
        "    threshold: 6\n"
        "    description: Does the app work?\n"
        "  - name: Code Quality\n"
        "    weight: MEDIUM\n"
        "    threshold: 5\n"
        "    description: Is the code clean?\n",
        encoding="utf-8",
    )
    return criteria_path


def _make_config(
    tmp_path: Path,
    criteria_path: Path,
    mode: RunMode = RunMode.SOLO,
    evaluator_models: list[str] | None = None,
    max_iterations: int = 3,
) -> RunConfig:
    return RunConfig(
        benchmark="test-bench",
        mode=mode,
        evaluator_models=evaluator_models or ["test-model"],
        criteria_path=criteria_path,
        max_iterations=max_iterations,
        run_id="testrun001",
    )


def _passing_eval_result(iteration: int = 1) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion="Functionality", score=8.0, justification="Good"),
            BenchmarkScore(criterion="Code Quality", score=7.0, justification="Clean"),
        ],
        bugs=[],
        verdict=Verdict.PASS,
        iteration=iteration,
    )


def _failing_eval_result(iteration: int = 1) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion="Functionality", score=4.0, justification="Broken"),
            BenchmarkScore(criterion="Code Quality", score=3.0, justification="Messy"),
        ],
        bugs=[
            BugReport(
                id="bug1",
                severity=Severity.HIGH,
                description="Crash on startup",
                file="app.py",
                line=10,
            ),
        ],
        verdict=Verdict.FAIL,
        iteration=iteration,
    )


class TestRunDirectoryCreation:
    """Test that run directories are created with proper structure."""

    def test_run_dirs_created(self, benchmark_dir: Path, criteria_file: Path) -> None:
        config = _make_config(benchmark_dir, criteria_file)
        orch = Orchestrator(config)

        with patch.object(orch, "_read_task_prompt", return_value="Build a test app"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = benchmark_dir / "gen"
            mock_iso.prepare_evaluator_worktree.return_value = benchmark_dir / "eval"
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = benchmark_dir / "gen"
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            (benchmark_dir / "gen").mkdir(exist_ok=True)

            manifest = orch.start_run()

            run_dir = Path(f"runs/{config.run_id}")
            assert run_dir.exists()
            for subdir in ("planner", "generator", "evaluations", "telemetry"):
                assert (run_dir / subdir).exists()

            # Cleanup
            shutil.rmtree(run_dir, ignore_errors=True)


class TestSoloModePipeline:
    """Test solo mode: generator + evaluator, no planner."""

    def test_solo_calls_generator_and_evaluator(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file, mode=RunMode.SOLO)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_tree"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            mock_gen.run.assert_called_once()
            mock_eval.grade.assert_called_once()
            assert manifest.verdict == "PASS"
            assert manifest.mode == "solo"

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)

    def test_solo_no_planner_called(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file, mode=RunMode.SOLO)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree2"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_tree2"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            mock_planner_cls.assert_not_called()

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestTrioModePipeline:
    """Test trio mode: planner → generator ↔ evaluator loop."""

    def test_trio_call_order(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        """Planner is called first, then generator, then evaluator."""
        config = _make_config(benchmark_dir, criteria_file, mode=RunMode.TRIO)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_trio"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_trio"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()
        spec_path = benchmark_dir / "spec.md"

        call_log: list[str] = []

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.rounds_completed = 1
            mock_negotiator.negotiate.return_value = (
                MagicMock(features=["f"], acceptance_criteria=["c"], files_to_modify=[], estimated_tests=1),
                MagicMock(approved=True, added_criteria=[], removed_criteria=[]),
            )

            def planner_run(**kwargs):
                call_log.append("planner")
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("spec content", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            def gen_run(**kwargs):
                call_log.append("generator")
                return gen_dir

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.side_effect = gen_run
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            def eval_grade(**kwargs):
                call_log.append("evaluator")
                return _passing_eval_result()

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.side_effect = eval_grade
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            assert call_log == ["planner", "generator", "evaluator"]
            assert manifest.verdict == "PASS"
            assert manifest.mode == "trio"

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestRetryLoop:
    """Test GAN-loop retry: evaluator fails → feedback → evaluator passes."""

    def test_retry_on_failure_then_pass(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(
            benchmark_dir, criteria_file, mode=RunMode.TRIO, max_iterations=3
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_retry"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_retry"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        eval_call_count = 0

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.rounds_completed = 1
            mock_negotiator.negotiate.return_value = (
                MagicMock(features=["f"], acceptance_criteria=["c"], files_to_modify=[], estimated_tests=1),
                MagicMock(approved=True, added_criteria=[], removed_criteria=[]),
            )

            def planner_run(**kwargs):
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("spec", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            def eval_grade(**kwargs):
                nonlocal eval_call_count
                eval_call_count += 1
                if eval_call_count == 1:
                    return _failing_eval_result(iteration=1)
                return _passing_eval_result(iteration=2)

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.side_effect = eval_grade
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            assert manifest.verdict == "PASS"
            assert eval_call_count == 2
            # Generator called twice (once per iteration)
            assert mock_gen.run.call_count == 2

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)

    def test_max_iterations_reached_fail(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(
            benchmark_dir, criteria_file, mode=RunMode.TRIO, max_iterations=2
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_maxiter"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_maxiter"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.rounds_completed = 1
            mock_negotiator.negotiate.return_value = (
                MagicMock(features=["f"], acceptance_criteria=["c"], files_to_modify=[], estimated_tests=1),
                MagicMock(approved=True, added_criteria=[], removed_criteria=[]),
            )

            def planner_run(**kwargs):
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("spec", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _failing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            assert manifest.verdict == "FAIL"
            assert mock_gen.run.call_count == 2
            assert mock_eval.grade.call_count == 2

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestCrossModelReconciliation:
    """Test cross-model evaluation with score reconciliation."""

    def test_two_evaluators_reconciled(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(
            benchmark_dir,
            criteria_file,
            mode=RunMode.TRIO,
            evaluator_models=["model-a", "model-b"],
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_cross"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_cross"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        eval_call_count = 0

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ScoreReconciler") as mock_reconciler_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.rounds_completed = 1
            mock_negotiator.negotiate.return_value = (
                MagicMock(features=["f"], acceptance_criteria=["c"], files_to_modify=[], estimated_tests=1),
                MagicMock(approved=True, added_criteria=[], removed_criteria=[]),
            )

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            def planner_run(**kwargs):
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("spec", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            def eval_grade(**kwargs):
                nonlocal eval_call_count
                eval_call_count += 1
                return _passing_eval_result()

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.side_effect = eval_grade
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            from harnessa.reconciler import ReconciledResult
            mock_reconciled = ReconciledResult(
                final_scores=[
                    BenchmarkScore(criterion="Functionality", score=8.0, justification="Agreed"),
                    BenchmarkScore(criterion="Code Quality", score=7.0, justification="Agreed"),
                ],
                final_bugs=[],
                verdict=Verdict.PASS,
                agreement_rate=1.0,
            )
            mock_reconciler = mock_reconciler_cls.return_value
            mock_reconciler.reconcile.return_value = mock_reconciled

            manifest = orch.start_run()

            # Two evaluator models → 2 evaluator calls per iteration
            assert eval_call_count == 2
            mock_reconciler.reconcile.assert_called_once()
            assert manifest.verdict == "PASS"

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestTelemetryManifest:
    """Test that the telemetry manifest is written correctly."""

    def test_manifest_written_with_correct_structure(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_telem"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_telem"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(
                model_id="test-model", tokens_in=100, tokens_out=200, cost_usd=0.01
            )

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(
                model_id="test-model", tokens_in=50, tokens_out=100, cost_usd=0.005
            )

            manifest = orch.start_run()

            manifest_path = Path(f"runs/{config.run_id}/telemetry/run-manifest.json")
            assert manifest_path.exists()

            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert data["run_id"] == config.run_id
            assert data["benchmark"] == "test-bench"
            assert data["mode"] == "solo"
            assert data["verdict"] == "PASS"
            assert len(data["agents"]) == 2
            assert len(data["scores"]) == 2
            assert data["cost_usd"] > 0
            assert data["duration_s"] >= 0
            assert data["started_at"] is not None
            assert data["finished_at"] is not None

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestArtifactSnapshot:
    """Test that artifact snapshots are saved for replay."""

    def test_artifact_snapshot_saved(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_snapshot"
        gen_dir.mkdir()
        (gen_dir / "app.py").write_text("print('hello')", encoding="utf-8")
        eval_tree = benchmark_dir / "eval_snapshot"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            artifacts_dir = Path(f"runs/{config.run_id}/artifacts")
            assert artifacts_dir.exists()
            assert (artifacts_dir / "app.py").exists()

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


class TestCleanup:
    """Test that cleanup fires on both success and failure."""

    def test_cleanup_on_success(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_clean"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_clean"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            mock_iso.cleanup_worktrees.assert_called_once()

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)

    def test_cleanup_on_failure(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = _make_config(benchmark_dir, criteria_file)
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_fail_clean"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_fail_clean"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.side_effect = RuntimeError("Generation failed!")
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            with pytest.raises(RuntimeError, match="Generation failed"):
                orch.start_run()

            mock_iso.cleanup_worktrees.assert_called_once()

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)
