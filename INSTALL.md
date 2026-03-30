# Installing Harnessa

## Prerequisites

- **GitHub Copilot CLI** installed and authenticated
  - Check: `copilot --version` should print a version number
  - Check: `copilot` should start without authentication errors
  - Install: [GitHub Copilot CLI docs](https://docs.github.com/en/copilot/how-tos/copilot-cli)
- **Works on:** macOS, Linux, Windows (WSL or PowerShell)
- **No API keys required** — Harnessa runs through Copilot CLI, which handles model access

---

## Install

### Option A: Per-Project (recommended for teams)

Add the skill to your repository so every collaborator gets it automatically:

```bash
mkdir -p .github/copilot/skills/harnessa
curl -fsSL -o .github/copilot/skills/harnessa/SKILL.md \
  https://raw.githubusercontent.com/ridermw/harnessa/main/.github/copilot/skills/harnessa/SKILL.md
```

Commit it:
```bash
git add .github/copilot/skills/harnessa
git commit -m "Add /harnessa skill"
```

### Option B: Global (all repos)

Install to your personal Copilot skills directory — available in every repo:

```bash
# Find your Copilot config dir
COPILOT_DIR="${COPILOT_CONFIG_DIR:-$HOME/.copilot}"
mkdir -p "$COPILOT_DIR/skills/harnessa"
curl -fsSL -o "$COPILOT_DIR/skills/harnessa/SKILL.md" \
  https://raw.githubusercontent.com/ridermw/harnessa/main/.github/copilot/skills/harnessa/SKILL.md
```

### Option C: Clone the full repo

Get everything — skill, benchmarks, runner scripts, telemetry, and criteria:

```bash
git clone https://github.com/ridermw/harnessa.git
cd harnessa
pip install -e ".[dev]"
```

This gives you:
- The `/harnessa` skill (in `.github/copilot/skills/harnessa/`)
- 5 benchmarks for testing the trio pattern
- Runner scripts for automated benchmark evaluation
- Criteria YAML files for customization

---

## Verify Installation

```bash
# Should show harnessa in the skills list
copilot -p "What skills do you have?" -s
```

---

## Usage

### Interactive mode

```
copilot
> /harnessa Fix the memory leak in src/cache.ts
```

### One-shot mode

```bash
copilot -p '/harnessa Add input validation to the user registration endpoint' --allow-all
```

### With a TASK.md

```bash
cat > TASK.md << 'EOF'
# Task: Add rate limiting to the API

Implement rate limiting on all /api/* endpoints. Use a sliding window
algorithm. Return 429 Too Many Requests after 100 requests per minute
per IP.
EOF

copilot -p '/harnessa Run the task in TASK.md' --allow-all
```

### Running benchmarks (full repo only)

```bash
# Run a single benchmark
bash scripts/run-benchmark.sh small-bugfix-python trio --model claude-sonnet-4

# Run solo for comparison
bash scripts/run-benchmark.sh small-bugfix-python solo --model claude-sonnet-4

# Run all benchmarks
bash scripts/run-all-benchmarks.sh --model claude-sonnet-4 --runs 3
```

---

## Best Practices

### Writing good task prompts

| ✅ Good | ❌ Bad |
|---------|--------|
| "Fix the race condition in pool.go where concurrent Acquire() calls can exceed max pool size" | "Fix bugs" |
| "The /api/users endpoint returns 500 when email contains a + character" | "Fix the users endpoint" |
| "Add pagination to /api/users — 20 per page, cursor-based, don't change the response schema" | "Add pagination" |
| "Refactor auth to JWT. Must remain backward compatible with existing session tokens for 30 days" | "Refactor auth" |

**Tips:**
- Be specific about the problem and where it lives
- Include constraints: "Don't change the public API", "Must be backward compatible"
- For features: describe the user story, not the implementation
- For bugfixes: include reproduction steps if you have them

### When to use /harnessa vs solo

| Use the trio (✅) | Skip the trio (❌) |
|---|---|
| Features touching 3+ files | Single-line fixes |
| Bugfixes you can't easily reproduce | Formatting / linting changes |
| Refactors with backward compatibility requirements | Dependency updates |
| Anything where you'd want a code review | Documentation-only changes |
| Fullstack changes (frontend + backend + tests) | Renaming a variable |

**Why?** The trio adds ~2-3x overhead per iteration. For small tasks, a solo agent
gets it right on the first try. For medium/large tasks, the Evaluator catches real
bugs that solo agents miss — our benchmarks showed solo FAIL → trio PASS on
fullstack features, with +2.8 avg functionality score improvement.

### Getting better evaluator results

- **Have tests in your repo.** The Evaluator runs them — no tests means no functionality signal.
- **Keep the test suite fast** (<30s) so iteration cycles are quick.
- **Use specific test names** so the Evaluator knows what passed/failed.
- **Have a clear project structure** — the Planner surveys the codebase to understand conventions.

---

## Customizing Criteria

Download and edit the grading criteria for your domain:

```bash
# Backend API projects
curl -fsSL -o harnessa-criteria.yaml \
  https://raw.githubusercontent.com/ridermw/harnessa/main/criteria/backend.yaml

# Full-stack projects
curl -fsSL -o harnessa-criteria.yaml \
  https://raw.githubusercontent.com/ridermw/harnessa/main/criteria/fullstack.yaml
```

The criteria YAML defines 4 dimensions (product_depth, functionality, code_quality,
test_coverage) with thresholds, weights, and few-shot calibration examples.
Edit thresholds, add domain-specific criteria, or adjust the calibration examples
to match your team's standards.

> **Note:** The `/harnessa` skill has criteria text inline (since skills can't load
> external YAML at runtime). To change criteria for the skill, edit the "Grading
> Criteria" section in `SKILL.md` directly.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Skill not found" | Check path: `.github/copilot/skills/harnessa/SKILL.md` must exist. For global install, check `~/.copilot/skills/harnessa/SKILL.md`. |
| Evaluator too lenient | The anti-people-pleasing rules in SKILL.md address this. If still lenient, file an issue — evaluator calibration is ongoing. |
| Evaluator too harsh | Lower the thresholds in the "Grading Criteria" section of SKILL.md (e.g., product_depth threshold from 6 to 5). |
| Stuck in iteration loop | Max 3 iterations enforced by the skill. If hitting 3 every time, the task may need to be broken into smaller pieces. |
| Copilot CLI not authenticated | Run `copilot` interactively first to complete authentication. |
| Generator ignores spec | This is the context reset working as intended. If the spec is too vague, make the task prompt more specific. |
| JSON parse errors in eval | The skill writes structured JSON to `harnessa-eval.md`. If this fails, try running the skill again — LLM output can vary. |

---

## Uninstall

**Per-project:**
```bash
rm -rf .github/copilot/skills/harnessa
git add -A && git commit -m "Remove /harnessa skill"
```

**Global:**
```bash
rm -rf "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/skills/harnessa"
```

**Full repo:**
```bash
pip uninstall harnessa
# Then remove the cloned directory
```

---

## How It Works

Harnessa implements a GAN-inspired multi-agent pattern described in
[Anthropic's guide to long-running agents](https://www.anthropic.com/engineering/harness-design-long-running-apps).

The core insight: separating the code **generator** from the code **evaluator**
creates an adversarial dynamic that catches bugs a solo agent would miss. The
generator can't see what the evaluator will check, so it can't game the grading.
The evaluator doesn't know what the generator intended, so it grades what was
actually built.

Our [benchmark results](RESULTS.md) confirm the pattern works:
- Solo FAIL → Trio PASS on fullstack features
- +2.8 avg functionality score improvement
- Evaluator catches real bugs that solo agents miss
- The trio advantage is strongest on medium/large tasks (3+ files)

The planner's primary value is **structure, not scope expansion** — giving the
generator a roadmap dramatically improves first-attempt quality on complex tasks.
