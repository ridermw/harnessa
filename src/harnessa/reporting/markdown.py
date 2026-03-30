"""Markdown reporter — generates human-readable run reports."""

from __future__ import annotations

import logging
from pathlib import Path

from harnessa.telemetry.models import RunManifest

logger = logging.getLogger(__name__)


class MarkdownReporter:
    """Generate Markdown reports from a RunManifest.

    Produces a structured summary including scores, agent metrics,
    cost breakdown, and quality trends.
    """

    PASS_THRESHOLD = 7.0

    def generate(self, manifest: RunManifest, output_path: Path) -> Path:
        """Generate a Markdown report and write it to *output_path*.

        Args:
            manifest: The completed run manifest.
            output_path: File path to write the report to.

        Returns:
            The path that was written.
        """
        content = self._build_report(manifest)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logger.info("Wrote report to %s", output_path)
        return output_path

    def generate_comparison(
        self,
        solo: RunManifest,
        trio: RunManifest,
        output_path: Path,
    ) -> Path:
        """Generate a side-by-side solo vs trio comparison report.

        Args:
            solo: RunManifest from a solo-mode run.
            trio: RunManifest from a trio-mode run.
            output_path: File path to write the report to.

        Returns:
            The path that was written.
        """
        content = self._build_comparison(solo, trio)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logger.info("Wrote comparison report to %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Single-run report
    # ------------------------------------------------------------------

    def _build_report(self, m: RunManifest) -> str:
        sections: list[str] = [
            self._section_run_summary(m),
            self._section_score_breakdown(m),
        ]
        if m.evaluator_agreement_rate is not None:
            sections.append(self._section_cross_model(m))
        if m.quality_trends:
            sections.append(self._section_quality_trend(m))
        if m.bugs:
            sections.append(self._section_bugs_found(m))
        sections.append(self._section_cost_breakdown(m))
        sections.append(self._section_tool_usage(m))
        return "\n\n".join(sections) + "\n"

    def _section_run_summary(self, m: RunManifest) -> str:
        models = ", ".join(mi.model_id for mi in m.model_info) or "N/A"
        return (
            f"# Run Report: {m.run_id}\n\n"
            "## Run Summary\n\n"
            "| Field | Value |\n"
            "|-------|-------|\n"
            f"| Benchmark | {m.benchmark} |\n"
            f"| Mode | {m.mode} |\n"
            f"| Model | {models} |\n"
            f"| Duration | {m.duration_s:.1f}s |\n"
            f"| Cost | ${m.cost_usd:.4f} |\n"
            f"| Verdict | {m.verdict or 'N/A'} |"
        )

    def _section_score_breakdown(self, m: RunManifest) -> str:
        lines = [
            "## Score Breakdown\n",
            "| Criterion | Score | Threshold | Pass/Fail | Justification |",
            "|-----------|-------|-----------|-----------|---------------|",
        ]
        for s in m.scores:
            pf = "✅ PASS" if s.score >= self.PASS_THRESHOLD else "❌ FAIL"
            lines.append(
                f"| {s.criterion} | {s.score:.1f} | "
                f"{self.PASS_THRESHOLD:.1f} | {pf} | {s.justification} |"
            )
        return "\n".join(lines)

    def _section_cross_model(self, m: RunManifest) -> str:
        rate = m.evaluator_agreement_rate
        rate_pct = f"{rate * 100:.0f}%" if rate is not None else "N/A"
        lines = [
            "## Cross-Model Evaluation\n",
            f"**Agreement Rate:** {rate_pct}\n",
        ]

        # Per-evaluator models from agent metrics (evaluator agents are non-first)
        eval_models = sorted({
            a.model_id for a in m.agents
        })
        if eval_models:
            lines.append("**Evaluator Models:** " + ", ".join(eval_models) + "\n")

        # Reconciled scores table
        lines.extend([
            "### Reconciled Scores\n",
            "| Criterion | Final Score | Justification |",
            "|-----------|-------------|---------------|",
        ])
        for s in m.scores:
            lines.append(f"| {s.criterion} | {s.score:.1f} | {s.justification} |")

        # Disagreements
        if m.evaluator_disagreements:
            lines.extend([
                "",
                "### Disagreements\n",
                "| Criterion | Score A | Score B | Delta |",
                "|-----------|---------|---------|-------|",
            ])
            for d in m.evaluator_disagreements:
                lines.append(
                    f"| {d['criterion']} | {d['score_a']:.1f} | "
                    f"{d['score_b']:.1f} | {d['delta']:.1f} |"
                )

        return "\n".join(lines)

    def _section_quality_trend(self, m: RunManifest) -> str:
        max_iters = max(len(t.scores) for t in m.quality_trends)
        header_cols = " | ".join(f"Iter {i + 1}" for i in range(max_iters))
        sep_cols = " | ".join("------" for _ in range(max_iters))
        lines = [
            "## Quality Trend\n",
            f"| Criterion | {header_cols} |",
            f"|-----------|{sep_cols}|",
        ]
        for t in m.quality_trends:
            scores_str = " | ".join(f"{s:.1f}" for s in t.scores)
            lines.append(f"| {t.criterion} | {scores_str} |")
        return "\n".join(lines)

    def _section_bugs_found(self, m: RunManifest) -> str:
        lines = [
            "## Bugs Found\n",
            "| Severity | Description | File | Line | Status |",
            "|----------|-------------|------|------|--------|",
        ]
        for b in m.bugs:
            lines.append(
                f"| {b.severity} | {b.description} | {b.file} | {b.line} | {b.status} |"
            )
        return "\n".join(lines)

    def _section_cost_breakdown(self, m: RunManifest) -> str:
        lines = [
            "## Cost Breakdown\n",
            "| Agent | Model | Tokens In | Tokens Out | Cost |",
            "|-------|-------|-----------|------------|------|",
        ]
        for i, a in enumerate(m.agents):
            lines.append(
                f"| Agent {i + 1} | {a.model_id} | "
                f"{a.tokens_in:,} | {a.tokens_out:,} | ${a.cost_usd:.4f} |"
            )
        lines.append(f"\n**Total Cost:** ${m.cost_usd:.4f}")
        return "\n".join(lines)

    def _section_tool_usage(self, m: RunManifest) -> str:
        lines = [
            "## Tool Usage\n",
            "| Agent | Model | Tools | Duration |",
            "|-------|-------|-------|----------|",
        ]
        for i, a in enumerate(m.agents):
            tools = ", ".join(a.tool_usage) if a.tool_usage else "None"
            lines.append(
                f"| Agent {i + 1} | {a.model_id} | {tools} | {a.duration_s:.1f}s |"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Comparison report
    # ------------------------------------------------------------------

    def _build_comparison(self, solo: RunManifest, trio: RunManifest) -> str:
        sections = [
            f"# Solo vs Trio Comparison\n\n**Benchmark:** {solo.benchmark}",
            self._comparison_summary(solo, trio),
            self._comparison_scores(solo, trio),
            self._comparison_cost(solo, trio),
        ]
        return "\n\n".join(sections) + "\n"

    @staticmethod
    def _avg_score(m: RunManifest) -> float:
        return sum(s.score for s in m.scores) / len(m.scores) if m.scores else 0.0

    def _comparison_summary(self, solo: RunManifest, trio: RunManifest) -> str:
        return (
            "## Summary Comparison\n\n"
            "| Metric | Solo | Trio |\n"
            "|--------|------|------|\n"
            f"| Avg Score | {self._avg_score(solo):.1f} | {self._avg_score(trio):.1f} |\n"
            f"| Duration | {solo.duration_s:.1f}s | {trio.duration_s:.1f}s |\n"
            f"| Cost | ${solo.cost_usd:.4f} | ${trio.cost_usd:.4f} |\n"
            f"| Verdict | {solo.verdict or 'N/A'} | {trio.verdict or 'N/A'} |"
        )

    @staticmethod
    def _comparison_scores(solo: RunManifest, trio: RunManifest) -> str:
        solo_map = {s.criterion: s for s in solo.scores}
        trio_map = {s.criterion: s for s in trio.scores}
        all_criteria = sorted(set(solo_map) | set(trio_map))

        lines = [
            "## Solo vs Trio Comparison\n",
            "| Criterion | Solo | Trio | Delta |",
            "|-----------|------|------|-------|",
        ]
        for c in all_criteria:
            s_score = solo_map[c].score if c in solo_map else 0.0
            t_score = trio_map[c].score if c in trio_map else 0.0
            delta = t_score - s_score
            sign = "+" if delta > 0 else ""
            lines.append(f"| {c} | {s_score:.1f} | {t_score:.1f} | {sign}{delta:.1f} |")
        return "\n".join(lines)

    @staticmethod
    def _comparison_cost(solo: RunManifest, trio: RunManifest) -> str:
        return (
            "## Cost Comparison\n\n"
            "| Metric | Solo | Trio |\n"
            "|--------|------|------|\n"
            f"| Total Cost | ${solo.cost_usd:.4f} | ${trio.cost_usd:.4f} |\n"
            f"| Duration | {solo.duration_s:.1f}s | {trio.duration_s:.1f}s |"
        )
