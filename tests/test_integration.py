"""End-to-end integration tests for the orchestrator pipeline — all LLM calls mocked."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    tmp_path: Path,
    criteria_path: Path,
    mode: RunMode = RunMode.TRIO,
    max_iterations: int = 3,
) -> RunConfig:
    return RunConfig(
        benchmark="integ-bench",
        mode=mode,
        evaluator_models=["test-model"],
        criteria_path=criteria_path,
        max_iterations=max_iterations,
        run_id="integ001",
    )


def _passing_eval_result(iteration: int = 1) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion="Functionality", score=8.0, justification="Works"),
            BenchmarkScore(criterion="Code Quality", score=7.0, justification="Clean"),
        ],
        bugs=[],
        verdict=Verdict.PASS,
        iteration=iteration,
    )


def _failing_eval_result(iteration: int = 1) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion="Functionality", score=3.0, justification="Broken"),
            BenchmarkScore(criterion="Code Quality", score=4.0, justification="Messy"),
        ],
        bugs=[
            BugReport(
                id="bug-integ-1",
                severity=Severity.HIGH,
                description="Division by zero in compute()",
                file="app.py",
                line=5,
            ),
        ],
        verdict=Verdict.FAIL,
        iteration=iteration,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def benchmark_dir(tmp_path: Path) -> Path:
    """Create a minimal benchmark with a buggy Python file + test + _eval/ test."""
    bench = tmp_path / "benchmarks" / "integ-bench"
    bench.mkdir(parents=True)

    # TASK.md — the benchmark description
    (bench / "TASK.md").write_text(
        "# Integration Benchmark\n\nFix the division-by-zero in app.py\n",
        encoding="utf-8",
    )

    # Buggy source file
    (bench / "app.py").write_text(
        "def compute(x, y):\n"
        "    return x / y  # BUG: crashes when y == 0\n",
        encoding="utf-8",
    )

    # Project tests (for regression detection)
    tests_dir = bench / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "from app import compute\n\n"
        "def test_basic():\n"
        "    assert compute(10, 2) == 5\n",
        encoding="utf-8",
    )

    # _eval/ test (the evaluator's test suite)
    eval_dir = bench / "_eval"
    eval_dir.mkdir()
    (eval_dir / "test_edge.py").write_text(
        "from app import compute\n\n"
        "def test_zero_division():\n"
        "    assert compute(10, 0) == 0  # should handle gracefully\n",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture()
def criteria_file(tmp_path: Path) -> Path:
    criteria_path = tmp_path / "criteria" / "backend.yaml"
    criteria_path.parent.mkdir(parents=True)
    criteria_path.write_text(
        "criteria:\n"
        "  - name: Functionality\n"
        "    weight: HIGH\n"
        "    threshold: 6\n"
        "    description: Does the fix resolve the bug?\n"
        "  - name: Code Quality\n"
        "    weight: MEDIUM\n"
        "    threshold: 5\n"
        "    description: Is the code clean and minimal?\n",
        encoding="utf-8",
    )
    return criteria_path


def _setup_orchestrator(
    benchmark_dir: Path,
    criteria_file: Path,
    mode: RunMode,
    max_iterations: int = 3,
):
    """Shared setup: create config, orchestrator, worktree dirs, and mock wiring."""
    config = _make_config(benchmark_dir, criteria_file, mode=mode, max_iterations=max_iterations)
    orch = Orchestrator(config)

    gen_dir = benchmark_dir / "gen_tree"
    gen_dir.mkdir(exist_ok=True)
    eval_tree = benchmark_dir / "eval_tree"
    eval_tree.mkdir(exist_ok=True)
    (eval_tree / "_eval").mkdir(exist_ok=True)

    return config, orch, gen_dir, eval_tree


# ---------------------------------------------------------------------------
# Trio mode — full pipeline
# ---------------------------------------------------------------------------


class TestTrioModeIntegration:
    """End-to-end trio mode: planner → generator → evaluator with telemetry."""

    def test_trio_full_pipeline(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config, orch, gen_dir, eval_tree = _setup_orchestrator(
            benchmark_dir, criteria_file, mode=RunMode.TRIO
        )

        planner_called = False
        generator_calls: list[dict] = []

        with patch.object(orch, "_read_task_prompt", return_value="Fix the division-by-zero"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

            # Isolation
            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            # Contract negotiator mock
            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.rounds_completed = 1
            mock_negotiator.negotiate.return_value = (
                MagicMock(features=["f"], acceptance_criteria=["c"], files_to_modify=[], estimated_tests=1),
                MagicMock(approved=True, added_criteria=[], removed_criteria=[]),
            )

            # Planner — writes spec.md
            def planner_run(**kwargs):
                nonlocal planner_called
                planner_called = True
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(
                    "# Spec\n\nHandle y==0 by returning 0 in compute().\n",
                    encoding="utf-8",
                )
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(
                model_id="test-model", tokens_in=50, tokens_out=200, cost_usd=0.01
            )

            # Generator — records call kwargs
            def gen_run(**kwargs):
                generator_calls.append(kwargs)
                return gen_dir

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.side_effect = gen_run
            mock_gen.get_metrics.return_value = AgentMetrics(
                model_id="test-model", tokens_in=200, tokens_out=500, cost_usd=0.02
            )

            # Evaluator — PASS on first try
            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(
                model_id="test-model", tokens_in=300, tokens_out=150, cost_usd=0.015
            )

            manifest = orch.start_run()

            # --- Verify pipeline execution ---
            assert planner_called, "Planner must be called in trio mode"
            mock_planner.run.assert_called_once()
            mock_gen.run.assert_called_once()
            mock_eval.grade.assert_called_once()

            # --- Verify run directory structure ---
            run_dir = Path(f"runs/{config.run_id}")
            assert run_dir.exists()
            for subdir in ("planner", "generator", "evaluations", "telemetry"):
                assert (run_dir / subdir).exists(), f"Missing subdir: {subdir}"

            # --- Verify spec.md was written ---
            spec_file = run_dir / "planner" / "spec.md"
            assert spec_file.exists()
            spec_content = spec_file.read_text(encoding="utf-8")
            assert "Handle y==0" in spec_content

            # --- Verify generator received spec ---
            assert len(generator_calls) == 1
            gen_kwargs = generator_calls[0]
            assert gen_kwargs["spec_path"] == spec_file
            assert gen_kwargs["working_dir"] == gen_dir

            # --- Verify manifest telemetry ---
            manifest_path = run_dir / "telemetry" / "run-manifest.json"
            assert manifest_path.exists()
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

            assert manifest_data["benchmark"] == "integ-bench"
            assert manifest_data["mode"] == "trio"
            assert manifest_data["verdict"] == "PASS"
            assert manifest_data["run_id"] == "integ001"
            assert len(manifest_data["scores"]) == 2
            assert manifest_data["scores"][0]["criterion"] == "Functionality"
            assert manifest_data["scores"][0]["score"] == 8.0

            # --- Verify RunManifest object ---
            assert isinstance(manifest, RunManifest)
            assert manifest.verdict == "PASS"
            assert manifest.benchmark == "integ-bench"
            assert manifest.mode == "trio"

            # --- Verify worktree cleanup was called ---
            mock_iso.cleanup_worktrees.assert_called_once_with(run_dir)

            # Cleanup
            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Solo mode
# ---------------------------------------------------------------------------


class TestSoloModeIntegration:
    """End-to-end solo mode: no planner, generator gets TASK.md content directly."""

    def test_solo_no_planner_generator_gets_task_content(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config, orch, gen_dir, eval_tree = _setup_orchestrator(
            benchmark_dir, criteria_file, mode=RunMode.SOLO
        )

        task_content = "Fix the division-by-zero bug"

        with patch.object(orch, "_read_task_prompt", return_value=task_content), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_planner_cls, \
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

            # Planner was never instantiated
            mock_planner_cls.assert_not_called()

            # Generator was called
            mock_gen.run.assert_called_once()

            # The spec.md in solo mode should contain the task content directly
            run_dir = Path(f"runs/{config.run_id}")
            spec_file = run_dir / "planner" / "spec.md"
            assert spec_file.exists()
            assert spec_file.read_text(encoding="utf-8") == task_content

            # Evaluator ran post-hoc
            mock_eval.grade.assert_called_once()

            # Manifest
            assert manifest.verdict == "PASS"
            assert manifest.mode == "solo"

            manifest_path = run_dir / "telemetry" / "run-manifest.json"
            assert manifest_path.exists()
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert data["mode"] == "solo"
            assert data["benchmark"] == "integ-bench"

            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Retry loop
# ---------------------------------------------------------------------------


class TestRetryLoopIntegration:
    """Evaluator fails on first attempt, passes on second — with feedback."""

    def test_retry_fail_then_pass_with_feedback(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config, orch, gen_dir, eval_tree = _setup_orchestrator(
            benchmark_dir, criteria_file, mode=RunMode.TRIO, max_iterations=3
        )

        eval_call_count = 0
        generator_calls: list[dict] = []

        with patch.object(orch, "_read_task_prompt", return_value="Fix the bug"), \
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

            # Planner
            def planner_run(**kwargs):
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("# Spec\nFix the bug.", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            # Generator — track calls and feedback
            def gen_run(**kwargs):
                generator_calls.append(kwargs)
                return gen_dir

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.side_effect = gen_run
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            # Evaluator — FAIL first, PASS second
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

            # Generator called twice (once per iteration)
            assert mock_gen.run.call_count == 2
            assert len(generator_calls) == 2

            # First call: no feedback
            assert generator_calls[0].get("feedback") is None

            # Second call: has feedback from iteration 1 failure
            feedback_path = generator_calls[1].get("feedback")
            assert feedback_path is not None
            assert feedback_path.exists()
            feedback_content = feedback_path.read_text(encoding="utf-8")
            assert "Functionality" in feedback_content
            assert "Broken" in feedback_content

            # Evaluator called twice
            assert eval_call_count == 2

            # Final verdict is PASS (second iteration succeeded)
            assert manifest.verdict == "PASS"

            # Sprints recorded
            manifest_path = Path(f"runs/{config.run_id}") / "telemetry" / "run-manifest.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            assert len(data["sprints"]) == 2
            assert data["sprints"][0]["iteration"] == 1
            assert data["sprints"][1]["iteration"] == 2

            # Cleanup
            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)
