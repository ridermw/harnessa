#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-cross-model.sh — Run cross-model evaluation on a single benchmark
# =============================================================================
# Usage: ./scripts/run-cross-model.sh <benchmark> [options]
#
# Options:
#   --gen-model <model>           Model for generator (REQUIRED)
#   --eval-models <m1,m2,...>     Comma-separated evaluator models (REQUIRED)
#   --max-iterations <n>          Max retry loops for trio mode (default: 3)
#   --mode <solo|trio>            Execution mode (default: trio)
#
# Examples:
#   ./scripts/run-cross-model.sh medium-feature-fullstack \
#     --gen-model claude-sonnet-4 \
#     --eval-models claude-sonnet-4,gpt-5.4,claude-opus-4.6
#
#   ./scripts/run-cross-model.sh small-bugfix-python \
#     --gen-model gpt-5.4 \
#     --eval-models gpt-5.4,claude-sonnet-4 --mode solo
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log()  { echo "[cross-model] $(date '+%H:%M:%S') $*"; }
err()  { echo "[cross-model] ERROR: $*" >&2; }
die()  { err "$@"; exit 1; }

usage() {
  sed -n '2,/^# =====/p' "$0" | grep '^#' | sed 's/^# \?//'
  exit 1
}

generate_uuid() {
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  else
    od -x /dev/urandom | head -1 | awk '{print $2$3"-"$4"-"$5"-"$6"-"$7$8$9}'
  fi
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

[[ $# -lt 1 ]] && usage

BENCHMARK="$1"; shift

GEN_MODEL=""
EVAL_MODELS=""
MAX_ITERATIONS=3
MODE="trio"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gen-model)       GEN_MODEL="$2"; shift 2 ;;
    --eval-models)     EVAL_MODELS="$2"; shift 2 ;;
    --max-iterations)  MAX_ITERATIONS="$2"; shift 2 ;;
    --mode)            MODE="$2"; shift 2 ;;
    -h|--help)         usage ;;
    *)                 die "Unknown option: $1" ;;
  esac
done

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

[[ -z "$GEN_MODEL" ]] && die "--gen-model is required"
[[ -z "$EVAL_MODELS" ]] && die "--eval-models is required (comma-separated)"

BENCHMARK_DIR="$REPO_ROOT/benchmarks/$BENCHMARK"
[[ -d "$BENCHMARK_DIR" ]] || die "Benchmark not found: $BENCHMARK_DIR"
[[ -f "$BENCHMARK_DIR/TASK.md" ]] || die "No TASK.md in $BENCHMARK_DIR"

# Split eval models into array
IFS=',' read -ra MODELS <<< "$EVAL_MODELS"
[[ ${#MODELS[@]} -lt 2 ]] && die "Need at least 2 eval models for cross-model comparison"

log "Benchmark:      $BENCHMARK"
log "Mode:           $MODE"
log "Generator:      $GEN_MODEL"
log "Eval models:    ${MODELS[*]}"
log "Max iterations: $MAX_ITERATIONS"

# ---------------------------------------------------------------------------
# Strategy 1: Use Python CLI with --evaluator-models (preferred)
# ---------------------------------------------------------------------------

if command -v harnessa >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  log "Using Python CLI for cross-model evaluation..."

  HARNESSA_CMD="harnessa"
  if ! command -v harnessa >/dev/null 2>&1; then
    HARNESSA_CMD="python -m harnessa.cli"
  fi

  $HARNESSA_CMD run "$BENCHMARK" \
    --mode "$MODE" \
    --evaluator-models "$EVAL_MODELS" \
    --max-iterations "$MAX_ITERATIONS"

  exit $?
fi

# ---------------------------------------------------------------------------
# Strategy 2: Shell-based — run each evaluator independently
# ---------------------------------------------------------------------------

log "Falling back to shell-based cross-model evaluation..."

RUN_ID="cross-$(generate_uuid | cut -c1-8)"
RESULTS_DIR="$REPO_ROOT/runs/$RUN_ID"
mkdir -p "$RESULTS_DIR"

# Step 1: Generate code once with gen-model
log "=== Step 1: Generate code ==="
GEN_RUN_ID="gen-$(generate_uuid | cut -c1-8)"

"$SCRIPT_DIR/run-benchmark.sh" "$BENCHMARK" "$MODE" \
  --model "$GEN_MODEL" \
  --eval-model "${MODELS[0]}" \
  --max-iterations "$MAX_ITERATIONS" \
  --run-id "$GEN_RUN_ID"

GEN_RUN_DIR="$REPO_ROOT/runs/$GEN_RUN_ID"

# Step 2: Run each evaluator against the same generated code
log "=== Step 2: Run evaluators ==="
declare -a EVAL_RUN_IDS=()

for i in "${!MODELS[@]}"; do
  model="${MODELS[$i]}"
  if [[ $i -eq 0 ]]; then
    # First evaluator already ran with the generator
    EVAL_RUN_IDS+=("$GEN_RUN_ID")
    log "  Evaluator $((i+1))/${#MODELS[@]}: $model (already run)"
    continue
  fi

  EVAL_RUN_ID="eval${i}-$(generate_uuid | cut -c1-8)"
  log "  Evaluator $((i+1))/${#MODELS[@]}: $model (run $EVAL_RUN_ID)"

  "$SCRIPT_DIR/run-benchmark.sh" "$BENCHMARK" "$MODE" \
    --model "$GEN_MODEL" \
    --eval-model "$model" \
    --max-iterations "$MAX_ITERATIONS" \
    --run-id "$EVAL_RUN_ID"

  EVAL_RUN_IDS+=("$EVAL_RUN_ID")
done

# Step 3: Compare scores
log "=== Step 3: Score Comparison ==="
echo ""
echo "=============================================="
echo "  CROSS-MODEL EVALUATION RESULTS"
echo "=============================================="
echo "  Benchmark:  $BENCHMARK"
echo "  Generator:  $GEN_MODEL"
echo "  Eval models: ${MODELS[*]}"
echo ""

# Print comparison table header
printf "  %-20s" "Criterion"
for model in "${MODELS[@]}"; do
  printf " | %-12s" "$model"
done
echo ""
printf "  %-20s" "--------------------"
for model in "${MODELS[@]}"; do
  printf " | %-12s" "------------"
done
echo ""

# Extract and compare scores from each run
CRITERIA=$(jq -r '.scores[]?.criterion' \
  "$REPO_ROOT/runs/${EVAL_RUN_IDS[0]}/telemetry/run-manifest.json" 2>/dev/null || true)

if [[ -n "$CRITERIA" ]]; then
  for criterion in $CRITERIA; do
    printf "  %-20s" "$criterion"
    for run_id in "${EVAL_RUN_IDS[@]}"; do
      score=$(jq -r --arg criterion "$criterion" '.scores[]? | select(.criterion == $criterion) | .score' \
        "$REPO_ROOT/runs/$run_id/telemetry/run-manifest.json" 2>/dev/null || echo "N/A")
      [[ -z "$score" ]] && score="N/A"
      printf " | %-12s" "$score"
    done
    echo ""
  done
fi

echo ""

# Print verdicts
printf "  %-20s" "Verdict"
for run_id in "${EVAL_RUN_IDS[@]}"; do
  verdict=$(jq -r '.verdict // "N/A"' \
    "$REPO_ROOT/runs/$run_id/telemetry/run-manifest.json" 2>/dev/null || echo "N/A")
  printf " | %-12s" "$verdict"
done
echo ""
echo "=============================================="

# Step 4: Write cross-model telemetry
CROSS_MANIFEST="$RESULTS_DIR/cross-model-results.json"
jq -n \
  --arg run_id "$RUN_ID" \
  --arg benchmark "$BENCHMARK" \
  --arg gen_model "$GEN_MODEL" \
  --arg eval_models "$EVAL_MODELS" \
  --argjson eval_run_ids "$(printf '%s\n' "${EVAL_RUN_IDS[@]}" | jq -R . | jq -s .)" \
  '{
    run_id: $run_id,
    benchmark: $benchmark,
    generator_model: $gen_model,
    evaluator_models: ($eval_models | split(",")),
    eval_run_ids: $eval_run_ids,
    type: "cross-model-comparison"
  }' > "$CROSS_MANIFEST"

log "Cross-model results written to $CROSS_MANIFEST"
log "Individual runs: ${EVAL_RUN_IDS[*]}"
