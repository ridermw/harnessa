"""Tests for sprint contract negotiation — all agent calls mocked."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harnessa.agents.contract import (
    ContractAgreement,
    ContractNegotiator,
    ContractProposal,
)
from harnessa.agents.evaluator import EvaluationResult, Verdict
from harnessa.agents.executors import ExecutionResult
from harnessa.config import RunConfig, RunMode
from harnessa.orchestrator import Orchestrator
from harnessa.telemetry.models import (
    AgentMetrics,
    BenchmarkScore,
    BugReport,
    ContractMetrics,
    RunManifest,
    Severity,
)


# ---------------------------------------------------------------------------
# Model instantiation tests
# ---------------------------------------------------------------------------


class TestContractProposal:
    """ContractProposal Pydantic model validation."""

    def test_valid_proposal(self) -> None:
        p = ContractProposal(
            features=["Add login endpoint"],
            acceptance_criteria=["Returns 200 on valid creds"],
            files_to_modify=["src/auth.py"],
            estimated_tests=3,
        )
        assert p.features == ["Add login endpoint"]
        assert p.estimated_tests == 3

    def test_empty_lists_allowed(self) -> None:
        p = ContractProposal(
            features=[],
            acceptance_criteria=[],
            files_to_modify=[],
            estimated_tests=0,
        )
        assert p.features == []
        assert p.estimated_tests == 0

    def test_negative_tests_rejected(self) -> None:
        with pytest.raises(Exception):
            ContractProposal(
                features=["x"],
                acceptance_criteria=["y"],
                files_to_modify=["z"],
                estimated_tests=-1,
            )


class TestContractAgreement:
    """ContractAgreement Pydantic model validation."""

    def test_approved_agreement(self) -> None:
        a = ContractAgreement(
            approved=True,
            feedback="",
            added_criteria=["Check edge case"],
            removed_criteria=[],
        )
        assert a.approved is True
        assert a.added_criteria == ["Check edge case"]

    def test_rejected_agreement(self) -> None:
        a = ContractAgreement(
            approved=False,
            feedback="Missing error handling",
            added_criteria=[],
            removed_criteria=["Unnecessary perf test"],
        )
        assert a.approved is False
        assert a.feedback == "Missing error handling"

    def test_defaults(self) -> None:
        a = ContractAgreement(approved=True)
        assert a.feedback == ""
        assert a.added_criteria == []
        assert a.removed_criteria == []


# ---------------------------------------------------------------------------
# Helper: mock agent that returns JSON from run_executor
# ---------------------------------------------------------------------------


def _make_mock_agent(responses: list[str]) -> MagicMock:
    """Create a mock BaseAgent whose run_executor returns successive responses."""
    agent = MagicMock()
    agent.run_executor.side_effect = [
        ExecutionResult(stdout=r, exit_code=0, duration_s=0.1, model="test", success=True)
        for r in responses
    ]
    return agent


def _proposal_json(
    features: list[str] | None = None,
    criteria: list[str] | None = None,
    files: list[str] | None = None,
    tests: int = 3,
) -> str:
    return json.dumps({
        "features": features or ["feat-1", "feat-2"],
        "acceptance_criteria": criteria or ["crit-1", "crit-2"],
        "files_to_modify": files or ["app.py"],
        "estimated_tests": tests,
    })


def _agreement_json(
    approved: bool = True,
    feedback: str = "",
    added: list[str] | None = None,
    removed: list[str] | None = None,
) -> str:
    return json.dumps({
        "approved": approved,
        "feedback": feedback,
        "added_criteria": added or [],
        "removed_criteria": removed or [],
    })


# ---------------------------------------------------------------------------
# Negotiation tests
# ---------------------------------------------------------------------------


class TestNegotiationApprovedRound1:
    """Evaluator approves on round 1 → single round negotiation."""

    def test_single_round(self, tmp_path: Path) -> None:
        gen_agent = _make_mock_agent([_proposal_json()])
        eval_agent = _make_mock_agent([_agreement_json(approved=True)])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        proposal, agreement = negotiator.negotiate("Build a TODO app", tmp_path)

        assert agreement.approved is True
        assert negotiator.rounds_completed == 1
        assert proposal.features == ["feat-1", "feat-2"]
        # Generator called once (proposal), evaluator called once (review)
        assert gen_agent.run_executor.call_count == 1
        assert eval_agent.run_executor.call_count == 1


class TestNegotiationRejectThenApprove:
    """Evaluator rejects round 1, approves round 2 → 2 rounds."""

    def test_two_rounds(self, tmp_path: Path) -> None:
        revised_proposal = _proposal_json(
            features=["feat-1", "feat-2", "error-handling"],
            criteria=["crit-1", "crit-2", "crit-3"],
        )
        gen_agent = _make_mock_agent([
            _proposal_json(),       # round 1 proposal
            revised_proposal,       # round 2 revision
        ])
        eval_agent = _make_mock_agent([
            _agreement_json(approved=False, feedback="Missing error handling"),
            _agreement_json(approved=True, added=["Check 500 response"]),
        ])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        proposal, agreement = negotiator.negotiate("Build a TODO app", tmp_path)

        assert agreement.approved is True
        assert negotiator.rounds_completed == 2
        assert "error-handling" in proposal.features
        # Generator: proposal + revision = 2 calls
        assert gen_agent.run_executor.call_count == 2
        # Evaluator: review + review = 2 calls
        assert eval_agent.run_executor.call_count == 2


class TestNegotiationMaxRoundsReached:
    """Max rounds reached — proceeds with last proposal and warning."""

    def test_max_rounds_proceeds(self, tmp_path: Path) -> None:
        gen_agent = _make_mock_agent([
            _proposal_json(),   # round 1
            _proposal_json(),   # round 2
        ])
        eval_agent = _make_mock_agent([
            _agreement_json(approved=False, feedback="Not good enough"),
            _agreement_json(approved=False, feedback="Still not good"),
        ])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        proposal, agreement = negotiator.negotiate(
            "Build a TODO app", tmp_path, max_rounds=2
        )

        assert agreement.approved is False
        assert negotiator.rounds_completed == 2
        assert proposal.features == ["feat-1", "feat-2"]


# ---------------------------------------------------------------------------
# File output tests
# ---------------------------------------------------------------------------


class TestContractFilesWritten:
    """Contract files written to correct paths."""

    def test_round_1_files(self, tmp_path: Path) -> None:
        gen_agent = _make_mock_agent([_proposal_json()])
        eval_agent = _make_mock_agent([_agreement_json(approved=True)])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        negotiator.negotiate("spec", tmp_path)

        contracts_dir = tmp_path / "contracts"
        assert (contracts_dir / "sprint-1-proposal.md").exists()
        assert (contracts_dir / "sprint-1-agreement.md").exists()

        proposal_content = (contracts_dir / "sprint-1-proposal.md").read_text()
        assert "feat-1" in proposal_content
        assert "Round 1" in proposal_content

        agreement_content = (contracts_dir / "sprint-1-agreement.md").read_text()
        assert "APPROVED" in agreement_content

    def test_round_2_files(self, tmp_path: Path) -> None:
        gen_agent = _make_mock_agent([_proposal_json(), _proposal_json()])
        eval_agent = _make_mock_agent([
            _agreement_json(approved=False, feedback="Needs work"),
            _agreement_json(approved=True),
        ])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        negotiator.negotiate("spec", tmp_path)

        contracts_dir = tmp_path / "contracts"
        assert (contracts_dir / "sprint-1-proposal.md").exists()
        assert (contracts_dir / "sprint-1-agreement.md").exists()
        assert (contracts_dir / "sprint-2-proposal.md").exists()
        assert (contracts_dir / "sprint-2-agreement.md").exists()

        # Round 1 agreement shows REJECTED
        r1_agreement = (contracts_dir / "sprint-1-agreement.md").read_text()
        assert "REJECTED" in r1_agreement


# ---------------------------------------------------------------------------
# JSON parsing edge cases
# ---------------------------------------------------------------------------


class TestJsonParsing:
    """Test JSON extraction from agent output."""

    def test_json_with_markdown_fences(self, tmp_path: Path) -> None:
        """Agent wraps JSON in markdown code fences."""
        wrapped = '```json\n' + _proposal_json() + '\n```'
        gen_agent = _make_mock_agent([wrapped])
        eval_agent = _make_mock_agent([_agreement_json()])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        proposal, _ = negotiator.negotiate("spec", tmp_path)
        assert proposal.features == ["feat-1", "feat-2"]

    def test_json_with_preamble_text(self, tmp_path: Path) -> None:
        """Agent includes explanatory text before JSON."""
        preamble = "Here is my proposal:\n\n" + _proposal_json()
        gen_agent = _make_mock_agent([preamble])
        eval_agent = _make_mock_agent([_agreement_json()])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        proposal, _ = negotiator.negotiate("spec", tmp_path)
        assert proposal.features == ["feat-1", "feat-2"]

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Completely invalid output raises ValueError."""
        gen_agent = _make_mock_agent(["This is not JSON at all"])
        eval_agent = _make_mock_agent([_agreement_json()])

        negotiator = ContractNegotiator(gen_agent, eval_agent)
        with pytest.raises(ValueError, match="Could not parse JSON"):
            negotiator.negotiate("spec", tmp_path)


# ---------------------------------------------------------------------------
# ContractMetrics in RunManifest
# ---------------------------------------------------------------------------


class TestContractMetrics:
    """ContractMetrics model and RunManifest integration."""

    def test_contract_metrics_valid(self) -> None:
        m = ContractMetrics(
            negotiation_rounds=2,
            approved=True,
            features_proposed=3,
            criteria_proposed=4,
            criteria_added_by_evaluator=1,
            duration_s=1.5,
        )
        assert m.negotiation_rounds == 2
        assert m.approved is True
        assert m.duration_s == 1.5

    def test_contract_metrics_in_manifest(self) -> None:
        cm = ContractMetrics(
            negotiation_rounds=1,
            approved=True,
            features_proposed=2,
            criteria_proposed=2,
            criteria_added_by_evaluator=0,
            duration_s=0.5,
        )
        manifest = RunManifest(
            run_id="test-001",
            benchmark="small-bugfix-python",
            mode="trio",
            contract_metrics=cm,
        )
        assert manifest.contract_metrics is not None
        assert manifest.contract_metrics.negotiation_rounds == 1

    def test_manifest_without_contract_metrics(self) -> None:
        manifest = RunManifest(
            run_id="test-002",
            benchmark="small-bugfix-python",
            mode="solo",
        )
        assert manifest.contract_metrics is None

    def test_contract_metrics_serialization(self) -> None:
        cm = ContractMetrics(
            negotiation_rounds=1,
            approved=True,
            features_proposed=2,
            criteria_proposed=3,
            criteria_added_by_evaluator=1,
            duration_s=2.0,
        )
        manifest = RunManifest(
            run_id="test-003",
            benchmark="test",
            mode="trio",
            contract_metrics=cm,
        )
        data = json.loads(manifest.model_dump_json())
        assert data["contract_metrics"]["negotiation_rounds"] == 1
        assert data["contract_metrics"]["approved"] is True


# ---------------------------------------------------------------------------
# Solo mode does NOT call negotiation
# ---------------------------------------------------------------------------


@pytest.fixture()
def benchmark_dir(tmp_path: Path) -> Path:
    """Create a minimal benchmark directory structure."""
    bench = tmp_path / "benchmarks" / "test-bench"
    bench.mkdir(parents=True)
    (bench / "TASK.md").write_text("# Test\nBuild a test app", encoding="utf-8")
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
        "    description: Does the app work?\n",
        encoding="utf-8",
    )
    return criteria_path


def _passing_eval_result(iteration: int = 1) -> EvaluationResult:
    return EvaluationResult(
        scores=[
            BenchmarkScore(criterion="Functionality", score=8.0, justification="Good"),
        ],
        bugs=[],
        verdict=Verdict.PASS,
        iteration=iteration,
    )


class TestSoloModeNoContracts:
    """Solo mode must NOT invoke contract negotiation."""

    def test_solo_no_contract_negotiation(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.SOLO,
            evaluator_models=["test-model"],
            criteria_path=criteria_file,
            max_iterations=1,
            run_id="solo-no-contract",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        with patch.object(orch, "_read_task_prompt", return_value="Build it"), \
             patch("harnessa.orchestrator.IsolationManager") as mock_iso_cls, \
             patch("harnessa.orchestrator.GeneratorAgent") as mock_gen_cls, \
             patch("harnessa.orchestrator.EvaluatorAgent") as mock_eval_cls, \
             patch("harnessa.orchestrator.ContractNegotiator") as mock_negotiator_cls:

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

            # ContractNegotiator should NOT be instantiated in solo mode
            mock_negotiator_cls.assert_not_called()
            assert manifest.contract_metrics is None
            assert manifest.mode == "solo"

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)


# ---------------------------------------------------------------------------
# Trio mode DOES call negotiation
# ---------------------------------------------------------------------------


class TestTrioModeWithContracts:
    """Trio mode invokes contract negotiation between planner and generator loop."""

    def test_trio_includes_contract_negotiation(
        self, benchmark_dir: Path, criteria_file: Path
    ) -> None:
        config = RunConfig(
            benchmark="test-bench",
            mode=RunMode.TRIO,
            evaluator_models=["test-model"],
            criteria_path=criteria_file,
            max_iterations=1,
            run_id="trio-with-contract",
        )
        orch = Orchestrator(config)

        gen_dir = benchmark_dir / "gen_trio"
        gen_dir.mkdir()
        eval_tree = benchmark_dir / "eval_trio"
        eval_tree.mkdir()
        (eval_tree / "_eval").mkdir()

        mock_proposal = ContractProposal(
            features=["feat-1"],
            acceptance_criteria=["crit-1"],
            files_to_modify=["app.py"],
            estimated_tests=2,
        )
        mock_agreement = ContractAgreement(
            approved=True,
            added_criteria=["extra-crit"],
        )

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

            def planner_run(**kwargs):
                p = kwargs.get("output_dir", benchmark_dir) / "planner" / "spec.md"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("spec content", encoding="utf-8")
                return p

            mock_planner = mock_planner_cls.return_value
            mock_planner.agent_id = "planner"
            mock_planner.run.side_effect = planner_run
            mock_planner.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_negotiator = mock_negotiator_cls.return_value
            mock_negotiator.negotiate.return_value = (mock_proposal, mock_agreement)
            mock_negotiator.rounds_completed = 1

            mock_gen = mock_gen_cls.return_value
            mock_gen.agent_id = "generator"
            mock_gen.run.return_value = gen_dir
            mock_gen.get_metrics.return_value = AgentMetrics(model_id="test-model")

            mock_eval = mock_eval_cls.return_value
            mock_eval.agent_id = "evaluator"
            mock_eval.grade.return_value = _passing_eval_result()
            mock_eval.get_metrics.return_value = AgentMetrics(model_id="test-model")

            manifest = orch.start_run()

            mock_negotiator.negotiate.assert_called_once()
            assert manifest.contract_metrics is not None
            assert manifest.contract_metrics.approved is True
            assert manifest.contract_metrics.features_proposed == 1
            assert manifest.contract_metrics.criteria_added_by_evaluator == 1
            assert manifest.mode == "trio"

            shutil.rmtree(Path(f"runs/{config.run_id}"), ignore_errors=True)
