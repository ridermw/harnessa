"""Subprocess isolation — worktree management, tool wrapping, and port allocation.

Ensures the generator agent cannot see evaluation artifacts (_eval/ directory)
while the evaluator has full access. See docs/designs/v1-cli-benchmark-harness.md
"Goodhart Mitigation" for rationale.
"""

from __future__ import annotations

import logging
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_PORT_BLOCK_SIZE = 10
_PORT_BASE = 8001


class SecurityError(Exception):
    """Raised when the generator/evaluator isolation boundary is breached."""


# ---------------------------------------------------------------------------
# ToolWrapper — logs every subprocess invocation for telemetry
# ---------------------------------------------------------------------------


@dataclass
class ToolUsage:
    """Record of a single tool invocation by an agent."""

    command: str
    args: list[str]
    duration_ms: float
    exit_code: int
    timestamp: datetime


class ToolWrapper:
    """Wraps subprocess calls made by agents, logging each invocation.

    Usage::

        wrapper = ToolWrapper()
        wrapper.run(["git", "status"], cwd=some_path)
        usage = wrapper.get_tool_usage()
    """

    def __init__(self) -> None:
        self._usage: list[ToolUsage] = []

    def run(
        self,
        cmd: list[str],
        *,
        cwd: Path | str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        """Run a subprocess and record its telemetry.

        Args:
            cmd: Command and arguments.
            cwd: Working directory for the subprocess.
            env: Environment variables.
            timeout: Timeout in seconds.

        Returns:
            The completed process result.
        """
        start = time.monotonic()
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=True,
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        self._usage.append(
            ToolUsage(
                command=cmd[0] if cmd else "",
                args=cmd[1:] if len(cmd) > 1 else [],
                duration_ms=elapsed_ms,
                exit_code=result.returncode,
                timestamp=datetime.now(tz=timezone.utc),
            )
        )
        logger.debug("Tool invocation: %s → exit %d (%.1fms)", cmd, result.returncode, elapsed_ms)
        return result

    def get_tool_usage(self) -> list[ToolUsage]:
        """Return accumulated tool usage records."""
        return list(self._usage)


# ---------------------------------------------------------------------------
# PortAllocator — assigns non-overlapping port ranges per benchmark
# ---------------------------------------------------------------------------


@dataclass
class PortRange:
    """A contiguous port range assigned to a benchmark."""

    start_port: int
    end_port: int


class PortAllocator:
    """Assigns port ranges per benchmark index.

    Bench 0 → 8001–8010, bench 1 → 8011–8020, etc.
    """

    def __init__(self, base: int = _PORT_BASE, block_size: int = _PORT_BLOCK_SIZE) -> None:
        self._base = base
        self._block_size = block_size

    def allocate(self, benchmark_index: int) -> PortRange:
        """Return the port range for the given benchmark index."""
        start = self._base + benchmark_index * self._block_size
        end = start + self._block_size - 1
        return PortRange(start_port=start, end_port=end)

    @staticmethod
    def check_available(port: int) -> bool:
        """Return True if *port* is not currently in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False


# ---------------------------------------------------------------------------
# IsolationManager — worktree creation and boundary enforcement
# ---------------------------------------------------------------------------


def _git_repo_root(path: Path) -> Path | None:
    """Return the git repo root for *path*, or None when not inside a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            check=True,
        )
        if result.stdout.strip() != b"true":
            return None
        top_level = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(top_level.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


class IsolationManager:
    """Creates isolated working trees for generator and evaluator agents.

    The generator tree **excludes** the ``_eval/`` directory so the agent
    cannot see evaluation fixtures.  The evaluator tree is a full copy.
    """

    EVAL_DIR = "_eval"

    # -- generator (no _eval/) ------------------------------------------

    def prepare_generator_worktree(self, benchmark_repo: Path, run_dir: Path) -> Path:
        """Create a working tree of *benchmark_repo* **without** ``_eval/``.

        Uses git sparse-checkout when the source is a git repo; otherwise
        falls back to :func:`shutil.copytree` with an ignore filter.

        Returns:
            Path to the generator's clean working tree.
        """
        dest = run_dir / "generator"
        dest.mkdir(parents=True, exist_ok=True)

        repo_root = _git_repo_root(benchmark_repo)
        if repo_root is not None and benchmark_repo.resolve() == repo_root:
            self._sparse_checkout_excluding_eval(benchmark_repo.resolve(), dest)
        else:
            self._copy_excluding_eval(benchmark_repo, dest)

        logger.info("Generator worktree ready at %s", dest)
        return dest

    # -- evaluator (full copy) ------------------------------------------

    def prepare_evaluator_worktree(self, benchmark_repo: Path, run_dir: Path) -> Path:
        """Create a full working tree of *benchmark_repo* including ``_eval/``.

        Returns:
            Path to the evaluator's working tree.
        """
        dest = run_dir / "evaluator"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(benchmark_repo, dest)
        logger.info("Evaluator worktree ready at %s", dest)
        return dest

    # -- boundary verification -------------------------------------------

    def verify_boundary(self, generator_tree: Path) -> bool:
        """Walk *generator_tree* and confirm no ``_eval/`` directory exists.

        Returns:
            ``True`` if the boundary holds.

        Raises:
            SecurityError: If ``_eval/`` is found anywhere in the tree.
        """
        for dirpath, dirnames, _ in generator_tree.rglob("*").__class__.__mro__[0] and []:  # type: ignore[unreachable]
            pass  # never reached — we use rglob below

        # Walk using os-level iteration for completeness.
        for item in generator_tree.rglob("*"):
            if item.is_dir() and item.name == self.EVAL_DIR:
                raise SecurityError(
                    f"Isolation breach: {self.EVAL_DIR}/ found at {item} "
                    f"inside generator tree {generator_tree}"
                )
        return True

    # -- cleanup ---------------------------------------------------------

    def cleanup_worktrees(self, run_dir: Path) -> None:
        """Remove generator and evaluator worktrees under *run_dir*.

        If the generator tree was created via ``git worktree add``, attempts
        ``git worktree remove`` first; otherwise falls back to ``shutil.rmtree``.
        """
        for name in ("generator", "evaluator"):
            tree = run_dir / name
            if not tree.exists():
                continue

            # Try git worktree remove (works if it was added as a worktree)
            git_file = tree / ".git"
            if git_file.is_file():
                # .git is a file (not a dir) inside worktrees
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(tree)],
                        capture_output=True,
                        check=True,
                    )
                    logger.info("Removed git worktree %s", tree)
                    continue
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.debug("git worktree remove failed for %s, falling back to rmtree", tree)

            shutil.rmtree(tree)
            logger.info("Removed worktree directory %s", tree)

    # -- internal helpers ------------------------------------------------

    def _sparse_checkout_excluding_eval(self, repo: Path, dest: Path) -> None:
        """Clone via git worktree, then remove ``_eval/``.

        Uses ``git worktree add`` for a lightweight checkout and then
        deletes ``_eval/`` from the working tree.  This is simpler and
        more portable than sparse-checkout pattern manipulation.
        """
        # Add a detached worktree
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(dest)],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        # Remove _eval/ from the worktree
        leaked = dest / self.EVAL_DIR
        if leaked.exists():
            shutil.rmtree(leaked)

    def _copy_excluding_eval(self, src: Path, dest: Path) -> None:
        """Copy *src* to *dest* excluding ``_eval/`` directories."""

        def _ignore(directory: str, contents: list[str]) -> set[str]:
            return {c for c in contents if c == self.EVAL_DIR}

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=_ignore)
