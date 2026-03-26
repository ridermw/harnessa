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

    def generate(self, manifest: RunManifest) -> str:
        """Generate a Markdown report string from a RunManifest.

        Args:
            manifest: The completed run manifest.

        Returns:
            Markdown-formatted report string.
        """
        logger.info("[stub] Would generate markdown report for run %s", manifest.run_id)
        return f"# Run Report: {manifest.run_id}\n\nNot yet implemented.\n"

    def write(self, manifest: RunManifest, output_dir: Path) -> Path:
        """Write a Markdown report to disk.

        Args:
            manifest: The completed run manifest.
            output_dir: Directory to write the report to.

        Returns:
            Path to the written report file.
        """
        content = self.generate(manifest)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{manifest.run_id}.md"
        path.write_text(content, encoding="utf-8")
        return path
