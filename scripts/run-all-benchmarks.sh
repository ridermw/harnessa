#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-all-benchmarks.sh — Run all Harnessa benchmarks in both modes
# =============================================================================
# Usage: ./scripts/run-all-benchmarks.sh --model <model> [options]
#
# Options:
#   --model <model>           Model to use (REQUIRED)
#   --eval-model <model>      Evaluator model (default: same as --model)
#   --runs <n>                Number of runs per benchmark+mode combo (default: 1)
#   --max-iterations <n>      Max evaluator retry loops for trio (default: 3)
#   --benchmarks <list>       Comma-separated list of benchmarks (default: all)
#   --modes <list>            Comma-separated list of modes (default: solo,trio)
#
# Examples:
#   ./scripts/run-all-benchmarks.sh --model claude-sonnet-4
#   ./scripts/run-all-benchmarks.sh --model claude-sonnet-4 --eval-model gpt-5.4 --runs 3
#   ./scripts/run-all-benchmarks.sh --model gpt-5.4 --benchmarks small-bugfix-python,small-feature-typescript
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$REPO_ROOT/scripts"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { echo "[harnessa] $(date '+%H:%M:%S') $*"; }
err()  { echo "[harnessa] ERROR: $*" >&2; }
die()  { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

MODEL=""
EVAL_MODEL=""
RUNS=1
MAX_ITERATIONS=3
BENCHMARKS=""
MODES="solo,trio"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)          MODEL="$2"; shift 2 ;;
    --eval-model)     EVAL_MODEL="$2"; shift 2 ;;
    --runs)           RUNS="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    --benchmarks)     BENCHMARKS="$2"; shift 2 ;;
    --modes)          MODES="$2"; shift 2 ;;
    -h|--help)        sed -n '2,/^# =====/p' "$0" | grep '^#' | sed 's/^# \?//'; exit 0 ;;
    *)                die "Unknown option: $1" ;;
  esac
done

[[ -z "$MODEL" ]] && die "--model is required"

# Discover benchmarks
if [[ -z "$BENCHMARKS" ]]; then
  BENCHMARKS=$(ls -1 "$REPO_ROOT/benchmarks/" | tr '\n' ',' | sed 's/,$//')
fi

# Split into arrays
IFS=',' read -ra BENCHMARK_LIST <<< "$BENCHMARKS"
IFS=',' read -ra MODE_LIST <<< "$MODES"

TOTAL_COMBOS=$(( ${#BENCHMARK_LIST[@]} * ${#MODE_LIST[@]} * RUNS ))

log "=============================================="
log "  HARNESSA BENCHMARK SUITE"
log "=============================================="
log "  Model:        $MODEL"
log "  Eval model:   ${EVAL_MODEL:-$MODEL}"
log "  Runs/combo:   $RUNS"
log "  Benchmarks:   ${BENCHMARK_LIST[*]}"
log "  Modes:        ${MODE_LIST[*]}"
log "  Total runs:   $TOTAL_COMBOS"
log "=============================================="
echo ""

# ---------------------------------------------------------------------------
# Run matrix
# ---------------------------------------------------------------------------

SUITE_START=$(date +%s)
COMPLETED=0
PASSED=0
FAILED=0
ERRORS=0

for benchmark in "${BENCHMARK_LIST[@]}"; do
  for mode in "${MODE_LIST[@]}"; do
    for run_num in $(seq 1 "$RUNS"); do
      COMPLETED=$((COMPLETED + 1))
      log "[$COMPLETED/$TOTAL_COMBOS] $benchmark / $mode (run $run_num/$RUNS)"

      EXTRA_ARGS=()
      [[ -n "$EVAL_MODEL" ]] && EXTRA_ARGS+=(--eval-model "$EVAL_MODEL")
      EXTRA_ARGS+=(--max-iterations "$MAX_ITERATIONS")

      if "$SCRIPT_DIR/run-benchmark.sh" "$benchmark" "$mode" --model "$MODEL" "${EXTRA_ARGS[@]}"; then
        PASSED=$((PASSED + 1))
      else
        exit_code=$?
        if [[ $exit_code -eq 1 ]]; then
          FAILED=$((FAILED + 1))
          err "$benchmark/$mode run $run_num failed"
        else
          ERRORS=$((ERRORS + 1))
          err "$benchmark/$mode run $run_num errored (exit $exit_code)"
        fi
      fi

      echo ""
    done
  done
done

SUITE_END=$(date +%s)
SUITE_DURATION=$((SUITE_END - SUITE_START))

# ---------------------------------------------------------------------------
# Suite summary
# ---------------------------------------------------------------------------

echo ""
log "=============================================="
log "  SUITE COMPLETE"
log "=============================================="
log "  Total runs:   $TOTAL_COMBOS"
log "  Completed:    $COMPLETED"
log "  Passed:       $PASSED"
log "  Failed:       $FAILED"
log "  Errors:       $ERRORS"
log "  Duration:     ${SUITE_DURATION}s"
log "=============================================="
echo ""

# Run analysis
if [[ -x "$SCRIPT_DIR/analyze-results.sh" ]]; then
  log "Running analysis..."
  "$SCRIPT_DIR/analyze-results.sh"
fi
