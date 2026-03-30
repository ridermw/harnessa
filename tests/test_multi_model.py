"""Tests for multi-model evaluation framework.

Covers: RunConfig with multiple evaluator models, orchestrator dual-evaluator
dispatch, ScoreReconciler end-to-end, markdown cross-model section, and
telemetry agreement_rate / disagreements fields.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.evaluator import EvaluationResult, Verdict
from harnessa.config import RunConfig, RunMode
from harnessa.orchestrator import Orchestrator
from harnessa.reconciler import ScoreReconciler
from harnessa.reporting.markdown import MarkdownReporter
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    BugReport,
    ModelInfo,
    RunManifest,
    Severity,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_eval(
    scores: list[tuple[str, float]],
    verdict: Verdict = Verdict.PASS,
    bugs: list[BugReport] | None = None,
) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion=name, score=score, justification=f"score={score}")
            for name, score in scores
        ],
        bugs=bugs or [],
        verdict=verdict,
    )


def _make_bug(file: str, line: int) -> BugReport:
    return BugReport(
        id=f"{file}-{line}",
        severity=Severity.MEDIUM,
        description="test bug",
        file=file,
        line=line,
    )


@pytest.fixture()
def benchmark_dir(tmp_path: Path) -> Path:
    bench = tmp_path / "benchmarks" / "test-bench"
    bench.mkdir(parents=True)
    (bench / "TASK.md").write_text("# Test\nDo something", encoding="utf-8")
    (bench / "app.py").write_text("print('hi')", encoding="utf-8")
    eval_dir = bench / "_eval"
    eval_dir.mkdir()
    (eval_dir / "test_app.py").write_text("def test_pass(): assert True", encoding="utf-8")
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
        "    description: Does it work?\n",
        encoding="utf-8",
    )
    return criteria_path


# ---------------------------------------------------------------------------
# 1. RunConfig with multiple evaluator models
# ---------------------------------------------------------------------------


class TestRunConfigMultiModel:
    """RunConfig accepts and defaults evaluator_models correctly."""

    def test_default_evaluator_models(self) -> None:
        config = RunConfig(benchmark="test")
        assert isinstance(config.evaluator_models, list)
        assert len(config.evaluator_models) == 1

    def test_single_evaluator_model(self) -> None:
        config = RunConfig(benchmark="test", evaluator_models=["model-a"])
        assert config.evaluator_models == ["model-a"]

    def test_multiple_evaluator_models(self) -> None:
        config = RunConfig(
            benchmark="test",
            evaluator_models=["model-a", "model-b"],
        )
        assert config.evaluator_models == ["model-a", "model-b"]
        assert len(config.evaluator_models) == 2

    def test_three_evaluator_models(self) -> None:
        config = RunConfig(
            benchmark="test",
            evaluator_models=["m1", "m2", "m3"],
        )
        assert len(config.evaluator_models) == 3


# ---------------------------------------------------------------------------
# 2. Orchestrator dispatches 2 evaluators when >1 model
# ---------------------------------------------------------------------------


class TestOrchestratorDualEvaluator:
    """Orchestrator creates one EvaluatorAgent per model when >1 evaluator model."""

    def test_solo_mode_dual_evaluators(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.SOLO,
            evaluator_models=["model-a", "model-b"],
            criteria_path=criteria_file,
            run_id="multitest01",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_tree"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        eval_call_models: list[str] = []

        with patch.object(orch, "_read_task_prompt", return_value="Do something"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.CriteriaLoader") as mock_loader:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="model-a")

            def make_eval_agent(model_id, work_dir):
                eval_call_models.append(model_id)
                mock_eval = MagicMock()
                mock_eval.agent_id = f"evaluator-{model_id}"
                mock_eval.grade.return_value = _make_eval(
                    [("Functionality", 8.0)], verdict=Verdict.PASS
                )
                mock_eval.get_metrics.return_value = AgentMetrics(model_id=model_id)
                return mock_eval

            mock_eval_cls.side_effect = make_eval_agent
            mock_loader.return_value.load.return_value = []

            manifest = orch.start_run()

            # Verify both evaluator models were used
            assert "model-a" in eval_call_models
            assert "model-b" in eval_call_models
            assert len(eval_call_models) == 2

            # Verify reconciliation data in manifest
            assert manifest.evaluator_agreement_rate is not None
            assert manifest.evaluator_agreement_rate == 1.0
            assert manifest.evaluator_disagreements == []

            # Cleanup
            run_dir = Path(f"runs/{config.run_id}")
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_trio_mode_dual_evaluators(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.TRIO,
            evaluator_models=["model-a", "model-b"],
            criteria_path=criteria_file,
            max_iterations=1,
            run_id="multitest02",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree"
        gen_dir.mkdir(exist_ok=True)
        eval_tree = benchmark_dir / "eval_tree"
        eval_tree.mkdir(exist_ok=True)
        (eval_tree / "_eval").mkdir(exist_ok=True)

        eval_call_models: list[str] = []

        with patch.object(orch, "_read_task_prompt", return_value="Do something"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_plan_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_contract_cls, \
             patch("harnessa.orchestrator.CriteriaLoader") as mock_loader:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            spec_path = benchmark_dir / "spec.md"
            spec_path.write_text("spec", encoding="utf-8")

            mock_plan = mock_plan_cls.return_value
            mock_plan.agent_id = "planner"
            mock_plan.run.return_value = spec_path
            mock_plan.get_metrics.return_value = AgentMetrics(model_id="model-a")

            mock_contract = mock_contract_cls.return_value
            from unittest.mock import PropertyMock
            mock_contract.rounds_completed = 1
            mock_proposal = MagicMock()
            mock_proposal.features = []
            mock_proposal.acceptance_criteria = []
            mock_agreement = MagicMock()
            mock_agreement.approved = True
            mock_agreement.added_criteria = []
            mock_contract.negotiate.return_value = (mock_proposal, mock_agreement)

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="model-a")

            def make_eval_agent(model_id, work_dir):
                eval_call_models.append(model_id)
                mock_eval = MagicMock()
                mock_eval.agent_id = f"evaluator-{model_id}"
                mock_eval.grade.return_value = _make_eval(
                    [("Functionality", 8.0)], verdict=Verdict.PASS
                )
                mock_eval.get_metrics.return_value = AgentMetrics(model_id=model_id)
                return mock_eval

            mock_eval_cls.side_effect = make_eval_agent
            mock_loader.return_value.load.return_value = []

            manifest = orch.start_run()

            # Both evaluator models used in the loop
            assert "model-a" in eval_call_models
            assert "model-b" in eval_call_models

            # Cleanup
            run_dir = Path(f"runs/{config.run_id}")
            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 3. Orchestrator uses single evaluator when 1 model (backward compat)
# ---------------------------------------------------------------------------


class TestOrchestratorSingleEvaluator:
    """Single evaluator model = no reconciler, backward compatible."""

    def test_solo_single_evaluator_no_reconciliation(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.SOLO,
            evaluator_models=["single-model"],
            criteria_path=criteria_file,
            run_id="singletest01",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree"
        gen_dir.mkdir(exist_ok=True)
        eval_tree = benchmark_dir / "eval_tree"
        eval_tree.mkdir(exist_ok=True)
        (eval_tree / "_eval").mkdir(exist_ok=True)

        with patch.object(orch, "_read_task_prompt", return_value="Do something"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.CriteriaLoader") as mock_loader:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="single-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _make_eval(
                [("Functionality", 7.0)], verdict=Verdict.PASS
            )
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="single-model")

            mock_loader.return_value.load.return_value = []

            manifest = orch.start_run()

            # No reconciliation data
            assert manifest.evaluator_agreement_rate is None
            assert manifest.evaluator_disagreements is None
            assert manifest.verdict == "PASS"

            # Cleanup
            run_dir = Path(f"runs/{config.run_id}")
            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 4. ScoreReconciler end-to-end
# ---------------------------------------------------------------------------


class TestScoreReconcilerEndToEnd:
    """Full reconciliation scenarios: agreement, disagreement, one-fails."""

    def test_agreement_case(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 7.0), ("B", 8.0)], verdict=Verdict.PASS)
        eval_b = _make_eval([("A", 7.5), ("B", 8.0)], verdict=Verdict.PASS)
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 1.0
        assert len(result.disagreements) == 0
        assert result.verdict == Verdict.PASS
        scores = {s.criterion: s.score for s in result.final_scores}
        assert scores["A"] == pytest.approx(7.25, abs=0.1)
        assert scores["B"] == 8.0

    def test_disagreement_case(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 9.0), ("B", 8.0)], verdict=Verdict.PASS)
        eval_b = _make_eval([("A", 4.0), ("B", 7.5)], verdict=Verdict.PASS)
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.agreement_rate == 0.5
        assert len(result.disagreements) == 1
        assert result.disagreements[0].criterion == "A"
        scores = {s.criterion: s.score for s in result.final_scores}
        assert scores["A"] == 4.0  # conservative lower
        assert scores["B"] == pytest.approx(7.75, abs=0.1)  # averaged

    def test_one_fails_case(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 8.0)], verdict=Verdict.PASS)
        eval_b = _make_eval([("A", 3.0)], verdict=Verdict.FAIL)
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.verdict == Verdict.FAIL

    def test_both_fail(self) -> None:
        reconciler = ScoreReconciler()
        eval_a = _make_eval([("A", 2.0)], verdict=Verdict.FAIL)
        eval_b = _make_eval([("A", 3.0)], verdict=Verdict.FAIL)
        result = reconciler.reconcile(eval_a, eval_b)

        assert result.verdict == Verdict.FAIL


# ---------------------------------------------------------------------------
# 5. Reconciled result used for verdict in trio mode
# ---------------------------------------------------------------------------


class TestReconciledVerdictInTrio:
    """When reconciler says FAIL, trio mode reports FAIL."""

    def test_trio_fails_when_reconciler_fails(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.TRIO,
            evaluator_models=["model-pass", "model-fail"],
            criteria_path=criteria_file,
            max_iterations=1,
            run_id="reconciletest",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_tree"
        gen_dir.mkdir(exist_ok=True)
        eval_tree = benchmark_dir / "eval_tree"
        eval_tree.mkdir(exist_ok=True)
        (eval_tree / "_eval").mkdir(exist_ok=True)

        with patch.object(orch, "_read_task_prompt", return_value="Do something"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.PlannerAgent") as mock_plan_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_contract_cls, \
             patch("harnessa.orchestrator.CriteriaLoader") as mock_loader:

            mock_iso = mock_iso_cls.return_value
            mock_iso.prepare_generator_worktree.return_value = gen_dir
            mock_iso.prepare_evaluator_worktree.return_value = eval_tree
            orch._isolation = mock_iso

            spec_path = benchmark_dir / "spec.md"
            spec_path.write_text("spec", encoding="utf-8")

            mock_plan = mock_plan_cls.return_value
            mock_plan.agent_id = "planner"
            mock_plan.run.return_value = spec_path
            mock_plan.get_metrics.return_value = AgentMetrics(model_id="model-pass")

            mock_contract = mock_contract_cls.return_value
            mock_contract.rounds_completed = 1
            mock_proposal = MagicMock()
            mock_proposal.features = []
            mock_proposal.acceptance_criteria = []
            mock_agreement = MagicMock()
            mock_agreement.approved = True
            mock_agreement.added_criteria = []
            mock_contract.negotiate.return_value = (mock_proposal, mock_agreement)

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="model-pass")

            eval_idx = [0]

            def make_eval_agent(model_id, work_dir):
                mock_eval = MagicMock()
                mock_eval.agent_id = f"evaluator-{model_id}"
                if model_id == "model-pass":
                    mock_eval.grade.return_value = _make_eval(
                        [("Functionality", 8.0)], verdict=Verdict.PASS
                    )
                else:
                    mock_eval.grade.return_value = _make_eval(
                        [("Functionality", 3.0)], verdict=Verdict.FAIL
                    )
                mock_eval.get_metrics.return_value = AgentMetrics(model_id=model_id)
                return mock_eval

            mock_eval_cls.side_effect = make_eval_agent
            mock_loader.return_value.load.return_value = []

            manifest = orch.start_run()

            # Reconciler should force FAIL when one evaluator says FAIL
            assert manifest.verdict == "FAIL"

            # Cleanup
            run_dir = Path(f"runs/{config.run_id}")
            shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 6. Markdown report includes cross-model section
# ---------------------------------------------------------------------------


class TestMarkdownCrossModelSection:
    """Cross-model section appears when evaluator_agreement_rate is set."""

    def _make_manifest(
        self,
        agreement_rate: float | None = None,
        disagreements: list[dict] | None = None,
    ) -> RunManifest:
        return RunManifest(
            run_id="crosstest",
            benchmark="test-bench",
            mode="trio",
            model_info=[
                ModelInfo(provider="test", model_id="model-a", temperature=0.7, max_tokens=4096),
                ModelInfo(provider="test", model_id="model-b", temperature=0.7, max_tokens=4096),
            ],
            agents=[
                AgentMetrics(model_id="model-a", tokens_in=100, tokens_out=50, cost_usd=0.01),
                AgentMetrics(model_id="model-b", tokens_in=100, tokens_out=50, cost_usd=0.01),
            ],
            scores=[
                BenchmarkScore(criterion="Functionality", score=7.5, justification="Agreed (avg)"),
            ],
            verdict="PASS",
            cost_usd=0.02,
            duration_s=30.0,
            started_at=datetime(2025, 6, 1, 12, 0, 0),
            evaluator_agreement_rate=agreement_rate,
            evaluator_disagreements=disagreements,
        )

    def test_cross_model_section_present(self, tmp_path: Path) -> None:
        manifest = self._make_manifest(
            agreement_rate=0.75,
            disagreements=[
                {"criterion": "Quality", "score_a": 9.0, "score_b": 4.0, "delta": 5.0},
            ],
        )
        reporter = MarkdownReporter()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()

        assert "## Cross-Model Evaluation" in content
        assert "75%" in content
        assert "Quality" in content
        assert "9.0" in content
        assert "4.0" in content
        assert "5.0" in content

    def test_cross_model_section_absent_when_single_model(self, tmp_path: Path) -> None:
        manifest = self._make_manifest(agreement_rate=None, disagreements=None)
        reporter = MarkdownReporter()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()

        assert "## Cross-Model Evaluation" not in content

    def test_cross_model_no_disagreements(self, tmp_path: Path) -> None:
        manifest = self._make_manifest(agreement_rate=1.0, disagreements=[])
        reporter = MarkdownReporter()
        out = tmp_path / "report.md"
        reporter.generate(manifest, out)
        content = out.read_text()

        assert "## Cross-Model Evaluation" in content
        assert "100%" in content
        assert "### Disagreements" not in content


# ---------------------------------------------------------------------------
# 7. Telemetry includes agreement_rate and disagreements
# ---------------------------------------------------------------------------


class TestTelemetryMultiModel:
    """RunManifest serializes/deserializes agreement_rate and disagreements."""

    def test_manifest_with_agreement_rate(self) -> None:
        m = RunManifest(
            run_id="telem01",
            benchmark="test",
            mode="solo",
            evaluator_agreement_rate=0.8,
            evaluator_disagreements=[
                {"criterion": "X", "score_a": 9.0, "score_b": 5.0, "delta": 4.0}
            ],
        )
        assert m.evaluator_agreement_rate == 0.8
        assert len(m.evaluator_disagreements) == 1

    def test_manifest_without_agreement_rate(self) -> None:
        m = RunManifest(
            run_id="telem02",
            benchmark="test",
            mode="solo",
        )
        assert m.evaluator_agreement_rate is None
        assert m.evaluator_disagreements is None

    def test_manifest_json_roundtrip(self) -> None:
        m = RunManifest(
            run_id="telem03",
            benchmark="test",
            mode="trio",
            evaluator_agreement_rate=0.5,
            evaluator_disagreements=[
                {"criterion": "A", "score_a": 8.0, "score_b": 3.0, "delta": 5.0}
            ],
            started_at=datetime(2025, 6, 1, 12, 0, 0),
        )
        json_str = m.model_dump_json()
        restored = RunManifest.model_validate_json(json_str)

        assert restored.evaluator_agreement_rate == 0.5
        assert len(restored.evaluator_disagreements) == 1
        assert restored.evaluator_disagreements[0]["criterion"] == "A"

    def test_manifest_json_null_fields(self) -> None:
        m = RunManifest(
            run_id="telem04",
            benchmark="test",
            mode="solo",
        )
        data = json.loads(m.model_dump_json())
        assert data["evaluator_agreement_rate"] is None
        assert data["evaluator_disagreements"] is None
