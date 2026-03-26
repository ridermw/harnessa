#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# analyze-results.sh — Analyze Harnessa benchmark results
# =============================================================================
# Reads all run-manifest.json files from runs/ and produces a summary table.
# Usage: ./scripts/analyze-results.sh [--json] [--filter-benchmark <name>] [--filter-model <model>]
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNS_DIR="$REPO_ROOT/runs"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

die() { echo "ERROR: $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command '$1' not found."
}

require_cmd jq

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

OUTPUT_JSON=false
FILTER_BENCHMARK=""
FILTER_MODEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)             OUTPUT_JSON=true; shift ;;
    --filter-benchmark) FILTER_BENCHMARK="$2"; shift 2 ;;
    --filter-model)     FILTER_MODEL="$2"; shift 2 ;;
    -h|--help)          sed -n '2,/^# =====/p' "$0" | grep '^#' | sed 's/^# \?//'; exit 0 ;;
    *)                  die "Unknown option: $1" ;;
  esac
done

# ---------------------------------------------------------------------------
# Collect all manifests
# ---------------------------------------------------------------------------

MANIFESTS=()
while IFS= read -r -d '' manifest; do
  MANIFESTS+=("$manifest")
done < <(find "$RUNS_DIR" -name 'run-manifest.json' -print0 2>/dev/null)

if [[ ${#MANIFESTS[@]} -eq 0 ]]; then
  echo "No run-manifest.json files found in $RUNS_DIR"
  exit 0
fi

echo "Found ${#MANIFESTS[@]} run(s)"
echo ""

# ---------------------------------------------------------------------------
# Build aggregated JSON array
# ---------------------------------------------------------------------------

ALL_RUNS="[]"
for manifest in "${MANIFESTS[@]}"; do
  run=$(jq '.' "$manifest" 2>/dev/null) || continue

  # Apply filters
  if [[ -n "$FILTER_BENCHMARK" ]]; then
    bm=$(echo "$run" | jq -r '.benchmark')
    [[ "$bm" != "$FILTER_BENCHMARK" ]] && continue
  fi
  if [[ -n "$FILTER_MODEL" ]]; then
    model=$(echo "$run" | jq -r '.model.model_id')
    [[ "$model" != "$FILTER_MODEL" ]] && continue
  fi

  ALL_RUNS=$(echo "$ALL_RUNS" | jq --argjson run "$run" '. + [$run]')
done

NUM_RUNS=$(echo "$ALL_RUNS" | jq 'length')

if [[ "$NUM_RUNS" -eq 0 ]]; then
  echo "No matching runs found."
  exit 0
fi

# ---------------------------------------------------------------------------
# JSON output mode
# ---------------------------------------------------------------------------

if [[ "$OUTPUT_JSON" == true ]]; then
  echo "$ALL_RUNS" | jq '.'
  exit 0
fi

# ---------------------------------------------------------------------------
# Aggregate by benchmark + mode
# ---------------------------------------------------------------------------

# Get unique benchmark/mode combos
COMBOS=$(echo "$ALL_RUNS" | jq -r '[.[] | {benchmark, mode}] | unique | .[] | "\(.benchmark)|\(.mode)"')

echo "# Harnessa Benchmark Results"
echo ""
echo "| Benchmark | Mode | Model | Runs | Avg Score | Test Pass Rate | Eval Pass Rate | Avg Duration | Verdict |"
echo "|-----------|------|-------|------|-----------|----------------|----------------|--------------|---------|"

while IFS='|' read -r benchmark mode; do
  [[ -z "$benchmark" ]] && continue

  # Filter runs for this combo
  COMBO_RUNS=$(echo "$ALL_RUNS" | jq --arg b "$benchmark" --arg m "$mode" \
    '[.[] | select(.benchmark == $b and .mode == $m)]')

  run_count=$(echo "$COMBO_RUNS" | jq 'length')
  [[ "$run_count" -eq 0 ]] && continue

  model_id=$(echo "$COMBO_RUNS" | jq -r '.[0].model.model_id')

  # Average score (mean of all 4 criteria across all runs)
  avg_score=$(echo "$COMBO_RUNS" | jq '
    [.[] | .evaluator_scores | to_entries | .[].value // 0] |
    if length > 0 then (add / length * 10 | round / 10) else 0 end
  ')

  # Visible test pass rate
  visible_pass_rate=$(echo "$COMBO_RUNS" | jq '
    [.[] | .visible_tests] |
    if [.[].total] | add > 0
    then (([.[].passed] | add) / ([.[].total] | add) * 100 | round)
    else 0 end
  ')

  # Eval test pass rate
  eval_pass_rate=$(echo "$COMBO_RUNS" | jq '
    [.[] | .eval_tests] |
    if [.[].total] | add > 0
    then (([.[].passed] | add) / ([.[].total] | add) * 100 | round)
    else 0 end
  ')

  # Average duration
  avg_duration=$(echo "$COMBO_RUNS" | jq '
    [.[].total_duration_s] | add / length | round
  ')

  # Verdict: PASS if majority pass
  pass_count=$(echo "$COMBO_RUNS" | jq '[.[] | select(.verdict == "PASS")] | length')
  if [[ "$pass_count" -gt $((run_count / 2)) ]]; then
    verdict="✅ PASS ($pass_count/$run_count)"
  else
    verdict="❌ FAIL ($pass_count/$run_count)"
  fi

  printf "| %-30s | %-4s | %-20s | %4s | %9s | %13s%% | %13s%% | %10ss | %s |\n" \
    "$benchmark" "$mode" "$model_id" "$run_count" "$avg_score" "$visible_pass_rate" "$eval_pass_rate" "$avg_duration" "$verdict"

done <<< "$COMBOS"

echo ""

# ---------------------------------------------------------------------------
# Overall summary
# ---------------------------------------------------------------------------

total_pass=$(echo "$ALL_RUNS" | jq '[.[] | select(.verdict == "PASS")] | length')
total_fail=$(echo "$ALL_RUNS" | jq '[.[] | select(.verdict != "PASS")] | length')
overall_avg=$(echo "$ALL_RUNS" | jq '
  [.[] | .evaluator_scores | to_entries | .[].value // 0] |
  if length > 0 then (add / length * 10 | round / 10) else 0 end
')
total_duration=$(echo "$ALL_RUNS" | jq '[.[].total_duration_s] | add')

echo "**Overall:** $total_pass passed, $total_fail failed out of $NUM_RUNS runs"
echo "**Average score:** $overall_avg/10"
echo "**Total wall time:** ${total_duration}s"
