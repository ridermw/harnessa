#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-benchmark.sh — Run a single Harnessa benchmark via Copilot CLI
# =============================================================================
# Usage: ./scripts/run-benchmark.sh <benchmark-name> <mode> [options]
#
# Arguments:
#   benchmark-name   Must match a directory in benchmarks/
#   mode             solo | trio
#
# Options:
#   --model <model>           Model to use (REQUIRED)
#   --eval-model <model>      Evaluator model (default: same as --model)
#   --max-iterations <n>      Max evaluator retry loops for trio (default: 3)
#   --run-id <id>             Run ID (default: auto-generated UUID)
#
# Examples:
#   ./scripts/run-benchmark.sh small-bugfix-python trio --model claude-sonnet-4
#   ./scripts/run-benchmark.sh small-bugfix-python solo --model gpt-5.4
#   ./scripts/run-benchmark.sh small-bugfix-python solo --model claude-sonnet-4 --eval-model gpt-5.4
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { echo "[harnessa] $(date '+%H:%M:%S') $*"; }
err()  { echo "[harnessa] ERROR: $*" >&2; }
die()  { err "$@"; exit 1; }

usage() {
  sed -n '2,/^# =====/p' "$0" | grep '^#' | sed 's/^# \?//'
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command '$1' not found. Please install it."
}

generate_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  else
    # Fallback: use /dev/urandom
    od -x /dev/urandom | head -1 | awk '{print $2$3"-"$4"-"$5"-"$6"-"$7$8$9}'
  fi
}

run_suite_json() {
  local cwd="$1"
  local test_dir="$2"
  local suite_name="$3"

  PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python -m harnessa.test_execution run-suite \
      --cwd "$cwd" \
      --test-dir "$test_dir" \
      --report-dir "$TELEMETRY_DIR" \
      --suite-name "$suite_name"
}

install_node_dependencies() {
  local message="$1"
  if [[ -f "$WORKSPACE/package.json" ]]; then
    log "$message"
    (cd "$WORKSPACE" && npm install --quiet 2>/dev/null) || true
  fi
}

write_canonical_manifest() {
  PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python - <<'PY'
import json
import os
from datetime import datetime
from pathlib import Path

from harnessa.telemetry.models import (
    BenchmarkScore,
    BugReport,
    ModelInfo,
    QualityTrend,
    RunManifest,
    RunValidity,
    Severity,
    SprintMetrics,
    SuiteResult,
)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def coerce_scores(raw_scores: object) -> list[BenchmarkScore]:
    if isinstance(raw_scores, dict):
        return [
            BenchmarkScore(criterion=criterion, score=float(score), justification="")
            for criterion, score in raw_scores.items()
        ]

    scores: list[BenchmarkScore] = []
    for entry in raw_scores if isinstance(raw_scores, list) else []:
        scores.append(
            BenchmarkScore(
                criterion=str(entry.get("criterion", "Unknown")),
                score=float(entry.get("score", 0)),
                justification=str(entry.get("justification", "")),
            )
        )
    return scores


def coerce_bug(index: int, raw_bug: object) -> BugReport:
    if isinstance(raw_bug, str):
        return BugReport(
            id=f"bug-{index}",
            severity=Severity.MEDIUM,
            description=raw_bug,
            file="",
            line=0,
        )

    severity = str(raw_bug.get("severity", "medium")).lower()
    if severity not in {"critical", "high", "medium", "low"}:
        severity = "medium"

    raw_line = raw_bug.get("line", 0)
    try:
        line = int(raw_line or 0)
    except (TypeError, ValueError):
        line = 0

    return BugReport(
        id=str(raw_bug.get("id", f"bug-{index}")),
        severity=Severity(severity),
        description=str(raw_bug.get("description", "Unspecified issue")),
        file=str(raw_bug.get("file", "")),
        line=line,
    )


def coerce_sprints(raw_sprints: object) -> list[SprintMetrics]:
    sprints: list[SprintMetrics] = []
    for entry in raw_sprints if isinstance(raw_sprints, list) else []:
        sprints.append(SprintMetrics.model_validate(entry))
    return sprints


def build_quality_trends(sprints: list[SprintMetrics]) -> list[QualityTrend]:
    criterion_scores: dict[str, list[float]] = {}
    for sprint in sprints:
        for score in sprint.scores:
            criterion_scores.setdefault(score.criterion, []).append(float(score.score))
    return [
        QualityTrend(criterion=criterion, scores=scores)
        for criterion, scores in sorted(criterion_scores.items())
    ]


raw_scores = json.loads(os.environ["EVAL_SCORES"])
raw_bugs = json.loads(os.environ["BUGS"])
raw_sprints = json.loads(os.environ.get("SPRINTS_JSON", "[]"))
visible_tests = SuiteResult.model_validate(json.loads(os.environ["VISIBLE_TESTS"]))
eval_tests = SuiteResult.model_validate(json.loads(os.environ["EVAL_TESTS"]))
sprints = coerce_sprints(raw_sprints)
quality_trends = build_quality_trends(sprints)

model_info = [ModelInfo(provider="copilot-cli", model_id=os.environ["MODEL"])]
if os.environ["EVAL_MODEL"] != os.environ["MODEL"]:
    model_info.append(ModelInfo(provider="copilot-cli", model_id=os.environ["EVAL_MODEL"]))

manifest = RunManifest(
    run_id=os.environ["RUN_ID"],
    benchmark=os.environ["BENCHMARK"],
    mode=os.environ["MODE"],
    model_info=model_info,
    scores=coerce_scores(raw_scores),
    bugs=[coerce_bug(index, raw_bug) for index, raw_bug in enumerate(raw_bugs, start=1)],
    quality_trends=quality_trends,
    sprints=sprints,
    planner_duration_s=float(os.environ["PLANNER_DURATION"]),
    generator_duration_s=float(os.environ["GENERATOR_DURATION"]),
    evaluator_duration_s=float(os.environ["EVALUATOR_DURATION"]),
    iterations=int(os.environ["ITERATIONS"]),
    visible_tests=visible_tests,
    eval_tests=eval_tests,
    run_validity=RunValidity(os.environ["RUN_VALIDITY"]),
    cost_usd=0.0,
    duration_s=float(os.environ["TOTAL_DURATION"]),
    verdict=os.environ["VERDICT"],
    started_at=parse_timestamp(os.environ["START_TIMESTAMP"]),
    finished_at=parse_timestamp(os.environ["END_TIMESTAMP"]),
)

manifest_path = Path(os.environ["MANIFEST_PATH"])
manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
PY
}

append_sprint_metric() {
  local iteration="$1"
  local duration_s="$2"
  local sprint_entry

  sprint_entry=$(jq -cn \
    --argjson iteration "$iteration" \
    --argjson scores "$EVAL_SCORES" \
    --argjson bugs "$BUGS" \
    --argjson duration "$duration_s" \
    '{iteration: $iteration, scores: $scores, bugs_found: ($bugs | length), duration_s: $duration}') || return 1

  SPRINTS_JSON=$(echo "$SPRINTS_JSON" | jq -c --argjson entry "$sprint_entry" '. + [$entry]')
}

write_iteration_feedback() {
  local iteration="$1"
  local feedback_path="$GENERATOR_DIR/feedback_iter${iteration}.md"

  ITERATION_LABEL="$iteration" \
  FEEDBACK_PATH="$feedback_path" \
  EVAL_JSON_PATH="$EVALUATIONS_DIR/eval.json" \
  RUN_VALIDITY_VALUE="$RUN_VALIDITY" \
  VISIBLE_TESTS_JSON="$VISIBLE_TESTS" \
  EVAL_TESTS_JSON="$EVAL_TESTS" \
    python - <<'PY'
import json
import os
from pathlib import Path


def excerpt(text: str, limit: int = 1200) -> str:
    normalized = (text or "").strip()
    if not normalized:
        return "(no output)"
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n...[truncated]..."


def suite_section(title: str, suite: dict[str, object]) -> list[str]:
    command = " ".join(str(part) for part in suite.get("command", []))
    return [
        f"## {title}",
        f"- Framework: {suite.get('framework') or 'unknown'}",
        f"- Command: {command or '(none)'}",
        (
            "- Result: "
            f"passed={suite.get('passed', 0)}, "
            f"failed={suite.get('failed', 0)}, "
            f"errors={suite.get('errors', 0)}, "
            f"total={suite.get('total', 0)}, "
            f"exit={suite.get('exit_code', 0)}"
        ),
        f"- Trusted evidence: {suite.get('execution_ok', False)}",
        "",
        "```text",
        excerpt(str(suite.get("output", ""))),
        "```",
        "",
    ]


iteration = os.environ["ITERATION_LABEL"]
feedback_path = Path(os.environ["FEEDBACK_PATH"])
eval_json = json.loads(Path(os.environ["EVAL_JSON_PATH"]).read_text(encoding="utf-8"))
visible = json.loads(os.environ["VISIBLE_TESTS_JSON"])
hidden = json.loads(os.environ["EVAL_TESTS_JSON"])
run_validity = os.environ["RUN_VALIDITY_VALUE"]

joined_output = "\n".join(
    str(section.get("output", ""))
    for section in (visible, hidden)
).lower()
suggestions: list[str] = []

if "cannot find module" in joined_output or "module not found" in joined_output:
    suggestions.append(
        "A dependency or import is missing. Update package manifests and imports so the app and tests can boot before adding more feature code."
    )
if any(
    marker in joined_output
    for marker in ("build failed", "syntax error", "redeclared", "undefined", "compile error")
):
    suggestions.append(
        "The code is failing before tests can run. Pivot to restoring a clean build first, then continue feature work."
    )
if (
    int(visible.get("total", 0)) == 0
    and int(visible.get("errors", 0)) > 0
    and int(hidden.get("total", 0)) == 0
    and int(hidden.get("errors", 0)) > 0
):
    suggestions.append(
        "Both visible and hidden suites are failing before any test body executes. Treat this as a setup/runtime blocker, not a polish issue."
    )
if not suggestions:
    suggestions.append(
        "Use the failing tests and bugs below as the acceptance criteria for the next attempt. You may refine the current implementation or pivot entirely."
    )

lines = [
    f"# Iteration {iteration} feedback",
    "",
    "## Summary",
    f"- Verdict: {eval_json.get('verdict', 'FAIL')}",
    f"- Run validity: {run_validity}",
    f"- Visible tests: {visible.get('passed', 0)}/{visible.get('total', 0)} passed (errors={visible.get('errors', 0)})",
    f"- Hidden tests: {hidden.get('passed', 0)}/{hidden.get('total', 0)} passed (errors={hidden.get('errors', 0)})",
    "",
    "## Criterion scores",
]

for score in eval_json.get("scores", []):
    lines.append(
        f"- {score.get('criterion', 'unknown')}: {score.get('score', '?')}/10 — {score.get('justification', '')}"
    )

lines.extend(["", "## Bugs to fix"])
bugs = eval_json.get("bugs", [])
if bugs:
    for bug in bugs:
        lines.append(
            f"- [{bug.get('severity', 'unknown')}] {bug.get('file', 'unknown')}:{bug.get('line', 0)} — {bug.get('description', '')}"
        )
else:
    lines.append("- None listed by evaluator.")

lines.extend(["", "## Required next-step guidance"])
for suggestion in suggestions:
    lines.append(f"- {suggestion}")
lines.append(
    "- Review the failing suites and fix the highest-leverage blocker first, even if that means changing package manifests, imports, or bootstrapping code."
)
lines.append(
    "- This is an adversarial review loop: if the current implementation path is broken, pivot instead of polishing around the failure."
)
lines.append("")

lines.extend(suite_section("Visible test evidence", visible))
lines.extend(suite_section("Hidden evaluation evidence", hidden))

feedback_path.write_text("\n".join(lines), encoding="utf-8")
print(feedback_path.read_text(encoding="utf-8"), end="")
PY
}

# Extract JSON from evaluator output (finds first { ... } block)
extract_json() {
  local input="$1"
  # Strategy 1: Try the full output as JSON directly
  if echo "$input" | jq . >/dev/null 2>&1; then
    echo "$input"
    return
  fi
  # Strategy 2: Extract content between first { and last }
  local extracted
  extracted=$(echo "$input" | python3 -c "
import sys, json
text = sys.stdin.read()
# Find the first { and last }
start = text.find('{')
end = text.rfind('}')
if start >= 0 and end > start:
    candidate = text[start:end+1]
    try:
        obj = json.loads(candidate)
        print(json.dumps(obj))
    except json.JSONDecodeError:
        pass
" 2>/dev/null)
  if [[ -n "$extracted" ]] && echo "$extracted" | jq . >/dev/null 2>&1; then
    echo "$extracted"
    return
  fi
  # Strategy 3: Look for ```json code blocks
  extracted=$(echo "$input" | sed -n '/```json/,/```/p' | sed '1d;$d' | head -50)
  if [[ -n "$extracted" ]] && echo "$extracted" | jq . >/dev/null 2>&1; then
    echo "$extracted"
    return
  fi
  # Nothing found
  echo "{}"
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

[[ $# -lt 2 ]] && usage

BENCHMARK="$1"; shift
MODE="$1"; shift

MODEL=""
EVAL_MODEL=""
MAX_ITERATIONS=3
RUN_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)        MODEL="$2"; shift 2 ;;
    --eval-model)   EVAL_MODEL="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --run-id)       RUN_ID="$2"; shift 2 ;;
    -h|--help)      usage ;;
    *)              die "Unknown option: $1" ;;
  esac
done

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

require_cmd jq
require_cmd copilot

[[ -z "$MODEL" ]] && die "--model is required"
[[ "$MODE" != "solo" && "$MODE" != "trio" ]] && die "Mode must be 'solo' or 'trio', got '$MODE'"

BENCHMARK_DIR="$REPO_ROOT/benchmarks/$BENCHMARK"
[[ -d "$BENCHMARK_DIR" ]] || die "Benchmark not found: $BENCHMARK_DIR"
[[ -f "$BENCHMARK_DIR/TASK.md" ]] || die "No TASK.md in $BENCHMARK_DIR"

[[ -z "$EVAL_MODEL" ]] && EVAL_MODEL="$MODEL"
[[ -z "$RUN_ID" ]] && RUN_ID="$(generate_uuid)"

# ---------------------------------------------------------------------------
# Setup run directory
# ---------------------------------------------------------------------------

RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
WORKSPACE="$RUN_DIR/workspace"
EVAL_DIR="$RUN_DIR/_eval"
PLANNER_DIR="$RUN_DIR/planner"
GENERATOR_DIR="$RUN_DIR/generator"
EVALUATIONS_DIR="$RUN_DIR/evaluations"
TELEMETRY_DIR="$RUN_DIR/telemetry"

mkdir -p "$WORKSPACE" "$PLANNER_DIR" "$GENERATOR_DIR" "$EVALUATIONS_DIR" "$TELEMETRY_DIR"

log "Benchmark:  $BENCHMARK"
log "Mode:       $MODE"
log "Model:      $MODEL"
log "Eval model: $EVAL_MODEL"
log "Run ID:     $RUN_ID"
log "Run dir:    $RUN_DIR"

# Copy benchmark to workspace (generator works on this copy)
cp -R "$BENCHMARK_DIR"/* "$WORKSPACE"/ 2>/dev/null || true
cp -R "$BENCHMARK_DIR"/.[!.]* "$WORKSPACE"/ 2>/dev/null || true

# Move _eval/ out of workspace — generator must NEVER see it
if [[ -d "$WORKSPACE/_eval" ]]; then
  mv "$WORKSPACE/_eval" "$EVAL_DIR"
elif [[ -d "$BENCHMARK_DIR/_eval" ]]; then
  cp -R "$BENCHMARK_DIR/_eval" "$EVAL_DIR"
fi

# Install deps if needed
if [[ -f "$WORKSPACE/package.json" ]] && [[ ! -d "$WORKSPACE/node_modules" ]]; then
  install_node_dependencies "Installing Node.js dependencies..."
fi

# Record start time
START_TIME=$(date +%s)
START_TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

PLANNER_DURATION=0
GENERATOR_DURATION=0
EVALUATOR_DURATION=0
ITERATIONS=0
RUN_VALIDITY="clean"
VERDICT="INCOMPLETE"
EVAL_SCORES='[]'
BUGS='[]'
VISIBLE_TESTS='null'
EVAL_TESTS='null'
SPRINTS_JSON='[]'

# ---------------------------------------------------------------------------
# SOLO mode
# ---------------------------------------------------------------------------

run_solo() {
  log "=== SOLO mode ==="

  # --- Generator ---
  log "Running generator..."
  local gen_start gen_end gen_output
  gen_start=$(date +%s)

  gen_output=$(cd "$WORKSPACE" && copilot -p \
    "Read TASK.md in the current directory. Implement the fix or feature it describes. Run the automated tests in tests/ to verify your changes pass. Make minimal, clean changes. Do not start long-running dev servers, watch processes, or manual demos. Do not create plans, todo lists, or extra documentation." \
    -s --no-ask-user --model "$MODEL" \
    --allow-tool='write, shell(*), read' --allow-all-paths 2>&1) || {
    err "Generator failed"
    echo "$gen_output" > "$GENERATOR_DIR/transcript.txt"
    gen_end=$(date +%s)
    GENERATOR_DURATION=$((gen_end - gen_start))
    return 1
  }

  gen_end=$(date +%s)
  GENERATOR_DURATION=$((gen_end - gen_start))
  echo "$gen_output" > "$GENERATOR_DIR/transcript.txt"
  log "Generator complete (${GENERATOR_DURATION}s)"
  ITERATIONS=1

  install_node_dependencies "Refreshing Node.js dependencies after generator..."

  # --- Evaluator ---
  run_evaluator ""
}

# ---------------------------------------------------------------------------
# TRIO mode
# ---------------------------------------------------------------------------

run_trio() {
  log "=== TRIO mode ==="

  # --- Planner ---
  log "Running planner..."
  local plan_start plan_end plan_output
  plan_start=$(date +%s)

  plan_output=$(cd "$WORKSPACE" && copilot -p \
    "Read TASK.md in the current directory. You are a planner agent. Expand this task into a concise spec covering: problem statement, root cause analysis (if bugfix), proposed approach with specific steps, acceptance criteria, and edge cases to handle. Do not run shell commands, modify files, create todo lists, or start servers. Write only the spec to stdout." \
    -s --no-ask-user --model "$MODEL" \
    --allow-tool='read' --allow-all-paths 2>&1) || {
    err "Planner failed"
    echo "$plan_output" > "$PLANNER_DIR/spec.md"
    plan_end=$(date +%s)
    PLANNER_DURATION=$((plan_end - plan_start))
    return 1
  }

  plan_end=$(date +%s)
  PLANNER_DURATION=$((plan_end - plan_start))
  echo "$plan_output" > "$PLANNER_DIR/spec.md"
  log "Planner complete (${PLANNER_DURATION}s)"

  # --- Generator + Evaluator loop ---
  local feedback=""
  local iteration=0

  while [[ $iteration -lt $MAX_ITERATIONS ]]; do
    iteration=$((iteration + 1))
    ITERATIONS=$iteration
    log "--- Iteration $iteration/$MAX_ITERATIONS ---"
    local iter_start iter_end iter_duration
    iter_start=$(date +%s)

    # Build generator prompt
    local gen_prompt="Read TASK.md in the current directory. "
    gen_prompt+="Here is the detailed spec from the planner:\n\n"
    gen_prompt+="$(cat "$PLANNER_DIR/spec.md")\n\n"

    if [[ -n "$feedback" ]]; then
      gen_prompt+="IMPORTANT — you are in an adversarial review loop. The evaluator rejected your previous attempt.\n"
      gen_prompt+="You may refine the current implementation or pivot entirely if the current path is broken.\n"
      gen_prompt+="Treat dependency, build, startup, and test-execution blockers as the highest priority; restore a runnable system before adding more feature work.\n\n"
      gen_prompt+="Evaluator feedback and harness evidence:\n\n"
      gen_prompt+="$feedback\n\n"
      gen_prompt+="Fix the issues described above and use the failing suites as acceptance criteria for this iteration. "
    fi

    gen_prompt+="Implement the fix or feature. Run the automated tests in tests/ to verify your changes pass. Make minimal, clean changes. If tests reveal setup or dependency issues, fix those before polishing features. Do not start long-running dev servers, watch processes, or manual demos. Do not create plans, todo lists, or extra documentation."

    # --- Generator ---
    log "Running generator (iteration $iteration)..."
    local gen_start gen_end gen_output
    gen_start=$(date +%s)

    gen_output=$(cd "$WORKSPACE" && copilot -p "$gen_prompt" \
      -s --no-ask-user --model "$MODEL" \
      --allow-tool='write, shell(*), read' --allow-all-paths 2>&1) || {
      err "Generator failed (iteration $iteration)"
      echo "$gen_output" > "$GENERATOR_DIR/transcript-iter${iteration}.txt"
      gen_end=$(date +%s)
      GENERATOR_DURATION=$((GENERATOR_DURATION + gen_end - gen_start))
      continue
    }

    gen_end=$(date +%s)
    GENERATOR_DURATION=$((GENERATOR_DURATION + gen_end - gen_start))
    echo "$gen_output" > "$GENERATOR_DIR/transcript-iter${iteration}.txt"
    log "Generator complete (iteration $iteration)"

    install_node_dependencies "Refreshing Node.js dependencies after generator iteration $iteration..."

    # --- Evaluator ---
    run_evaluator "$iteration"
    iter_end=$(date +%s)
    iter_duration=$((iter_end - iter_start))
    append_sprint_metric "$iteration" "$iter_duration"

    # Check verdict
    if [[ "$VERDICT" == "PASS" ]]; then
      log "PASS on iteration $iteration"
      break
    else
      feedback=$(write_iteration_feedback "$iteration")
      log "Feedback saved to $GENERATOR_DIR/feedback_iter${iteration}.md"
      log "FAIL on iteration $iteration — retrying..."
    fi
  done
}

# ---------------------------------------------------------------------------
# Evaluator (shared by solo and trio)
# ---------------------------------------------------------------------------

run_evaluator() {
  local iteration_label="$1"
  log "Running evaluator..."

  local eval_start eval_end eval_output eval_json
  local visible_summary hidden_summary

  eval_start=$(date +%s)

  log "Running visible tests..."
  VISIBLE_TESTS=$(run_suite_json "$WORKSPACE" "$WORKSPACE/tests" "visible-tests")

  log "Running hidden eval tests..."
  EVAL_TESTS=$(run_suite_json "$WORKSPACE" "$EVAL_DIR" "eval-tests")

  if ! echo "$VISIBLE_TESTS" | jq -e '.execution_ok == true' >/dev/null 2>&1; then
    RUN_VALIDITY="harness_error"
  fi
  if ! echo "$EVAL_TESTS" | jq -e '.execution_ok == true' >/dev/null 2>&1; then
    RUN_VALIDITY="harness_error"
  fi

  visible_summary=$(echo "$VISIBLE_TESTS" | jq '.')
  hidden_summary=$(echo "$EVAL_TESTS" | jq '.')

  local eval_prompt="IMPORTANT: Your ENTIRE response must be a single JSON object. No text before or after it. No markdown formatting. No explanation. "
  eval_prompt+="You are a skeptical code evaluator grading an AI-generated solution. "
  eval_prompt+="The harness has already executed the visible and hidden test suites. "
  eval_prompt+="Do NOT run benchmark tests yourself. Use only the harness evidence below when judging functionality and test coverage. "
  eval_prompt+="Visible test evidence:\n$visible_summary\n\n"
  eval_prompt+="Hidden evaluation evidence:\n$hidden_summary\n\n"
  eval_prompt+="Grade the solution on 4 criteria (1-10 each): "
  eval_prompt+="product_depth (does it fully solve the task?), "
  eval_prompt+="functionality (do tests pass? does the code work?), "
  eval_prompt+="code_quality (clean, minimal, idiomatic?), "
  eval_prompt+="test_coverage (are edge cases handled?). "
  eval_prompt+="Return bugs as objects with fields: id, severity, description, file, line. "
  eval_prompt+="Do not start dev servers, watchers, or manual demos. "
  eval_prompt+="Be harsh and objective. Any criterion below 6 means overall FAIL. "
  eval_prompt+="After analyzing the code and harness evidence, respond with ONLY this JSON (no other text): "
  eval_prompt+='{\"scores\": [{\"criterion\": \"product_depth\", \"score\": N, \"justification\": \"...\"}, {\"criterion\": \"functionality\", \"score\": N, \"justification\": \"...\"}, {\"criterion\": \"code_quality\", \"score\": N, \"justification\": \"...\"}, {\"criterion\": \"test_coverage\", \"score\": N, \"justification\": \"...\"}], '
  eval_prompt+='\"verdict\": \"PASS\", '
  eval_prompt+='\"bugs\": [], '
  eval_prompt+='\"justification\": \"one sentence per criterion\"}'
  eval_prompt+=" Replace N with integer scores 1-10. Replace PASS with FAIL if any score < 6."

  eval_output=$(cd "$WORKSPACE" && copilot -p "$eval_prompt" \
    -s --no-ask-user --model "$EVAL_MODEL" \
    --allow-tool='read' --allow-all-paths 2>&1) || {
      err "Evaluator failed"
      echo "$eval_output" > "$EVALUATIONS_DIR/eval-raw${iteration_label:+-iter$iteration_label}.txt"
    }

  eval_end=$(date +%s)
  EVALUATOR_DURATION=$((EVALUATOR_DURATION + eval_end - eval_start))

  # Save raw output
  echo "$eval_output" > "$EVALUATIONS_DIR/eval-raw${iteration_label:+-iter$iteration_label}.txt"
  log "Evaluator complete (${EVALUATOR_DURATION}s total)"

  # Parse JSON from evaluator output
  eval_json=$(extract_json "$eval_output")

  if echo "$eval_json" | jq . >/dev/null 2>&1; then
    if echo "$eval_json" | jq -e '
      ((.bugs // []) | map(tostring | ascii_downcase) | join(" ")) as $bugs |
      ((.justification // "") | ascii_downcase) as $justification |
      ($bugs | test("permission denied|cannot run tests|could not run tests|execution was blocked")) or
      ($justification | test("permission denied|cannot run tests|could not run tests|execution was blocked"))
    ' >/dev/null 2>&1; then
      RUN_VALIDITY="tainted"
      eval_json=$(echo "$eval_json" | jq '
        .verdict = "FAIL"
        | .scores = (
            (.scores // [])
            | map(
                if (.criterion == "functionality") or (.criterion == "test_coverage")
                then .score = 1 | .justification = "Harness evidence was not trusted; forced low score."
                else .
                end
              )
          )
        | .bugs = ((.bugs // []) + [{"id": "harness-tainted", "severity": "medium", "description": "Evaluator claimed benchmark tests could not be run despite harness evidence being supplied.", "file": "", "line": 0}])
      ')
    fi

    if echo "$VISIBLE_TESTS" | jq -e '.failed > 0 or .errors > 0' >/dev/null 2>&1 || \
       echo "$EVAL_TESTS" | jq -e '.failed > 0 or .errors > 0' >/dev/null 2>&1; then
      eval_json=$(echo "$eval_json" | jq '
        .verdict = "FAIL"
        | .scores = (
            (.scores // [])
            | map(
                if (.criterion == "functionality") or (.criterion == "test_coverage")
                then
                  .score = (if .score > 5 then 5 else .score end)
                  | .justification = ((.justification // "") + " Clamped by harness because automated tests did not fully pass.")
                else .
                end
              )
          )
      ')
    fi

    if [[ "$RUN_VALIDITY" != "clean" ]]; then
      eval_json=$(echo "$eval_json" | jq '
        .verdict = "FAIL"
        | .scores = (
            (.scores // [])
            | map(
                if (.criterion == "functionality") or (.criterion == "test_coverage")
                then .score = 1 | .justification = "Harness could not trust the test evidence."
                else .
                end
              )
          )
      ')
    fi

    echo "$eval_json" | jq . > "$EVALUATIONS_DIR/eval.json"
    VERDICT=$(echo "$eval_json" | jq -r '.verdict // "FAIL"')
    EVAL_SCORES=$(echo "$eval_json" | jq -c '.scores // []')
    BUGS=$(echo "$eval_json" | jq -c '.bugs // []')
    log "Evaluator verdict: $VERDICT"
    log "Scores: $EVAL_SCORES"
  else
    err "Could not parse evaluator JSON output"
    RUN_VALIDITY="tainted"
    echo '{"scores": [], "verdict": "FAIL", "bugs": [], "justification": "Failed to parse evaluator output"}' > "$EVALUATIONS_DIR/eval.json"
    VERDICT="FAIL"
    EVAL_SCORES='[]'
    BUGS='[]'
  fi
}

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

case "$MODE" in
  solo) run_solo ;;
  trio) run_trio ;;
esac

# ---------------------------------------------------------------------------
# Telemetry phase
# ---------------------------------------------------------------------------

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
END_TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
MANIFEST_PATH="$TELEMETRY_DIR/run-manifest.json"

if [[ "$VISIBLE_TESTS" == "null" ]]; then
  RUN_VALIDITY="harness_error"
  VISIBLE_TESTS='{"passed":0,"failed":0,"errors":1,"total":0,"output":"Visible tests never ran.","framework":"","command":[],"exit_code":1,"report_path":"","execution_ok":false}'
fi

if [[ "$EVAL_TESTS" == "null" ]]; then
  RUN_VALIDITY="harness_error"
  EVAL_TESTS='{"passed":0,"failed":0,"errors":1,"total":0,"output":"Hidden eval tests never ran.","framework":"","command":[],"exit_code":1,"report_path":"","execution_ok":false}'
fi

export RUN_ID BENCHMARK MODE MODEL EVAL_MODEL PLANNER_DURATION GENERATOR_DURATION
export EVALUATOR_DURATION TOTAL_DURATION ITERATIONS VERDICT EVAL_SCORES BUGS
export VISIBLE_TESTS EVAL_TESTS RUN_VALIDITY START_TIMESTAMP END_TIMESTAMP MANIFEST_PATH
export SPRINTS_JSON

write_canonical_manifest

log "Telemetry saved to $TELEMETRY_DIR/run-manifest.json"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=============================================="
echo "  BENCHMARK RUN COMPLETE"
echo "=============================================="
echo "  Benchmark:    $BENCHMARK"
echo "  Mode:         $MODE"
echo "  Model:        $MODEL"
echo "  Eval Model:   $EVAL_MODEL"
echo "  Run ID:       $RUN_ID"
echo "  Iterations:   $ITERATIONS"
echo "  Duration:     ${TOTAL_DURATION}s"
echo "  Validity:     $RUN_VALIDITY"
echo "  Visible tests: $(echo "$VISIBLE_TESTS" | jq -r '"\(.passed)/\(.total) passed"')"
echo "  Eval tests:    $(echo "$EVAL_TESTS" | jq -r '"\(.passed)/\(.total) passed"')"
echo "  Scores:       $(echo "$EVAL_SCORES" | jq -c 'map({(.criterion): .score}) | add // {}')"
echo "  Verdict:      $VERDICT"
echo "=============================================="
