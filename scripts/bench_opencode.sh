#!/usr/bin/env zsh
# OpenCode real-world benchmark: measures end-to-end coding agent sessions
# Compares OpenAI Direct vs OpenRouter on identical tasks
#
# Usage: zsh scripts/bench_opencode.sh [repeats]
# Default: 3 repeats per config per task

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENCODE="$HOME/.opencode/bin/opencode"
RESULTS_DIR="$PROJECT_ROOT/results/opencode"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

REPEATS=${1:-3}

# Load environment variables
set -a
source "$PROJECT_ROOT/.env"
set +a

# Configs to compare
typeset -A CONFIGS
CONFIGS[direct]="$PROJECT_ROOT/opencode_direct.json"
CONFIGS[openrouter]="$PROJECT_ROOT/opencode_openrouter.json"

# Tasks: easy / medium / hard
TASK_NAMES=("type_hints" "find_bug" "refactor")
TASKS=(
  "Look at src/llm_router_lab/types.py and list all the classes defined in it. Do not modify any files."
  "Read scenarios/coding_agent.yaml and identify the SQL injection vulnerability in the code_review example. Explain the fix in 3 sentences. Do not modify any files."
  "Read src/llm_router_lab/providers/base.py and all provider implementations in src/llm_router_lab/providers/. Describe how you would add a new provider without changing existing code. Do not modify any files."
)

# CSV header
CSV="$RESULTS_DIR/bench_${TIMESTAMP}.csv"
echo "provider,task,run,wallclock_ms,tokens_input,tokens_output,cost,steps,session_id" > "$CSV"

echo "=== OpenCode Benchmark ==="
echo "Repeats: $REPEATS"
echo "Results: $CSV"
echo ""

for config_name in direct openrouter; do
  config_path="${CONFIGS[$config_name]}"
  echo "--- Provider: $config_name ---"

  for task_idx in {1..${#TASKS[@]}}; do
    task_name="${TASK_NAMES[$task_idx]}"
    task_prompt="${TASKS[$task_idx]}"

    for r in $(seq 1 "$REPEATS"); do
      echo -n "  $task_name [run $r/$REPEATS] ... "

      JSON_OUT="$RESULTS_DIR/${config_name}_${task_name}_run${r}_${TIMESTAMP}.jsonl"

      START_MS=$(python3 -c "import time; print(int(time.time()*1000))")

      OPENCODE_CONFIG="$config_path" "$OPENCODE" run \
        --format json \
        --title "bench_${config_name}_${task_name}_${r}" \
        "$task_prompt" > "$JSON_OUT" 2>/dev/null || true

      END_MS=$(python3 -c "import time; print(int(time.time()*1000))")
      ELAPSED=$((END_MS - START_MS))

      # Parse JSON output for metrics
      SESSION_ID=$(grep -o '"sessionID":"[^"]*"' "$JSON_OUT" | head -1 | cut -d'"' -f4)

      # Sum tokens from all step_finish events
      TOKENS_IN=$(grep '"type":"step-finish"' "$JSON_OUT" | \
        python3 -c "import sys,json; print(sum(json.loads(l)['part']['tokens']['input'] for l in sys.stdin if 'step-finish' in l))" 2>/dev/null || echo "0")
      TOKENS_OUT=$(grep '"type":"step-finish"' "$JSON_OUT" | \
        python3 -c "import sys,json; print(sum(json.loads(l)['part']['tokens']['output'] for l in sys.stdin if 'step-finish' in l))" 2>/dev/null || echo "0")
      COST=$(grep '"type":"step-finish"' "$JSON_OUT" | \
        python3 -c "import sys,json; print(sum(json.loads(l)['part']['cost'] for l in sys.stdin if 'step-finish' in l))" 2>/dev/null || echo "0")
      STEPS=$(grep -c '"type":"step-finish"' "$JSON_OUT" 2>/dev/null || echo "0")

      echo "${ELAPSED}ms | in:${TOKENS_IN} out:${TOKENS_OUT} | \$${COST} | ${STEPS} steps"
      echo "${config_name},${task_name},${r},${ELAPSED},${TOKENS_IN},${TOKENS_OUT},${COST},${STEPS},${SESSION_ID}" >> "$CSV"

      # Brief pause between runs
      sleep 2
    done
  done
  echo ""
done

echo "=== Summary ==="
echo ""
python3 << PYEOF
import csv
from collections import defaultdict

data = defaultdict(list)
with open("$CSV") as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row["provider"], row["task"])
        data[key].append({
            "wallclock": int(row["wallclock_ms"]),
            "tokens_in": int(row["tokens_input"]),
            "tokens_out": int(row["tokens_output"]),
            "cost": float(row["cost"]),
            "steps": int(row["steps"]),
        })

print(f"{'Provider':<12} {'Task':<14} {'Avg ms':>8} {'Min ms':>8} {'Max ms':>8} {'Avg In':>8} {'Avg Out':>8} {'Avg Cost':>10} {'Steps':>6}")
print("-" * 90)
for (provider, task), runs in sorted(data.items()):
    n = len(runs)
    avg_wall = sum(r["wallclock"] for r in runs) // n
    min_wall = min(r["wallclock"] for r in runs)
    max_wall = max(r["wallclock"] for r in runs)
    avg_in = sum(r["tokens_in"] for r in runs) // n
    avg_out = sum(r["tokens_out"] for r in runs) // n
    avg_cost = sum(r["cost"] for r in runs) / n
    avg_steps = sum(r["steps"] for r in runs) / n
    print(f"{provider:<12} {task:<14} {avg_wall:>8} {min_wall:>8} {max_wall:>8} {avg_in:>8} {avg_out:>8} {avg_cost:>10.6f} {avg_steps:>6.1f}")
PYEOF
echo ""
echo "Raw data: $CSV"
