"""Tests for shared test execution and normalization."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from harnessa.test_execution import (
    _build_go_command,
    _build_node_command,
    _materialize_test_dir,
    _parse_go_json,
    _parse_jest_like_report,
    _parse_pytest_junit_xml,
)


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _subprocess_env(fake_bin: Path) -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
    env["PYTHONPATH"] = f"{repo_root / 'src'}:{env.get('PYTHONPATH', '')}"
    return env


def test_materialize_test_dir_copies_external_suite(tmp_path: Path) -> None:
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    external = tmp_path / "external_eval"
    external.mkdir()
    (external / "case.txt").write_text("fixture", encoding="utf-8")

    materialized, cleanup_dir = _materialize_test_dir(cwd, external)

    assert cleanup_dir is not None
    assert materialized.parent == cwd
    assert (materialized / "case.txt").read_text(encoding="utf-8") == "fixture"


def test_materialize_test_dir_uses_eval_path_for_hidden_external_suite(tmp_path: Path) -> None:
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    external = tmp_path / "external_eval"
    external.mkdir()
    (external / "jest.config.js").write_text("module.exports = {}", encoding="utf-8")

    materialized, cleanup_dir = _materialize_test_dir(cwd, external, preferred_name="_eval")

    assert cleanup_dir == cwd / "_eval"
    assert materialized == cwd / "_eval"
    assert (materialized / "jest.config.js").exists()


def test_parse_jest_like_report_reads_machine_output(tmp_path: Path) -> None:
    report_path = tmp_path / "jest-report.json"
    report_path.write_text(
        json.dumps(
            {
                "numPassedTests": 3,
                "numFailedTests": 1,
                "numTotalTests": 4,
                "numRuntimeErrorTestSuites": 0,
            }
        ),
        encoding="utf-8",
    )

    result = _parse_jest_like_report(
        report_path,
        framework="jest",
        command=["npm", "test"],
        exit_code=1,
        output="1 failed",
    )

    assert result.passed == 3
    assert result.failed == 1
    assert result.total == 4
    assert result.execution_ok is True


def test_parse_jest_like_report_marks_zero_total_failure_untrusted(tmp_path: Path) -> None:
    report_path = tmp_path / "jest-report.json"
    report_path.write_text(
        json.dumps(
            {
                "numPassedTests": 0,
                "numFailedTests": 0,
                "numTotalTests": 0,
                "numRuntimeErrorTestSuites": 2,
            }
        ),
        encoding="utf-8",
    )

    result = _parse_jest_like_report(
        report_path,
        framework="jest",
        command=["npm", "test"],
        exit_code=1,
        output="Cannot find module",
    )

    assert result.execution_ok is False
    assert result.errors == 2


def test_parse_pytest_junit_xml_reads_counts(tmp_path: Path) -> None:
    report_path = tmp_path / "pytest-report.xml"
    report_path.write_text(
        "<testsuite tests='5' failures='1' errors='1' skipped='1'></testsuite>",
        encoding="utf-8",
    )

    result = _parse_pytest_junit_xml(
        report_path,
        command=["python", "-m", "pytest"],
        exit_code=1,
        output="pytest output",
    )

    assert result.total == 5
    assert result.failed == 1
    assert result.errors == 1
    assert result.passed == 2


def test_parse_go_json_counts_pass_and_fail(tmp_path: Path) -> None:
    report_path = tmp_path / "go-report.jsonl"
    stdout = "\n".join(
        [
            json.dumps({"Action": "run", "Test": "TestOne"}),
            json.dumps({"Action": "pass", "Test": "TestOne"}),
            json.dumps({"Action": "run", "Test": "TestTwo"}),
            json.dumps({"Action": "fail", "Test": "TestTwo"}),
        ]
    )

    result = _parse_go_json(
        report_path,
        command=["go", "test", "-json", "./..."],
        exit_code=1,
        stdout=stdout,
        output="go output",
    )

    assert result.passed == 1
    assert result.failed == 1
    assert result.total == 2
    assert report_path.read_text(encoding="utf-8") == stdout


def test_parse_go_json_marks_zero_total_nonzero_exit_untrusted(tmp_path: Path) -> None:
    report_path = tmp_path / "go-report.jsonl"
    stdout = "\n".join(
        [
            json.dumps({"Action": "output", "Package": "example.com/foo", "Output": "# example.com/foo"}),
            json.dumps({"Action": "fail", "Package": "example.com/foo", "Elapsed": 0.0}),
        ]
    )

    result = _parse_go_json(
        report_path,
        command=["go", "test", "-json", "./hidden/..."],
        exit_code=1,
        stdout=stdout,
        output="undefined: NewPool",
    )

    assert result.total == 0
    assert result.errors == 1
    assert result.execution_ok is False


def test_build_node_command_preserves_hidden_suite_role(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest run"}}),
        encoding="utf-8",
    )
    hidden_dir = workspace / ".harnessa-suite-hidden"
    hidden_dir.mkdir()
    report_path = tmp_path / "hidden-report.json"

    command, framework = _build_node_command(
        workspace,
        hidden_dir,
        report_path,
        is_hidden=True,
    )

    assert framework == "vitest"
    assert command[0] == "npx"


def test_build_go_command_preserves_hidden_suite_role(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    hidden_dir = workspace / "harnessa-suite-hidden"
    hidden_dir.mkdir()

    command, framework = _build_go_command(workspace, hidden_dir, is_hidden=True)

    assert framework == "go test"
    assert command[-1] == "./harnessa-suite-hidden/..."


def test_cli_run_suite_node_with_fake_npm(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "npm",
        """#!/bin/sh
out=""
for arg in "$@"; do
  case "$arg" in
    --outputFile=*) out="${arg#--outputFile=}" ;;
  esac
done
cat > "$out" <<'JSON'
{"numPassedTests": 3, "numFailedTests": 1, "numTotalTests": 4, "numRuntimeErrorTestSuites": 0}
JSON
exit 1
""",
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest run"}}),
        encoding="utf-8",
    )
    (workspace / "tests").mkdir()
    report_dir = tmp_path / "reports"
    env = _subprocess_env(fake_bin)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "harnessa.test_execution",
            "run-suite",
            "--cwd",
            str(workspace),
            "--test-dir",
            str(workspace / "tests"),
            "--report-dir",
            str(report_dir),
            "--suite-name",
            "visible-tests",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    result = json.loads(proc.stdout)
    assert result["framework"] == "vitest"
    assert result["passed"] == 3
    assert result["failed"] == 1
    assert Path(result["report_path"]).exists()


def test_cli_run_suite_python_with_fake_python(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "python",
        """#!/bin/sh
out=""
for arg in "$@"; do
  case "$arg" in
    --junitxml=*) out="${arg#--junitxml=}" ;;
  esac
done
cat > "$out" <<'XML'
<testsuite tests="4" failures="1" errors="0" skipped="0"></testsuite>
XML
exit 1
""",
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tests").mkdir()
    report_dir = tmp_path / "reports"
    env = _subprocess_env(fake_bin)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "harnessa.test_execution",
            "run-suite",
            "--cwd",
            str(workspace),
            "--test-dir",
            str(workspace / "tests"),
            "--report-dir",
            str(report_dir),
            "--suite-name",
            "visible-tests",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    result = json.loads(proc.stdout)
    assert result["framework"] == "pytest"
    assert result["passed"] == 3
    assert result["failed"] == 1
    assert Path(result["report_path"]).exists()


def test_cli_run_suite_go_with_fake_go(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(
        fake_bin / "go",
        """#!/bin/sh
cat <<'JSON'
{"Action":"run","Test":"TestOne"}
{"Action":"pass","Test":"TestOne"}
{"Action":"run","Test":"TestTwo"}
{"Action":"fail","Test":"TestTwo"}
JSON
exit 1
""",
    )

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "go.mod").write_text("module example.com/test\n", encoding="utf-8")
    report_dir = tmp_path / "reports"
    env = _subprocess_env(fake_bin)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "harnessa.test_execution",
            "run-suite",
            "--cwd",
            str(workspace),
            "--test-dir",
            str(workspace / "tests"),
            "--report-dir",
            str(report_dir),
            "--suite-name",
            "visible-tests",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    result = json.loads(proc.stdout)
    assert result["framework"] == "go test"
    assert result["passed"] == 1
    assert result["failed"] == 1
    assert Path(result["report_path"]).exists()
