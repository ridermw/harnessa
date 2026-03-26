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

# Detect the test runner for a workspace directory and run tests.
# Usage: run_tests <workspace_dir> [test_dir]
# Prints JSON: {"passed": N, "failed": N, "total": N}
run_tests() {
  local dir="$1"
  local test_dir="${2:-tests}"
  local output
  local passed=0 failed=0 total=0

  pushd "$dir" >/dev/null

  if [[ -f "package.json" ]]; then
    # Node.js project — use npm test
    output=$(npm test -- --reporter=verbose 2>&1) || true
    # Parse vitest/jest output: "Tests  X passed | Y failed"
    passed=$(echo "$output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
    failed=$(echo "$output" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
  elif [[ -f "go.mod" ]] || ls ./*.go >/dev/null 2>&1; then
    # Go project
    output=$(go test ./... -v 2>&1) || true
    passed=$(echo "$output" | grep -c '^--- PASS' || echo "0")
    failed=$(echo "$output" | grep -c '^--- FAIL' || echo "0")
  else
    # Default: Python / pytest
    if [[ -d "$test_dir" ]]; then
      output=$(python -m pytest "$test_dir" -q 2>&1) || true
      # Parse pytest output: "X passed, Y failed" or "X passed"
      passed=$(echo "$output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
      failed=$(echo "$output" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
    fi
  fi

  # Ensure numeric — strip whitespace and take only first number
  passed=$(echo "$passed" | tr -d '[:space:]' | head -c 10)
  failed=$(echo "$failed" | tr -d '[:space:]' | head -c 10)
  passed=$((${passed:-0} + 0))
  failed=$((${failed:-0} + 0))
  total=$((passed + failed))

  popd >/dev/null
  echo "{\"passed\": $passed, \"failed\": $failed, \"total\": $total}"
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
  log "Installing Node.js dependencies..."
  (cd "$WORKSPACE" && npm install --quiet 2>/dev/null) || true
fi

# Record start time
START_TIME=$(date +%s)
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

PLANNER_DURATION=0
GENERATOR_DURATION=0
EVALUATOR_DURATION=0
ITERATIONS=0
VERDICT="INCOMPLETE"
EVAL_SCORES='{}'
BUGS='[]'

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
    "Read TASK.md in the current directory. Implement the fix or feature it describes. Run the tests in tests/ to verify your changes pass. Make minimal, clean changes." \
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
    "Read TASK.md in the current directory. You are a planner agent. Expand this task into a comprehensive spec covering: problem statement, root cause analysis (if bugfix), proposed approach with specific steps, acceptance criteria, edge cases to handle. Write the complete spec to stdout." \
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

    # Build generator prompt
    local gen_prompt="Read TASK.md in the current directory. "
    gen_prompt+="Here is the detailed spec from the planner:\n\n"
    gen_prompt+="$(cat "$PLANNER_DIR/spec.md")\n\n"

    if [[ -n "$feedback" ]]; then
      gen_prompt+="IMPORTANT — the evaluator rejected your previous attempt with this feedback:\n\n"
      gen_prompt+="$feedback\n\n"
      gen_prompt+="Fix the issues described above. "
    fi

    gen_prompt+="Implement the fix or feature. Run the tests in tests/ to verify your changes pass. Make minimal, clean changes."

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

    # --- Evaluator ---
    run_evaluator "$iteration"

    # Check verdict
    if [[ "$VERDICT" == "PASS" ]]; then
      log "PASS on iteration $iteration"
      break
    else
      # Extract feedback for next iteration
      feedback=$(jq -r '.justification // "No justification provided"' "$EVALUATIONS_DIR/eval.json" 2>/dev/null || echo "Evaluation failed — retry.")
      local bug_list
      bug_list=$(jq -r '.bugs[]? | "- [\(.severity)] \(.file // "unknown"): \(.description)"' "$EVALUATIONS_DIR/eval.json" 2>/dev/null || echo "")
      if [[ -n "$bug_list" ]]; then
        feedback+=$'\n\nBugs found:\n'"$bug_list"
      fi
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

  # Temporarily copy _eval/ into workspace for the evaluator
  cp -R "$EVAL_DIR" "$WORKSPACE/_eval" 2>/dev/null || true

  eval_start=$(date +%s)

  local eval_prompt="IMPORTANT: Your ENTIRE response must be a single JSON object. No text before or after it. No markdown formatting. No explanation. "
  eval_prompt+="You are a skeptical code evaluator grading an AI-generated solution. "
  eval_prompt+="Run the visible tests in the tests/ directory. "
  eval_prompt+="Run the hidden acceptance tests in the _eval/ directory against the code. "

  if [[ -f "$WORKSPACE/package.json" ]]; then
    eval_prompt+="This is a Node.js/TypeScript project — use npm test for visible tests and npx vitest run _eval/ for hidden tests. "
  elif [[ -f "$WORKSPACE/go.mod" ]] || ls "$WORKSPACE"/*.go >/dev/null 2>&1; then
    eval_prompt+="This is a Go project — use 'go test ./...' for visible and 'go test ./_eval/...' for hidden tests. "
  else
    eval_prompt+="This is a Python project — use 'python -m pytest tests/' for visible and 'python -m pytest _eval/' for hidden tests. "
  fi

  eval_prompt+="Grade the solution on 4 criteria (1-10 each): "
  eval_prompt+="product_depth (does it fully solve the task?), "
  eval_prompt+="functionality (do tests pass? does the code work?), "
  eval_prompt+="code_quality (clean, minimal, idiomatic?), "
  eval_prompt+="test_coverage (are edge cases handled?). "
  eval_prompt+="Be harsh and objective. Any criterion below 6 means overall FAIL. "
  eval_prompt+="After running tests and analyzing the code, respond with ONLY this JSON (no other text): "
  eval_prompt+='{\"scores\": {\"product_depth\": N, \"functionality\": N, \"code_quality\": N, \"test_coverage\": N}, '
  eval_prompt+='\"verdict\": \"PASS\", '
  eval_prompt+='\"bugs\": [], '
  eval_prompt+='\"justification\": \"one sentence per criterion\"}'
  eval_prompt+=" Replace N with integer scores 1-10. Replace PASS with FAIL if any score < 6."

  eval_output=$(cd "$WORKSPACE" && copilot -p "$eval_prompt" \
    -s --no-ask-user --model "$EVAL_MODEL" \
    --allow-tool='shell(*), read' --allow-all-paths 2>&1) || {
    err "Evaluator failed"
    echo "$eval_output" > "$EVALUATIONS_DIR/eval-raw${iteration_label:+-iter$iteration_label}.txt"
  }

  eval_end=$(date +%s)
  EVALUATOR_DURATION=$((EVALUATOR_DURATION + eval_end - eval_start))

  # Remove _eval/ from workspace immediately
  rm -rf "$WORKSPACE/_eval"

  # Save raw output
  echo "$eval_output" > "$EVALUATIONS_DIR/eval-raw${iteration_label:+-iter$iteration_label}.txt"
  log "Evaluator complete (${EVALUATOR_DURATION}s total)"

  # Parse JSON from evaluator output
  eval_json=$(extract_json "$eval_output")

  if echo "$eval_json" | jq . >/dev/null 2>&1; then
    echo "$eval_json" | jq . > "$EVALUATIONS_DIR/eval.json"
    VERDICT=$(echo "$eval_json" | jq -r '.verdict // "FAIL"')
    EVAL_SCORES=$(echo "$eval_json" | jq -c '.scores // {}')
    BUGS=$(echo "$eval_json" | jq -c '.bugs // []')
    log "Evaluator verdict: $VERDICT"
    log "Scores: $EVAL_SCORES"
  else
    err "Could not parse evaluator JSON output"
    echo '{"scores": {}, "verdict": "FAIL", "bugs": [], "justification": "Failed to parse evaluator output"}' > "$EVALUATIONS_DIR/eval.json"
    VERDICT="FAIL"
    EVAL_SCORES='{}'
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

log "Running visible tests..."
VISIBLE_TESTS=$(run_tests "$WORKSPACE" "tests")

log "Running hidden eval tests..."
# Copy _eval/ in, run, remove
cp -R "$EVAL_DIR" "$WORKSPACE/_eval" 2>/dev/null || true
EVAL_TESTS=$(run_tests "$WORKSPACE" "_eval")
rm -rf "$WORKSPACE/_eval"

# Build run manifest
jq -n \
  --arg run_id "$RUN_ID" \
  --arg benchmark "$BENCHMARK" \
  --arg mode "$MODE" \
  --arg model_id "$MODEL" \
  --arg eval_model_id "$EVAL_MODEL" \
  --argjson planner_duration "$PLANNER_DURATION" \
  --argjson generator_duration "$GENERATOR_DURATION" \
  --argjson evaluator_duration "$EVALUATOR_DURATION" \
  --argjson total_duration "$TOTAL_DURATION" \
  --argjson iterations "$ITERATIONS" \
  --argjson visible_tests "$VISIBLE_TESTS" \
  --argjson eval_tests "$EVAL_TESTS" \
  --argjson evaluator_scores "$EVAL_SCORES" \
  --arg verdict "$VERDICT" \
  --argjson bugs "$BUGS" \
  --arg timestamp "$TIMESTAMP" \
  '{
    run_id: $run_id,
    benchmark: $benchmark,
    mode: $mode,
    model: { provider: "copilot-cli", model_id: $model_id },
    eval_model: { provider: "copilot-cli", model_id: $eval_model_id },
    planner_duration_s: $planner_duration,
    generator_duration_s: $generator_duration,
    evaluator_duration_s: $evaluator_duration,
    total_duration_s: $total_duration,
    iterations: $iterations,
    visible_tests: $visible_tests,
    eval_tests: $eval_tests,
    evaluator_scores: $evaluator_scores,
    verdict: $verdict,
    bugs: $bugs,
    timestamp: $timestamp
  }' > "$TELEMETRY_DIR/run-manifest.json"

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
echo "  Visible tests: $(echo "$VISIBLE_TESTS" | jq -r '"\(.passed)/\(.total) passed"')"
echo "  Eval tests:    $(echo "$EVAL_TESTS" | jq -r '"\(.passed)/\(.total) passed"')"
echo "  Scores:       $EVAL_SCORES"
echo "  Verdict:      $VERDICT"
echo "=============================================="
