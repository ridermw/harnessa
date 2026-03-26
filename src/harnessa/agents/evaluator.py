"""Evaluator agent — grades code against criteria with Goodhart mitigations."""

from __future__ import annotations

import json
import logging
import subprocess
import uuid
from dataclasses import field as dc_field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from harnessa.agents.base import BaseAgent
from harnessa.criteria.loader import Criterion, CriteriaLoader
from harnessa.telemetry.models import BenchmarkScore, BugReport, CanonicalResponse, Severity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt fragments
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are a ruthlessly honest code evaluator. Your job is to grade code against \
specific criteria. You must resist every urge to be lenient or people-pleasing.

## Core principles
- Be skeptical by default — do NOT praise mediocre work.
- A score of 7 means "solidly good". Anything above 8 should be genuinely impressive.
- If tests fail, that is an automatic signal to score Functionality LOW.
- Do NOT round up. A 6.4 is a 6, not a 7.
- Do NOT use filler praise like "great job" or "well done" unless the work truly warrants it.
- When in doubt, score LOWER, not higher. False negatives are safer than false positives.

## Anti-people-pleasing rules
- You are not the developer's friend. You are quality control.
- If something barely works, say so. A 4 is an honest 4.
- Giving high scores to flawed code is a FAILURE of your role.
- If all your scores are >= 9, you are almost certainly rubber-stamping.

## Output format
Respond with ONLY a JSON object (no markdown fences) with this structure:
{{
  "scores": [
    {{"criterion": "<name>", "score": <1-10>, "justification": "<specific reasoning>"}},
    ...
  ],
  "bugs": [
    {{"id": "<unique-id>", "severity": "critical|high|medium|low", "description": "<what>", "file": "<path>", "line": <number>}},
    ...
  ]
}}

## Criteria to grade
{criteria_block}

## Context
{context_block}
"""


class Verdict(StrEnum):
    """Evaluation verdict."""

    PASS = "PASS"
    FAIL = "FAIL"


class SuiteResult(BaseModel):
    """Result of running a test suite."""

    model_config = {"strict": True}

    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)
    output: str = Field(default="")


class EvaluationResult(BaseModel):
    """Complete evaluation output from the evaluator agent."""

    model_config = {"strict": True}

    scores: list[BenchmarkScore] = Field(default_factory=list)
    bugs: list[BugReport] = Field(default_factory=list)
    verdict: Verdict = Field(default=Verdict.FAIL)
    iteration: int = Field(default=1, ge=1)
    degraded_evaluation: bool = Field(default=False)
    suspicious_approval: bool = Field(default=False)
    test_suite_result: SuiteResult | None = Field(default=None)
    regression_result: SuiteResult | None = Field(default=None)
    refusal_detected: bool = Field(default=False)
    refusal_recovery: str = Field(default="")


REFUSAL_RE_PROMPT = """\
Your previous evaluation is INVALID. Tests are FAILING but you gave all \
scores >= 7. This is a refusal-to-be-negative failure mode.

You MUST give scores below 5 for criteria that have failing tests. \
Being generous is a failure mode. A failing test suite means the code \
does not work — score Functionality accordingly.

Re-evaluate with honest, LOW scores where warranted.
"""


class EvaluatorAgent(BaseAgent):
    """Evaluates generated code against YAML criteria with Goodhart mitigations.

    Runs test suites, compares fixtures, grades diffs, and calls an LLM
    to score each criterion. Detects rubber-stamping and refusal to be
    negative. Falls back to test-suite-only grading if full eval fails.
    """

    def __init__(self, model_id: str, work_dir: Path) -> None:
        super().__init__(agent_id="evaluator", model_id=model_id, work_dir=work_dir)
        self._loader = CriteriaLoader()

    def execute(self, **kwargs: Any) -> None:
        """Execute is the BaseAgent interface — delegates to grade()."""
        code_dir = Path(kwargs["code_dir"])
        eval_dir = Path(kwargs["eval_dir"])
        criteria_path = Path(kwargs["criteria_path"])
        output_dir = Path(kwargs["output_dir"])
        self.grade(code_dir, eval_dir, criteria_path, output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grade(
        self,
        code_dir: Path,
        eval_dir: Path,
        criteria_path: Path,
        output_dir: Path,
        iteration: int = 1,
    ) -> EvaluationResult:
        """Grade code in *code_dir* against criteria, using eval assets.

        Args:
            code_dir: Directory containing the generated code.
            eval_dir: Directory containing _eval/ test suite and fixtures.
            criteria_path: Path to the YAML criteria file.
            output_dir: Where to write evaluation artifacts.
            iteration: Current GAN-loop iteration number.

        Returns:
            A complete EvaluationResult.
        """
        self.write_status("grading")
        criteria = self._loader.load(criteria_path)

        # Phase 1: run _eval/ test suite
        eval_test_result = self._run_test_suite(eval_dir, code_dir)

        # Phase 2: check fixtures
        fixture_ok = self._check_fixtures(eval_dir, code_dir)

        # Phase 3: regression check — run full existing test suite
        regression_result = self._run_regression_tests(code_dir)

        # Phase 4: grade via LLM
        try:
            result = self._llm_grade(
                criteria, code_dir, eval_test_result, regression_result, fixture_ok, iteration
            )
        except Exception:
            logger.warning("[evaluator] LLM grading failed, falling back to test-suite-only")
            result = self._fallback_grade(eval_test_result, regression_result, criteria, iteration)

        # Goodhart mitigations
        result.suspicious_approval = self._detect_rubber_stamp(result.scores)
        result = self._handle_refusal(result, eval_test_result)

        # Regression = automatic FAIL
        if regression_result and regression_result.failed > 0:
            result.verdict = Verdict.FAIL

        # Write output atomically
        self._write_output(result, output_dir)
        self.write_status("done")
        return result

    # ------------------------------------------------------------------
    # Test suite runners
    # ------------------------------------------------------------------

    def _run_test_suite(self, eval_dir: Path, code_dir: Path) -> SuiteResult:
        """Run the _eval/ test suite inside *code_dir*.

        Tries pytest, then npm test, then go test.
        """
        return self._execute_tests(eval_dir, code_dir)

    def _run_regression_tests(self, code_dir: Path) -> SuiteResult | None:
        """Run the project's existing test suite to detect regressions."""
        test_dir = code_dir / "tests"
        if not test_dir.exists():
            test_dir = code_dir / "test"
        if not test_dir.exists():
            return None
        return self._execute_tests(test_dir, code_dir)

    def _execute_tests(self, test_dir: Path, cwd: Path) -> SuiteResult:
        """Execute test suite, auto-detecting the runner."""
        # Try pytest first
        cmd = self._detect_test_command(test_dir, cwd)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(cwd),
            )
            passed, failed, errors = self._parse_test_output(proc.stdout + proc.stderr)
            return SuiteResult(
                passed=passed,
                failed=failed,
                errors=errors,
                output=(proc.stdout + proc.stderr)[-2000:],
            )
        except subprocess.TimeoutExpired:
            return SuiteResult(errors=1, output="Test suite timed out after 120s")
        except FileNotFoundError:
            return SuiteResult(errors=1, output=f"Test runner not found for: {cmd}")

    def _detect_test_command(self, test_dir: Path, cwd: Path) -> list[str]:
        """Detect the appropriate test command for the project."""
        if (cwd / "package.json").exists():
            return ["npm", "test", "--", "--no-coverage"]
        if (cwd / "go.mod").exists():
            return ["go", "test", str(test_dir / "...")]
        # Default to pytest
        return ["python", "-m", "pytest", str(test_dir), "-v", "--tb=short"]

    def _parse_test_output(self, output: str) -> tuple[int, int, int]:
        """Parse test output to extract pass/fail/error counts.

        Returns (passed, failed, errors) tuple. Conservative: if parsing
        fails, reports 0 passed and 1 error.
        """
        passed = failed = errors = 0

        # pytest style: "5 passed, 2 failed, 1 error"
        import re

        m_passed = re.search(r"(\d+)\s+passed", output)
        m_failed = re.search(r"(\d+)\s+failed", output)
        m_errors = re.search(r"(\d+)\s+error", output)

        if m_passed:
            passed = int(m_passed.group(1))
        if m_failed:
            failed = int(m_failed.group(1))
        if m_errors:
            errors = int(m_errors.group(1))

        # npm test style
        if not m_passed and not m_failed:
            m_npm_pass = re.search(r"Tests:\s+(\d+)\s+passed", output)
            m_npm_fail = re.search(r"Tests:\s+(\d+)\s+failed", output)
            if m_npm_pass:
                passed = int(m_npm_pass.group(1))
            if m_npm_fail:
                failed = int(m_npm_fail.group(1))

        return passed, failed, errors

    # ------------------------------------------------------------------
    # Fixture comparison
    # ------------------------------------------------------------------

    def _check_fixtures(self, eval_dir: Path, code_dir: Path) -> bool:
        """Compare actual output against expected fixtures if present.

        Returns True if fixtures match or no fixtures exist.
        """
        fixtures_dir = eval_dir / "fixtures"
        if not fixtures_dir.exists():
            return True

        all_match = True
        for expected_file in fixtures_dir.iterdir():
            if expected_file.is_file():
                actual_file = code_dir / expected_file.name
                if not actual_file.exists():
                    logger.warning("[evaluator] Missing output file: %s", actual_file)
                    all_match = False
                    continue
                expected = expected_file.read_text(encoding="utf-8")
                actual = actual_file.read_text(encoding="utf-8")
                if expected.strip() != actual.strip():
                    logger.warning(
                        "[evaluator] Fixture mismatch: %s", expected_file.name
                    )
                    all_match = False
        return all_match

    # ------------------------------------------------------------------
    # LLM grading
    # ------------------------------------------------------------------

    def _llm_grade(
        self,
        criteria: list[Criterion],
        code_dir: Path,
        eval_test_result: SuiteResult,
        regression_result: SuiteResult | None,
        fixture_ok: bool,
        iteration: int,
    ) -> EvaluationResult:
        """Build prompt, call LLM, parse response into EvaluationResult."""
        prompt = self._build_prompt(
            criteria, code_dir, eval_test_result, regression_result, fixture_ok
        )
        response = self.call_llm(prompt)
        return self._parse_llm_response(response, criteria, eval_test_result, regression_result, iteration)

    def _build_prompt(
        self,
        criteria: list[Criterion],
        code_dir: Path,
        eval_test_result: SuiteResult,
        regression_result: SuiteResult | None,
        fixture_ok: bool,
    ) -> str:
        """Build the full evaluation prompt."""
        criteria_block = self._format_criteria(criteria)
        context_block = self._format_context(
            code_dir, eval_test_result, regression_result, fixture_ok
        )
        return SYSTEM_PROMPT_TEMPLATE.format(
            criteria_block=criteria_block,
            context_block=context_block,
        )

    def _format_criteria(self, criteria: list[Criterion]) -> str:
        """Format criteria list for the LLM prompt."""
        lines = []
        for c in criteria:
            lines.append(f"### {c.name} (weight: {c.weight}, threshold: {c.threshold})")
            lines.append(c.description.strip())
            if c.few_shot_examples:
                lines.append("Examples:")
                for ex in c.few_shot_examples:
                    lines.append(f"  - Input: {ex.input} → Score: {ex.score} — {ex.justification}")
            lines.append("")
        return "\n".join(lines)

    def _format_context(
        self,
        code_dir: Path,
        eval_test_result: SuiteResult,
        regression_result: SuiteResult | None,
        fixture_ok: bool,
    ) -> str:
        """Format test results and diff info for the LLM prompt."""
        parts = []
        parts.append(f"Eval test suite: {eval_test_result.passed} passed, "
                      f"{eval_test_result.failed} failed, {eval_test_result.errors} errors")
        if regression_result:
            parts.append(f"Regression tests: {regression_result.passed} passed, "
                          f"{regression_result.failed} failed")
        parts.append(f"Fixtures match: {fixture_ok}")

        # Include git diff summary if available
        diff = self._get_git_diff(code_dir)
        if diff:
            parts.append(f"\nGit diff (truncated to 3000 chars):\n{diff[:3000]}")

        return "\n".join(parts)

    def _get_git_diff(self, code_dir: Path) -> str:
        """Get git diff of the working directory."""
        try:
            proc = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(code_dir),
            )
            return proc.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _parse_llm_response(
        self,
        response: CanonicalResponse,
        criteria: list[Criterion],
        eval_test_result: SuiteResult,
        regression_result: SuiteResult | None,
        iteration: int,
    ) -> EvaluationResult:
        """Parse the LLM JSON response into an EvaluationResult."""
        scores: list[BenchmarkScore] = []
        bugs: list[BugReport] = []

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            logger.warning("[evaluator] LLM response is not valid JSON, falling back")
            raise ValueError("LLM response is not valid JSON")

        for score_data in data.get("scores", []):
            scores.append(BenchmarkScore(
                criterion=score_data["criterion"],
                score=float(score_data["score"]),
                justification=score_data.get("justification", ""),
            ))

        for bug_data in data.get("bugs", []):
            bugs.append(BugReport(
                id=bug_data.get("id", uuid.uuid4().hex[:8]),
                severity=Severity(bug_data.get("severity", "medium")),
                description=bug_data["description"],
                file=bug_data.get("file", ""),
                line=bug_data.get("line", 0),
            ))

        # Determine verdict: any score below its criterion's threshold = FAIL
        verdict = self._compute_verdict(scores, criteria)

        return EvaluationResult(
            scores=scores,
            bugs=bugs,
            verdict=verdict,
            iteration=iteration,
            test_suite_result=eval_test_result,
            regression_result=regression_result,
        )

    def _compute_verdict(
        self, scores: list[BenchmarkScore], criteria: list[Criterion]
    ) -> Verdict:
        """Any score below its criterion's threshold → FAIL."""
        threshold_map = {c.name: c.threshold for c in criteria}
        for s in scores:
            threshold = threshold_map.get(s.criterion)
            if threshold is not None and s.score < threshold:
                return Verdict.FAIL
        return Verdict.PASS

    # ------------------------------------------------------------------
    # Goodhart mitigations
    # ------------------------------------------------------------------

    def _detect_rubber_stamp(self, scores: list[BenchmarkScore]) -> bool:
        """If all scores >= 9, flag as suspicious approval."""
        if not scores:
            return False
        return all(s.score >= 9 for s in scores)

    def _detect_refusal_to_be_negative(
        self, result: EvaluationResult, test_result: SuiteResult
    ) -> EvaluationResult:
        """If tests failed but LLM gave no low scores, override to FAIL."""
        if test_result.failed > 0 or test_result.errors > 0:
            has_low_score = any(s.score < 5 for s in result.scores)
            if not has_low_score and result.scores:
                logger.warning(
                    "[evaluator] Tests failed but LLM gave no low scores — "
                    "overriding to FAIL (refusal to be negative detected)"
                )
                result.verdict = Verdict.FAIL
                result.suspicious_approval = True
        return result

    def _is_refusal(self, result: EvaluationResult, test_result: SuiteResult) -> bool:
        """Check if the result shows refusal-to-be-negative pattern.

        Refusal is detected when tests fail but all scores are >= 7.
        """
        tests_failing = (test_result.failed > 0 or test_result.errors > 0)
        if not tests_failing or not result.scores:
            return False
        return all(s.score >= 7 for s in result.scores)

    def _handle_refusal(
        self, result: EvaluationResult, test_result: SuiteResult
    ) -> EvaluationResult:
        """Handle refusal-to-be-negative with re-prompting and fallback.

        Strategy:
        1. Detect refusal (tests fail but all scores >= 7).
        2. First attempt: re-prompt with explicit instruction to score low.
        3. If second attempt still shows refusal: switch to fallback grading.
        4. Log the refusal event in telemetry.

        Args:
            result: The initial EvaluationResult.
            test_result: The test suite result.

        Returns:
            The (possibly corrected) EvaluationResult.
        """
        if not self._is_refusal(result, test_result):
            # No refusal — still run legacy detection for edge cases
            return self._detect_refusal_to_be_negative(result, test_result)

        logger.warning(
            "[evaluator] Refusal detected: tests failing but all scores >= 7. "
            "Re-prompting with explicit instruction."
        )
        result.refusal_detected = True

        # First attempt: re-prompt
        try:
            re_prompted = self._re_prompt_for_honesty(result, test_result)
            if not self._is_refusal(re_prompted, test_result):
                logger.info("[evaluator] Re-prompt resolved the refusal")
                re_prompted.refusal_detected = True
                re_prompted.refusal_recovery = "re_prompt"
                return re_prompted
        except Exception:
            logger.warning("[evaluator] Re-prompt LLM call failed")

        # Second attempt failed or still shows refusal — fallback grading
        logger.warning(
            "[evaluator] Persistent refusal after re-prompt. "
            "Falling back to test-suite-only grading."
        )
        fallback = self._fallback_grade_from_tests(test_result, result.iteration)
        fallback.refusal_detected = True
        fallback.refusal_recovery = "fallback"
        fallback.verdict = Verdict.FAIL
        return fallback

    def _re_prompt_for_honesty(
        self, result: EvaluationResult, test_result: SuiteResult
    ) -> EvaluationResult:
        """Re-prompt the LLM with explicit instruction to give low scores.

        Sends the refusal re-prompt along with the original scores so the
        LLM can see what it did wrong.
        """
        import json as _json

        original_scores = _json.dumps(
            [{"criterion": s.criterion, "score": s.score} for s in result.scores]
        )
        prompt = (
            f"{REFUSAL_RE_PROMPT}\n\n"
            f"Your previous scores were: {original_scores}\n\n"
            f"Test results: {test_result.passed} passed, "
            f"{test_result.failed} failed, {test_result.errors} errors\n\n"
            f"Test output:\n{test_result.output[:1500]}"
        )
        response = self.call_llm(prompt)
        return self._parse_reprompt_response(response, result, test_result)

    def _parse_reprompt_response(
        self,
        response: CanonicalResponse,
        original: EvaluationResult,
        test_result: SuiteResult,
    ) -> EvaluationResult:
        """Parse re-prompt response, falling back to original on failure."""
        import json as _json

        try:
            data = _json.loads(response.text)
        except (ValueError, _json.JSONDecodeError):
            logger.warning("[evaluator] Re-prompt response is not valid JSON")
            return original

        scores: list[BenchmarkScore] = []
        for score_data in data.get("scores", []):
            scores.append(BenchmarkScore(
                criterion=score_data["criterion"],
                score=float(score_data["score"]),
                justification=score_data.get("justification", ""),
            ))

        if not scores:
            return original

        bugs: list[BugReport] = []
        for bug_data in data.get("bugs", []):
            bugs.append(BugReport(
                id=bug_data.get("id", uuid.uuid4().hex[:8]),
                severity=Severity(bug_data.get("severity", "medium")),
                description=bug_data["description"],
                file=bug_data.get("file", ""),
                line=bug_data.get("line", 0),
            ))

        # Determine verdict conservatively
        has_low = any(s.score < 5 for s in scores)
        verdict = Verdict.FAIL if (test_result.failed > 0 and not has_low) else (
            Verdict.FAIL if test_result.failed > 0 else Verdict.PASS
        )

        return EvaluationResult(
            scores=scores,
            bugs=bugs or original.bugs,
            verdict=verdict,
            iteration=original.iteration,
            test_suite_result=test_result,
            regression_result=original.regression_result,
        )

    def _fallback_grade_from_tests(
        self, test_result: SuiteResult, iteration: int
    ) -> EvaluationResult:
        """Create a fallback grade purely from test results.

        Used when re-prompting fails to resolve refusal.
        """
        total = test_result.passed + test_result.failed + test_result.errors
        pass_rate = test_result.passed / max(total, 1)
        raw_score = round(pass_rate * 10, 1)

        scores = [
            BenchmarkScore(
                criterion="Overall",
                score=raw_score,
                justification=f"Fallback (refusal recovery): test pass rate "
                              f"{pass_rate:.0%} ({test_result.passed}/{total})",
            ),
        ]

        return EvaluationResult(
            scores=scores,
            bugs=[],
            verdict=Verdict.FAIL,
            iteration=iteration,
            degraded_evaluation=True,
            test_suite_result=test_result,
        )

    # ------------------------------------------------------------------
    # Fallback grading
    # ------------------------------------------------------------------

    def _fallback_grade(
        self,
        eval_test_result: SuiteResult,
        regression_result: SuiteResult | None,
        criteria: list[Criterion],
        iteration: int,
    ) -> EvaluationResult:
        """Test-suite-only grading when full evaluation fails.

        Sets degraded_evaluation = True. Scores are derived purely from
        test pass rates — no LLM judgment.
        """
        total = eval_test_result.passed + eval_test_result.failed + eval_test_result.errors
        pass_rate = eval_test_result.passed / max(total, 1)

        # Map pass rate to a 1-10 score
        raw_score = round(pass_rate * 10, 1)

        scores = [
            BenchmarkScore(
                criterion=c.name,
                score=raw_score,
                justification=f"Fallback: test pass rate {pass_rate:.0%} ({eval_test_result.passed}/{total})",
            )
            for c in criteria
        ]

        verdict = self._compute_verdict(scores, criteria)

        # Regressions force FAIL
        if regression_result and regression_result.failed > 0:
            verdict = Verdict.FAIL

        return EvaluationResult(
            scores=scores,
            bugs=[],
            verdict=verdict,
            iteration=iteration,
            degraded_evaluation=True,
            test_suite_result=eval_test_result,
            regression_result=regression_result,
        )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _write_output(self, result: EvaluationResult, output_dir: Path) -> None:
        """Write evaluation result atomically to output_dir/evaluations/."""
        eval_dir = output_dir / "evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)

        filename = f"eval_iter{result.iteration}.json"
        target = eval_dir / filename
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        tmp.rename(target)

        logger.info("[evaluator] Wrote evaluation to %s", target)

    @property
    def system_prompt(self) -> str:
        """Return the system prompt template (for testing/introspection)."""
        return SYSTEM_PROMPT_TEMPLATE
