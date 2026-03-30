"""Sprint contract negotiation between Generator and Evaluator.

Before the generator implements, the generator proposes what "done" looks like
and the evaluator reviews the proposal. This prevents scope misinterpretation.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from pydantic import BaseModel, Field

from harnessa.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ContractProposal(BaseModel):
    """Generator's proposal for what it will build."""

    model_config = {"strict": True}

    features: list[str] = Field(description="What will be implemented")
    acceptance_criteria: list[str] = Field(description="How to verify each feature works")
    files_to_modify: list[str] = Field(description="Which files will be touched")
    estimated_tests: int = Field(ge=0, description="How many tests will be written/modified")


class ContractAgreement(BaseModel):
    """Evaluator's review of the proposal."""

    model_config = {"strict": True}

    approved: bool = Field(description="Whether the proposal is accepted")
    feedback: str = Field(default="", description="What needs changing (if not approved)")
    added_criteria: list[str] = Field(
        default_factory=list,
        description="Additional criteria the evaluator wants",
    )
    removed_criteria: list[str] = Field(
        default_factory=list,
        description="Criteria the evaluator thinks are unnecessary",
    )


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

PROPOSAL_PROMPT = """\
You are a senior software engineer. Based on the following product specification, \
propose what you will build in this sprint.

Respond with ONLY a JSON object (no markdown fences) with this structure:
{{
  "features": ["feature 1", "feature 2"],
  "acceptance_criteria": ["criterion 1", "criterion 2"],
  "files_to_modify": ["path/to/file1.py", "path/to/file2.py"],
  "estimated_tests": 5
}}

## Product Specification
{spec}
"""

REVIEW_PROMPT = """\
You are a ruthlessly honest code evaluator. Review the following sprint contract \
proposal and decide if it adequately addresses the specification.

Respond with ONLY a JSON object (no markdown fences) with this structure:
{{
  "approved": true,
  "feedback": "what needs changing (empty string if approved)",
  "added_criteria": ["additional criterion 1"],
  "removed_criteria": ["unnecessary criterion 1"]
}}

## Specification
{spec}

## Proposed Contract
Features: {features}
Acceptance Criteria: {criteria}
Files to modify: {files}
Estimated tests: {estimated_tests}
"""

REVISION_PROMPT = """\
You are a senior software engineer. Revise your sprint contract proposal based on \
the evaluator's feedback.

Respond with ONLY a JSON object (no markdown fences) with this structure:
{{
  "features": ["feature 1", "feature 2"],
  "acceptance_criteria": ["criterion 1", "criterion 2"],
  "files_to_modify": ["path/to/file1.py", "path/to/file2.py"],
  "estimated_tests": 5
}}

## Original Specification
{spec}

## Evaluator Feedback
{feedback}

## Previous Proposal
Features: {features}
Acceptance Criteria: {criteria}
Files to modify: {files}
Estimated tests: {estimated_tests}
"""


class ContractNegotiator:
    """Negotiates a sprint contract between generator and evaluator.

    Protocol:
    1. Generator writes proposal based on planner spec
    2. Evaluator reviews proposal
    3. If not approved, generator revises (max 2 rounds)
    4. Final contract = proposal + evaluator additions
    """

    def __init__(self, generator_agent: BaseAgent, evaluator_agent: BaseAgent) -> None:
        self.generator_agent = generator_agent
        self.evaluator_agent = evaluator_agent
        self.rounds_completed: int = 0

    def negotiate(
        self,
        spec: str,
        output_dir: Path,
        max_rounds: int = 2,
    ) -> tuple[ContractProposal, ContractAgreement]:
        """Run contract negotiation.

        Args:
            spec: The planner's spec text.
            output_dir: Where to write contracts/sprint-N-proposal.md etc.
            max_rounds: Max negotiation rounds before proceeding anyway.

        Returns:
            (final_proposal, final_agreement)
        """
        contracts_dir = output_dir / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)

        # Round 1: generator proposes
        proposal = self._generate_proposal(spec)
        self._save_proposal(proposal, contracts_dir, round_num=1)

        # Evaluator reviews
        agreement = self._review_proposal(proposal, spec)
        self._save_agreement(agreement, contracts_dir, round_num=1)
        self.rounds_completed = 1

        if agreement.approved:
            return proposal, agreement

        # Subsequent rounds: revise if needed
        for round_num in range(2, max_rounds + 1):
            proposal = self._revise_proposal(proposal, agreement.feedback, spec)
            self._save_proposal(proposal, contracts_dir, round_num=round_num)

            agreement = self._review_proposal(proposal, spec)
            self._save_agreement(agreement, contracts_dir, round_num=round_num)
            self.rounds_completed = round_num

            if agreement.approved:
                return proposal, agreement

        # Max rounds reached — proceed with last proposal anyway
        logger.warning(
            "Contract not agreed after %d rounds — proceeding with last proposal",
            max_rounds,
        )
        return proposal, agreement

    # ------------------------------------------------------------------
    # Agent interaction methods
    # ------------------------------------------------------------------

    def _generate_proposal(self, spec: str) -> ContractProposal:
        """Ask the generator agent to propose a sprint contract."""
        prompt = PROPOSAL_PROMPT.format(spec=spec)
        result = self.generator_agent.run_executor(prompt)
        return self._parse_json_as(result.stdout, ContractProposal)

    def _review_proposal(self, proposal: ContractProposal, spec: str) -> ContractAgreement:
        """Ask the evaluator agent to review a proposal."""
        prompt = REVIEW_PROMPT.format(
            spec=spec,
            features="\n".join(f"- {f}" for f in proposal.features),
            criteria="\n".join(f"- {c}" for c in proposal.acceptance_criteria),
            files="\n".join(f"- {f}" for f in proposal.files_to_modify),
            estimated_tests=proposal.estimated_tests,
        )
        result = self.evaluator_agent.run_executor(prompt)
        return self._parse_json_as(result.stdout, ContractAgreement)

    def _revise_proposal(
        self,
        proposal: ContractProposal,
        feedback: str,
        spec: str,
    ) -> ContractProposal:
        """Ask the generator to revise its proposal based on feedback."""
        prompt = REVISION_PROMPT.format(
            spec=spec,
            feedback=feedback,
            features="\n".join(f"- {f}" for f in proposal.features),
            criteria="\n".join(f"- {c}" for c in proposal.acceptance_criteria),
            files="\n".join(f"- {f}" for f in proposal.files_to_modify),
            estimated_tests=proposal.estimated_tests,
        )
        result = self.generator_agent.run_executor(prompt)
        return self._parse_json_as(result.stdout, ContractProposal)

    # ------------------------------------------------------------------
    # JSON parsing (same strategy as evaluator)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_as(text: str, model_cls: type[BaseModel]) -> BaseModel:
        """Parse text as JSON into a Pydantic model.

        Strategy: try direct parse first, then find first {} block.
        """
        # Try direct parse
        try:
            data = json.loads(text)
            return model_cls.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Find first JSON object in the text
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return model_cls.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass

        raise ValueError(f"Could not parse JSON from agent output for {model_cls.__name__}: {text[:200]}")

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    @staticmethod
    def _save_proposal(proposal: ContractProposal, contracts_dir: Path, round_num: int) -> None:
        """Write proposal to contracts/sprint-{round}-proposal.md."""
        path = contracts_dir / f"sprint-{round_num}-proposal.md"
        content = (
            f"# Sprint Contract Proposal (Round {round_num})\n\n"
            f"## Features\n"
            + "\n".join(f"- {f}" for f in proposal.features)
            + f"\n\n## Acceptance Criteria\n"
            + "\n".join(f"- {c}" for c in proposal.acceptance_criteria)
            + f"\n\n## Files to Modify\n"
            + "\n".join(f"- {f}" for f in proposal.files_to_modify)
            + f"\n\n## Estimated Tests: {proposal.estimated_tests}\n"
        )
        tmp = path.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)

    @staticmethod
    def _save_agreement(agreement: ContractAgreement, contracts_dir: Path, round_num: int) -> None:
        """Write agreement to contracts/sprint-{round}-agreement.md."""
        path = contracts_dir / f"sprint-{round_num}-agreement.md"
        status = "APPROVED" if agreement.approved else "REJECTED"
        content = (
            f"# Sprint Contract Review (Round {round_num})\n\n"
            f"## Status: {status}\n\n"
            f"## Feedback\n{agreement.feedback}\n\n"
            f"## Added Criteria\n"
            + "\n".join(f"- {c}" for c in agreement.added_criteria)
            + f"\n\n## Removed Criteria\n"
            + "\n".join(f"- {c}" for c in agreement.removed_criteria)
            + "\n"
        )
        tmp = path.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)
