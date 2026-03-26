"""Tests for subprocess isolation: worktree management, tool wrapping, and port allocation."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest

from harnessa.agents.isolation import (
    IsolationManager,
    PortAllocator,
    PortRange,
    SecurityError,
    ToolUsage,
    ToolWrapper,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_benchmark_repo(base: Path, *, git: bool = False) -> Path:
    """Create a fake benchmark repo with src/ and _eval/ directories."""
    repo = base / "benchmark"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hello')\n")
    (repo / "README.md").write_text("# Benchmark\n")
    (repo / "_eval").mkdir()
    (repo / "_eval" / "test_solution.py").write_text("assert True\n")

    if git:
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init", "--allow-empty-message"],
            cwd=repo,
            capture_output=True,
            check=True,
            env={
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
                "PATH": subprocess.check_output(
                    ["bash", "-c", "echo $PATH"]
                ).decode().strip(),
            },
        )
    return repo


# ---------------------------------------------------------------------------
# IsolationManager — generator worktree (excludes _eval/)
# ---------------------------------------------------------------------------


class TestPrepareGeneratorWorktree:
    """prepare_generator_worktree must exclude _eval/."""

    def test_copy_excludes_eval(self, tmp_path: Path) -> None:
        """Non-git repo: copytree-based path excludes _eval/."""
        repo = _make_benchmark_repo(tmp_path)
        run_dir = tmp_path / "run"
        run_dir.mkdir()

        mgr = IsolationManager()
        gen_tree = mgr.prepare_generator_worktree(repo, run_dir)

        assert (gen_tree / "src" / "main.py").exists()
        assert (gen_tree / "README.md").exists()
        assert not (gen_tree / "_eval").exists(), "_eval/ must be excluded from generator tree"

    def test_git_repo_excludes_eval(self, tmp_path: Path) -> None:
        """Git repo: worktree/sparse-checkout path excludes _eval/."""
        repo = _make_benchmark_repo(tmp_path, git=True)
        run_dir = tmp_path / "run"
        run_dir.mkdir()

        mgr = IsolationManager()
        gen_tree = mgr.prepare_generator_worktree(repo, run_dir)

        assert (gen_tree / "src" / "main.py").exists()
        assert not (gen_tree / "_eval").exists(), "_eval/ must be excluded from git generator tree"


# ---------------------------------------------------------------------------
# IsolationManager — evaluator worktree (includes _eval/)
# ---------------------------------------------------------------------------


class TestPrepareEvaluatorWorktree:
    """prepare_evaluator_worktree must include _eval/."""

    def test_copy_includes_eval(self, tmp_path: Path) -> None:
        repo = _make_benchmark_repo(tmp_path)
        run_dir = tmp_path / "run"
        run_dir.mkdir()

        mgr = IsolationManager()
        eval_tree = mgr.prepare_evaluator_worktree(repo, run_dir)

        assert (eval_tree / "src" / "main.py").exists()
        assert (eval_tree / "_eval").exists(), "_eval/ must be present in evaluator tree"
        assert (eval_tree / "_eval" / "test_solution.py").exists()


# ---------------------------------------------------------------------------
# IsolationManager — boundary verification
# ---------------------------------------------------------------------------


class TestVerifyBoundary:
    """verify_boundary must detect _eval/ presence."""

    def test_passes_when_no_eval(self, tmp_path: Path) -> None:
        tree = tmp_path / "clean"
        tree.mkdir()
        (tree / "src").mkdir()
        (tree / "src" / "main.py").write_text("")

        mgr = IsolationManager()
        assert mgr.verify_boundary(tree) is True

    def test_raises_when_eval_present(self, tmp_path: Path) -> None:
        tree = tmp_path / "dirty"
        tree.mkdir()
        (tree / "_eval").mkdir()

        mgr = IsolationManager()
        with pytest.raises(SecurityError, match="Isolation breach"):
            mgr.verify_boundary(tree)

    def test_raises_when_eval_nested(self, tmp_path: Path) -> None:
        """_eval/ nested inside a subdirectory is also a breach."""
        tree = tmp_path / "nested"
        tree.mkdir()
        (tree / "sub").mkdir()
        (tree / "sub" / "_eval").mkdir()

        mgr = IsolationManager()
        with pytest.raises(SecurityError, match="Isolation breach"):
            mgr.verify_boundary(tree)


# ---------------------------------------------------------------------------
# IsolationManager — cleanup
# ---------------------------------------------------------------------------


class TestCleanupWorktrees:
    """cleanup_worktrees removes generator and evaluator dirs."""

    def test_removes_plain_directories(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        gen = run_dir / "generator"
        evl = run_dir / "evaluator"
        gen.mkdir(parents=True)
        evl.mkdir(parents=True)
        (gen / "file.txt").write_text("x")
        (evl / "file.txt").write_text("y")

        mgr = IsolationManager()
        mgr.cleanup_worktrees(run_dir)

        assert not gen.exists()
        assert not evl.exists()

    def test_noop_when_no_trees(self, tmp_path: Path) -> None:
        """cleanup_worktrees is safe to call when dirs don't exist."""
        run_dir = tmp_path / "empty_run"
        run_dir.mkdir()

        mgr = IsolationManager()
        mgr.cleanup_worktrees(run_dir)  # should not raise


# ---------------------------------------------------------------------------
# ToolWrapper
# ---------------------------------------------------------------------------


class TestToolWrapper:
    """ToolWrapper logs subprocess invocations."""

    def test_logs_invocation(self) -> None:
        wrapper = ToolWrapper()
        wrapper.run(["echo", "hello"])

        usage = wrapper.get_tool_usage()
        assert len(usage) == 1
        assert usage[0].command == "echo"
        assert usage[0].args == ["hello"]
        assert usage[0].exit_code == 0
        assert usage[0].duration_ms >= 0
        assert usage[0].timestamp is not None

    def test_multiple_invocations(self) -> None:
        wrapper = ToolWrapper()
        wrapper.run(["echo", "a"])
        wrapper.run(["echo", "b"])
        wrapper.run(["false"])  # exit code 1

        usage = wrapper.get_tool_usage()
        assert len(usage) == 3
        assert usage[2].command == "false"
        assert usage[2].exit_code != 0

    def test_returns_completed_process(self) -> None:
        wrapper = ToolWrapper()
        result = wrapper.run(["echo", "output"])
        assert result.stdout.strip() == b"output"

    def test_get_tool_usage_returns_copy(self) -> None:
        """Mutating the returned list must not affect internal state."""
        wrapper = ToolWrapper()
        wrapper.run(["echo", "x"])
        first = wrapper.get_tool_usage()
        first.clear()
        assert len(wrapper.get_tool_usage()) == 1


# ---------------------------------------------------------------------------
# PortAllocator
# ---------------------------------------------------------------------------


class TestPortAllocator:
    """PortAllocator assigns non-overlapping ranges."""

    def test_allocate_bench_0(self) -> None:
        alloc = PortAllocator()
        r = alloc.allocate(0)
        assert r == PortRange(start_port=8001, end_port=8010)

    def test_allocate_bench_1(self) -> None:
        alloc = PortAllocator()
        r = alloc.allocate(1)
        assert r == PortRange(start_port=8011, end_port=8020)

    def test_non_overlapping(self) -> None:
        alloc = PortAllocator()
        ranges = [alloc.allocate(i) for i in range(5)]
        for i, a in enumerate(ranges):
            for j, b in enumerate(ranges):
                if i != j:
                    assert a.end_port < b.start_port or b.end_port < a.start_port, (
                        f"Ranges for bench {i} and {j} overlap: {a} vs {b}"
                    )

    def test_check_available_on_free_port(self) -> None:
        """An unlikely-to-be-used high port should be available."""
        assert PortAllocator.check_available(49152) is True

    def test_check_available_on_bound_port(self) -> None:
        """A port we are actively listening on should report unavailable."""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()
        try:
            assert PortAllocator.check_available(port) is False
        finally:
            sock.close()
