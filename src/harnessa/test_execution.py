"""Shared benchmark test execution and normalization helpers."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

from harnessa.telemetry.models import SuiteResult

_OUTPUT_LIMIT = 2000


def _cap_output(text: str, limit: int = _OUTPUT_LIMIT) -> str:
    """Return a capped stdout/stderr excerpt with both ends preserved."""
    if len(text) <= limit:
        return text
    head = text[: limit // 2]
    tail = text[-(limit // 2):]
    return f"{head}\n...\n{tail}"


def _load_package_json(cwd: Path) -> dict[str, Any]:
    """Load package.json if it exists, otherwise return an empty object."""
    package_json = cwd / "package.json"
    if not package_json.exists():
        return {}
    return json.loads(package_json.read_text(encoding="utf-8"))


def _relative_to_cwd(path: Path, cwd: Path) -> Path | None:
    """Return the path relative to *cwd* when possible."""
    try:
        return path.resolve().relative_to(cwd.resolve())
    except ValueError:
        return None


def _materialize_test_dir(
    cwd: Path,
    test_dir: Path,
    *,
    preferred_name: str | None = None,
) -> tuple[Path, Path | None]:
    """Copy external test directories into *cwd* when the runner needs local paths."""
    resolved = test_dir.resolve()
    if not resolved.exists():
        return resolved, None

    relative = _relative_to_cwd(resolved, cwd)
    if relative is not None:
        return cwd / relative, None

    temp_dir = cwd / (preferred_name or f"harnessa-suite-{uuid.uuid4().hex}")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    shutil.copytree(resolved, temp_dir)
    return temp_dir, temp_dir


def _write_vitest_eval_config(cwd: Path, include_dir: Path) -> Path:
    """Create a temporary Vitest config that includes hidden eval files."""
    config_path = cwd / ".harnessa-vitest-eval.config.mjs"
    relative = _relative_to_cwd(include_dir, cwd)
    include_glob = (
        f"{relative.as_posix()}/**/*" if relative is not None else f"{include_dir.as_posix()}/**/*"
    )
    config_path.write_text(
        "\n".join(
            [
                "import { defineConfig } from 'vitest/config'",
                "",
                "export default defineConfig({",
                "  test: {",
                f"    include: ['{include_glob}.{{js,mjs,cjs,ts,mts,cts,jsx,tsx}}'],",
                "    environment: 'node',",
                "  },",
                "})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _detect_runtime(cwd: Path) -> str:
    """Detect the project runtime from workspace files."""
    if (cwd / "package.json").exists():
        return "node"
    if (cwd / "go.mod").exists() or any(cwd.glob("*.go")):
        return "go"
    return "python"


def _build_node_command(
    cwd: Path,
    test_dir: Path,
    report_path: Path,
    *,
    is_hidden: bool,
) -> tuple[list[str], str]:
    """Build a machine-readable Node test command for Jest or Vitest."""
    package_json = _load_package_json(cwd)
    scripts = package_json.get("scripts", {})
    test_script = str(scripts.get("test", ""))
    eval_script = str(scripts.get("test:eval", ""))
    if is_hidden and eval_script:
        if "vitest" in eval_script.lower():
            return (
                ["npm", "run", "test:eval", "--", "--reporter=json", f"--outputFile={report_path}"],
                "vitest",
            )
        return (
            ["npm", "run", "test:eval", "--", "--runInBand", "--json", f"--outputFile={report_path}"],
            "jest",
        )

    if "vitest" in test_script.lower():
        if is_hidden:
            config_path = _write_vitest_eval_config(cwd, test_dir)
            return (
                [
                    "npx",
                    "--yes",
                    "vitest",
                    "run",
                    "--config",
                    str(config_path),
                    "--reporter=json",
                    f"--outputFile={report_path}",
                ],
                "vitest",
            )
        return (
            ["npm", "test", "--", "--reporter=json", f"--outputFile={report_path}"],
            "vitest",
        )

    if "jest" in test_script.lower():
        if is_hidden:
            config_path = test_dir / "jest.config.js"
            if config_path.exists():
                return (
                    [
                        "npx",
                        "jest",
                        "--config",
                        str(config_path),
                        "--runInBand",
                        "--json",
                        f"--outputFile={report_path}",
                    ],
                    "jest",
                )
        return (
            ["npm", "test", "--", "--runInBand", "--json", f"--outputFile={report_path}"],
            "jest",
        )

    return (["npm", "test"], "unknown-node")


def _build_go_command(cwd: Path, test_dir: Path, *, is_hidden: bool) -> tuple[list[str], str]:
    """Build a Go test command with JSON output."""
    relative = _relative_to_cwd(test_dir, cwd)
    if is_hidden and relative is not None:
        package_pattern = f"./{relative.as_posix()}/..."
    else:
        package_pattern = "./..."
    return (["go", "test", "-json", package_pattern], "go test")


def _build_python_command(test_dir: Path, report_path: Path) -> tuple[list[str], str]:
    """Build a pytest command with JUnit XML output."""
    return (
        ["python", "-m", "pytest", str(test_dir), "-q", f"--junitxml={report_path}"],
        "pytest",
    )


def _missing_suite_result(
    *,
    suite_path: Path,
    report_dir: Path,
    suite_name: str,
    runtime: str,
) -> SuiteResult:
    """Return a harness-error result when the requested suite directory is missing."""
    if runtime == "node":
        report_path = report_dir / f"{suite_name}-report.json"
        framework = "node"
        command = ["npm", "test", "--", str(suite_path)]
        exit_code = 1
    elif runtime == "go":
        report_path = report_dir / f"{suite_name}-report.jsonl"
        framework = "go test"
        command = ["go", "test", str(suite_path)]
        exit_code = 1
    else:
        report_path = report_dir / f"{suite_name}-report.xml"
        command, framework = _build_python_command(suite_path, report_path)
        exit_code = 4

    return _invalid_result(
        command=command,
        framework=framework,
        exit_code=exit_code,
        report_path=report_path,
        message=f"Test directory not found: {suite_path}",
    )


def _invalid_result(
    *,
    command: list[str],
    framework: str,
    exit_code: int,
    report_path: Path,
    message: str,
) -> SuiteResult:
    """Create a harness-error result."""
    return SuiteResult(
        failed=0,
        errors=1,
        output=message,
        framework=framework,
        command=command,
        exit_code=exit_code,
        report_path=str(report_path),
        execution_ok=False,
    )


def _parse_text_summary(output: str) -> tuple[int, int, int]:
    """Best-effort parser for mocked or fallback human-readable test output."""
    passed = failed = errors = 0
    match_passed = re.search(r"(\d+)\s+passed", output)
    match_failed = re.search(r"(\d+)\s+failed", output)
    match_errors = re.search(r"(\d+)\s+errors?", output)
    if match_passed:
        passed = int(match_passed.group(1))
    if match_failed:
        failed = int(match_failed.group(1))
    if match_errors:
        errors = int(match_errors.group(1))
    return passed, failed, errors


def _parse_jest_like_report(
    report_path: Path,
    *,
    framework: str,
    command: list[str],
    exit_code: int,
    output: str,
) -> SuiteResult:
    """Parse a Jest/Vitest JSON report."""
    if not report_path.exists():
        passed, failed, errors = _parse_text_summary(output)
        return SuiteResult(
            passed=passed,
            failed=failed,
            errors=errors,
            total=passed + failed,
            output=output,
            framework=framework,
            command=command,
            exit_code=exit_code,
            report_path=str(report_path),
            execution_ok=False,
        )

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        passed, failed, errors = _parse_text_summary(output)
        return SuiteResult(
            passed=passed,
            failed=failed,
            errors=errors if errors > 0 else 1,
            total=passed + failed,
            output=f"Could not parse {framework} JSON report: {exc}\n{output}",
            framework=framework,
            command=command,
            exit_code=exit_code,
            report_path=str(report_path),
            execution_ok=False,
        )

    passed = int(data.get("numPassedTests", 0))
    failed = int(data.get("numFailedTests", 0))
    total = int(data.get("numTotalTests", passed + failed))
    errors = int(data.get("numRuntimeErrorTestSuites", 0))
    return SuiteResult(
        passed=passed,
        failed=failed,
        errors=errors,
        total=total,
        output=output,
        framework=framework,
        command=command,
        exit_code=exit_code,
        report_path=str(report_path),
        execution_ok=True,
    )


def _parse_pytest_junit_xml(
    report_path: Path,
    *,
    command: list[str],
    exit_code: int,
    output: str,
) -> SuiteResult:
    """Parse a pytest JUnit XML report."""
    if not report_path.exists():
        passed, failed, errors = _parse_text_summary(output)
        return SuiteResult(
            passed=passed,
            failed=failed,
            errors=errors,
            total=passed + failed,
            output=output,
            framework="pytest",
            command=command,
            exit_code=exit_code,
            report_path=str(report_path),
            execution_ok=False,
        )

    try:
        root = ET.fromstring(report_path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        passed, failed, errors = _parse_text_summary(output)
        return SuiteResult(
            passed=passed,
            failed=failed,
            errors=errors if errors > 0 else 1,
            total=passed + failed,
            output=f"Could not parse pytest JUnit XML report: {exc}\n{output}",
            framework="pytest",
            command=command,
            exit_code=exit_code,
            report_path=str(report_path),
            execution_ok=False,
        )

    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = list(root.findall("testsuite"))

    total = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    failed = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    passed = max(total - failed - errors - skipped, 0)

    return SuiteResult(
        passed=passed,
        failed=failed,
        errors=errors,
        total=total,
        output=output,
        framework="pytest",
        command=command,
        exit_code=exit_code,
        report_path=str(report_path),
        execution_ok=True,
    )


def _parse_go_json(
    report_path: Path,
    *,
    command: list[str],
    exit_code: int,
    stdout: str,
    output: str,
) -> SuiteResult:
    """Parse a `go test -json` stream."""
    report_path.write_text(stdout, encoding="utf-8")

    passed = 0
    failed = 0
    parse_errors = 0

    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue
        action = event.get("Action")
        if not event.get("Test"):
            continue
        if action == "pass":
            passed += 1
        elif action == "fail":
            failed += 1

    if not stdout.strip() and exit_code != 0:
        return _invalid_result(
            command=command,
            framework="go test",
            exit_code=exit_code,
            report_path=report_path,
            message=f"go test produced no machine-readable output.\n{output}",
        )

    total = passed + failed
    build_failure = exit_code != 0 and total == 0
    errors = parse_errors + (1 if build_failure else 0)

    return SuiteResult(
        passed=passed,
        failed=failed,
        errors=errors,
        total=total,
        output=output,
        framework="go test",
        command=command,
        exit_code=exit_code,
        report_path=str(report_path),
        execution_ok=(parse_errors == 0),
    )


def run_test_suite(
    cwd: Path,
    test_dir: Path,
    *,
    report_dir: Path | None = None,
    suite_name: str | None = None,
    timeout: int = 120,
    runner: Callable[..., Any] = subprocess.run,
) -> SuiteResult:
    """Run a test suite and normalize its result into a shared shape."""
    cwd = cwd.resolve()
    suite_path = test_dir.resolve() if test_dir.is_absolute() else (cwd / test_dir).resolve()
    report_dir = (report_dir or cwd).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    is_hidden = test_dir.name == "_eval" or "_eval" in test_dir.parts or (
        suite_name is not None and suite_name.startswith("eval")
    )
    runtime = _detect_runtime(cwd)
    preferred_name = "_eval" if is_hidden and runtime == "node" else None
    materialized_dir, cleanup_dir = _materialize_test_dir(
        cwd,
        suite_path,
        preferred_name=preferred_name,
    )
    suite_name = suite_name or materialized_dir.name or "suite"
    if not materialized_dir.exists() and (runtime == "python" or is_hidden):
        return _missing_suite_result(
            suite_path=suite_path,
            report_dir=report_dir,
            suite_name=suite_name,
            runtime=runtime,
        )

    if runtime == "node":
        report_path = report_dir / f"{suite_name}-report.json"
        command, framework = _build_node_command(cwd, materialized_dir, report_path, is_hidden=is_hidden)
        if framework == "unknown-node":
            if cleanup_dir is not None:
                shutil.rmtree(cleanup_dir, ignore_errors=True)
            return _invalid_result(
                command=command,
                framework=framework,
                exit_code=1,
                report_path=report_path,
                message="Unsupported Node test runner. Expected Jest or Vitest.",
            )
    elif runtime == "go":
        report_path = report_dir / f"{suite_name}-report.jsonl"
        command, framework = _build_go_command(cwd, materialized_dir, is_hidden=is_hidden)
    else:
        report_path = report_dir / f"{suite_name}-report.xml"
        command, framework = _build_python_command(materialized_dir, report_path)

    try:
        proc = runner(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd),
        )
    except subprocess.TimeoutExpired:
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
        return _invalid_result(
            command=command,
            framework=framework,
            exit_code=124,
            report_path=report_path,
            message=f"Test suite timed out after {timeout}s",
        )
    except FileNotFoundError:
        if cleanup_dir is not None:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
        return _invalid_result(
            command=command,
            framework=framework,
            exit_code=127,
            report_path=report_path,
            message=f"Test runner not found for command: {' '.join(command)}",
        )

    output = _cap_output((proc.stdout or "") + (proc.stderr or ""))

    if runtime == "node":
        result = _parse_jest_like_report(
            report_path,
            framework=framework,
            command=command,
            exit_code=proc.returncode,
            output=output,
        )
    elif runtime == "go":
        result = _parse_go_json(
            report_path,
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            output=output,
        )
    else:
        result = _parse_pytest_junit_xml(
            report_path,
            command=command,
            exit_code=proc.returncode,
            output=output,
        )

    if cleanup_dir is not None:
        shutil.rmtree(cleanup_dir, ignore_errors=True)
    return result


def _run_suite_command(args: argparse.Namespace) -> int:
    """CLI handler for executing and normalizing a test suite."""
    result = run_test_suite(
        Path(args.cwd),
        Path(args.test_dir),
        report_dir=Path(args.report_dir) if args.report_dir else None,
        suite_name=args.suite_name,
        timeout=args.timeout,
    )
    print(result.model_dump_json())
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run and normalize benchmark test suites.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_suite_parser = subparsers.add_parser("run-suite")
    run_suite_parser.add_argument("--cwd", required=True)
    run_suite_parser.add_argument("--test-dir", required=True)
    run_suite_parser.add_argument("--report-dir")
    run_suite_parser.add_argument("--suite-name")
    run_suite_parser.add_argument("--timeout", type=int, default=120)
    run_suite_parser.set_defaults(func=_run_suite_command)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
