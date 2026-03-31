#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# run-cross-model.sh — Run cross-model evaluation on a single benchmark
# =============================================================================
# Usage: ./scripts/run-cross-model.sh <benchmark> [options]
#
# Options:
#   --gen-model <model>           Model for planner/generator and evaluator A (REQUIRED)
#   --eval-models <m1>            External evaluator model IDs (currently exactly 1, REQUIRED)
#   --max-iterations <n>          Max retry loops for trio mode (default: 3)
#   --mode <solo|trio>            Execution mode (default: trio)
#
# Examples:
#   ./scripts/run-cross-model.sh medium-feature-fullstack \
#     --gen-model claude-sonnet-4 \
#     --eval-models gpt-5.4
#
#   ./scripts/run-cross-model.sh small-bugfix-python \
#     --gen-model gpt-5.4 \
#     --eval-models claude-sonnet-4 --mode solo
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
  local exit_code="${1:-1}"
  cat <<'EOF'
run-cross-model.sh — Run cross-model evaluation on a single benchmark

Usage:
  ./scripts/run-cross-model.sh <benchmark> [options]

Options:
  --gen-model <model>           Model for planner/generator and evaluator A (required)
  --eval-models <m1>            External evaluator model IDs (currently exactly 1, required)
  --max-iterations <n>          Max retry loops for trio mode (default: 3)
  --mode <solo|trio>            Execution mode (default: trio)

Examples:
  ./scripts/run-cross-model.sh medium-feature-fullstack \
    --gen-model claude-sonnet-4 \
    --eval-models gpt-5.4

  ./scripts/run-cross-model.sh small-bugfix-python \
    --gen-model gpt-5.4 \
    --eval-models claude-sonnet-4 \
    --mode solo
EOF
  exit "$exit_code"
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

[[ $# -lt 1 ]] && usage 1

case "${1:-}" in
  -h|--help)
    usage 0
    ;;
esac

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
    -h|--help)         usage 0 ;;
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
for i in "${!MODELS[@]}"; do
  MODELS[$i]="$(echo "${MODELS[$i]}" | xargs)"
done
[[ ${#MODELS[@]} -ne 1 ]] && die \
  "Cross-model comparison currently supports exactly 1 external evaluator model. " \
  "The Python orchestrator uses the first evaluator model for planner/generator work " \
  "and only reconciles two evaluators total."

EXTERNAL_EVAL_MODEL="${MODELS[0]}"

log "Benchmark:      $BENCHMARK"
log "Mode:           $MODE"
log "Generator:      $GEN_MODEL"
log "External eval:  $EXTERNAL_EVAL_MODEL"
log "Max iterations: $MAX_ITERATIONS"

# ---------------------------------------------------------------------------
# Use Python CLI with --evaluator-models (required)
# ---------------------------------------------------------------------------

if command -v harnessa >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  log "Using Python CLI for cross-model evaluation..."

  HARNESSA_CMD="harnessa"
  if ! command -v harnessa >/dev/null 2>&1; then
    HARNESSA_CMD="python -m harnessa.cli"
  fi

  COMBINED_MODELS="$GEN_MODEL,$EXTERNAL_EVAL_MODEL"
  log "Planner/Generator model: $GEN_MODEL"
  log "Evaluator models:        $COMBINED_MODELS"

  $HARNESSA_CMD run "$BENCHMARK" \
    --mode "$MODE" \
    --evaluator-models "$COMBINED_MODELS" \
    --max-iterations "$MAX_ITERATIONS"

  exit $?
fi

die "Cross-model benchmarking requires the Python CLI path. Shell fallback is disabled because rerunning generation per evaluator would taint the comparison."
