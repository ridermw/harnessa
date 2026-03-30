"""Evaluator consistency — same artifact scored multiple times should produce similar scores."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from unittest.mock import patch

import pytest

from harnessa.agents.evaluator import EvaluatorAgent, EvaluationResult, SuiteResult, Verdict
from harnessa.criteria.loader import Criterion, Weight
from harnessa.telemetry.models import BenchmarkScore, CanonicalResponse


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def agent(tmp_path: Path) -> EvaluatorAgent:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return EvaluatorAgent(model_id="test-model", work_dir=work_dir)


@pytest.fixture()
def criteria_file(tmp_path: Path) -> Path:
    path = tmp_path / "criteria.yaml"
    path.write_text(
        "criteria:\n"
        "  - name: Functionality\n"
        "    weight: HIGH\n"
        "    threshold: 6\n"
        "    description: Does the fix resolve the bug?\n"
        "  - name: Code Quality\n"
        "    weight: MEDIUM\n"
        "    threshold: 5\n"
        "    description: Is the code clean?\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Slightly varied LLM responses (simulating natural LLM variance)
# ---------------------------------------------------------------------------

_VARIED_RESPONSES = [
    {
        "scores": [
            {"criterion": "Functionality", "score": 7, "justification": "Fix works, tests pass"},
            {"criterion": "Code Quality", "score": 7, "justification": "Clean and minimal"},
        ],
        "bugs": [
            {"id": "b1", "severity": "low", "description": "Missing docstring on compute()", "file": "app.py", "line": 1},
        ],
    },
    {
        "scores": [
            {"criterion": "Functionality", "score": 8, "justification": "All tests pass, edge cases handled"},
            {"criterion": "Code Quality", "score": 8, "justification": "Well-structured code"},
        ],
        "bugs": [
            {"id": "b1", "severity": "low", "description": "Missing docstring on compute()", "file": "app.py", "line": 1},
        ],
    },
    {
        "scores": [
            {"criterion": "Functionality", "score": 7, "justification": "Fix resolves the bug correctly"},
            {"criterion": "Code Quality", "score": 7, "justification": "Follows conventions"},
        ],
        "bugs": [
            {"id": "b1", "severity": "low", "description": "Missing docstring on compute()", "file": "app.py", "line": 1},
        ],
    },
]


def _make_canonical(data: dict) -> CanonicalResponse:
    return CanonicalResponse(
        text=json.dumps(data),
        stop_reason="end_turn",
        model="test-model",
        tokens_in=100,
        tokens_out=200,
        cost=0.005,
        truncated=False,
    )


def _setup_workspace(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    code_dir = tmp_path / f"code_{tag}"
    code_dir.mkdir(parents=True)
    eval_dir = tmp_path / f"eval_{tag}"
    eval_dir.mkdir(parents=True)
    (code_dir / "app.py").write_text(
        "def compute(x, y):\n"
        "    if y == 0:\n"
        "        return 0\n"
        "    return x / y\n",
        encoding="utf-8",
    )
    return code_dir, eval_dir


def _mock_subprocess(stdout: str, returncode: int):
    return type("Result", (), {
        "stdout": stdout, "stderr": "", "returncode": returncode
    })()


# ---------------------------------------------------------------------------
# Consistency tests
# ---------------------------------------------------------------------------


class TestEvaluatorConsistency:
    """Score the same artifact 3x, verify low variance."""

    def _run_evaluator_n_times(
        self,
        n: int,
        tmp_path: Path,
        agent: EvaluatorAgent,
        criteria_file: Path,
        responses: list[dict],
        test_stdout: str = "2 passed, 0 failed",
        test_returncode: int = 0,
    ) -> list[EvaluationResult]:
        """Run the evaluator N times with different mocked LLM responses."""
        results: list[EvaluationResult] = []
        for i in range(n):
            code_dir, eval_dir = _setup_workspace(tmp_path, f"run-{i}")
            # Each run uses a unique output dir to avoid file conflicts
            output_dir = tmp_path / f"output-{i}"
            output_dir.mkdir()

            response = responses[i % len(responses)]
            with patch.object(agent, "call_llm", return_value=_make_canonical(response)), \
                 patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
                mock_sub.return_value = _mock_subprocess(test_stdout, test_returncode)

                result = agent.grade(
                    code_dir=code_dir,
                    eval_dir=eval_dir,
                    criteria_path=criteria_file,
                    output_dir=output_dir,
                )
            results.append(result)
        return results

    def test_scores_consistent_across_runs(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Run evaluator 3x on identical code with slightly varied LLM responses.
        Assert per-criterion std dev < 1.5."""
        results = self._run_evaluator_n_times(
            3, tmp_path, agent, criteria_file, _VARIED_RESPONSES,
        )

        # Collect scores per criterion
        scores_by_criterion: dict[str, list[float]] = {}
        for result in results:
            for score in result.scores:
                scores_by_criterion.setdefault(score.criterion, []).append(score.score)

        assert len(scores_by_criterion) > 0, "Should have scores for at least one criterion"

        for criterion, scores in scores_by_criterion.items():
            assert len(scores) == 3, f"Expected 3 scores for {criterion}"
            stddev = statistics.stdev(scores)
            assert stddev < 1.5, (
                f"{criterion}: stddev {stddev:.2f} >= 1.5 — scores too inconsistent: {scores}"
            )

    def test_verdict_consistent(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Same artifact should produce same verdict across runs."""
        results = self._run_evaluator_n_times(
            3, tmp_path, agent, criteria_file, _VARIED_RESPONSES,
        )

        verdicts = [r.verdict for r in results]
        assert len(set(verdicts)) == 1, (
            f"Verdict inconsistency across runs: {verdicts}"
        )
        # All runs should PASS since scores are 7+ and thresholds are 6/5
        assert verdicts[0] == Verdict.PASS

    def test_bug_detection_consistent(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """Same bugs found across runs (at least 70% overlap).
        Compare bug descriptions via Jaccard similarity."""
        results = self._run_evaluator_n_times(
            3, tmp_path, agent, criteria_file, _VARIED_RESPONSES,
        )

        # Extract normalized bug descriptions per run
        bug_sets: list[set[str]] = []
        for result in results:
            # Normalize: lowercase, strip, take first 40 chars for fuzzy match
            bugs = {b.description.lower().strip()[:40] for b in result.bugs}
            bug_sets.append(bugs)

        # Pairwise Jaccard similarity
        for i in range(len(bug_sets)):
            for j in range(i + 1, len(bug_sets)):
                if not bug_sets[i] and not bug_sets[j]:
                    continue  # both empty = consistent
                union = bug_sets[i] | bug_sets[j]
                intersection = bug_sets[i] & bug_sets[j]
                jaccard = len(intersection) / len(union) if union else 1.0
                assert jaccard >= 0.7, (
                    f"Bug overlap between run {i} and run {j} too low: "
                    f"Jaccard={jaccard:.2f}, bugs_i={bug_sets[i]}, bugs_j={bug_sets[j]}"
                )


class TestConsistencyWithFailingTests:
    """Consistency when tests fail — verdict should always be FAIL."""

    def test_failing_verdict_consistent(
        self, tmp_path: Path, agent: EvaluatorAgent, criteria_file: Path,
    ) -> None:
        """When tests fail and scores are low, FAIL verdict is consistent."""
        failing_responses = [
            {
                "scores": [
                    {"criterion": "Functionality", "score": 3, "justification": "Tests fail"},
                    {"criterion": "Code Quality", "score": 4, "justification": "Broken code"},
                ],
                "bugs": [{"id": "b1", "severity": "high", "description": "Main bug persists", "file": "app.py", "line": 2}],
            },
            {
                "scores": [
                    {"criterion": "Functionality", "score": 2, "justification": "Multiple failures"},
                    {"criterion": "Code Quality", "score": 3, "justification": "Poor quality"},
                ],
                "bugs": [{"id": "b1", "severity": "critical", "description": "Main bug persists", "file": "app.py", "line": 2}],
            },
            {
                "scores": [
                    {"criterion": "Functionality", "score": 3, "justification": "Not working"},
                    {"criterion": "Code Quality", "score": 4, "justification": "Needs work"},
                ],
                "bugs": [{"id": "b1", "severity": "high", "description": "Main bug still present", "file": "app.py", "line": 2}],
            },
        ]

        results: list[EvaluationResult] = []
        for i, resp in enumerate(failing_responses):
            code_dir, eval_dir = _setup_workspace(tmp_path, f"fail-{i}")
            output_dir = tmp_path / f"fail-output-{i}"
            output_dir.mkdir()

            with patch.object(agent, "call_llm", return_value=_make_canonical(resp)), \
                 patch("harnessa.agents.evaluator.subprocess.run") as mock_sub:
                mock_sub.return_value = _mock_subprocess("0 passed, 2 failed", 1)

                result = agent.grade(
                    code_dir=code_dir,
                    eval_dir=eval_dir,
                    criteria_path=criteria_file,
                    output_dir=output_dir,
                )
            results.append(result)

        # All should be FAIL
        for i, result in enumerate(results):
            assert result.verdict == Verdict.FAIL, (
                f"Run {i}: expected FAIL, got {result.verdict}"
            )

        # Scores should be consistently low
        for result in results:
            for score in result.scores:
                assert score.score <= 5, (
                    f"{score.criterion}: {score.score} too high for failing tests"
                )
