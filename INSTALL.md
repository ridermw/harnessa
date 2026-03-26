# Installing Harnessa

## Prerequisites
- [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli) installed and authenticated
- Works on macOS, Linux, and Windows (WSL)

## Option 1: Install as Copilot CLI Skill (Recommended)

### Per-Project (any repo)
Copy the skill into your project:

```bash
mkdir -p .github/copilot/skills/harnessa
curl -o .github/copilot/skills/harnessa/SKILL.md \
  https://raw.githubusercontent.com/ridermw/harnessa/main/.github/copilot/skills/harnessa/SKILL.md
```

Then in Copilot CLI:
```
/harnessa Fix the authentication bug in src/auth.ts
```

### Global (all repos)
Install to your personal Copilot skills directory:

```bash
mkdir -p ~/.copilot/skills/harnessa
curl -o ~/.copilot/skills/harnessa/SKILL.md \
  https://raw.githubusercontent.com/ridermw/harnessa/main/.github/copilot/skills/harnessa/SKILL.md
```

## Option 2: Use the Runner Scripts

For benchmark-style evaluation with telemetry:

```bash
git clone https://github.com/ridermw/harnessa.git
cd harnessa
pip install -e ".[dev]"

# Run a benchmark
bash scripts/run-benchmark.sh small-bugfix-python trio --model claude-sonnet-4

# Run all benchmarks
bash scripts/run-all-benchmarks.sh --model claude-sonnet-4 --runs 3
```

## Option 3: Create a Plan and Run

1. Create a `TASK.md` in your project root:
```markdown
# Task: [Description]
[What needs to be done. 1-4 sentences.]
```

2. Run the trio:
```bash
copilot -p '/harnessa Run the task in TASK.md' --allow-all
```

## Customizing Criteria

Copy and edit the criteria YAML for your domain:
```bash
curl -o criteria.yaml https://raw.githubusercontent.com/ridermw/harnessa/main/criteria/backend.yaml
# Edit criteria.yaml with your own thresholds and few-shot examples
```

## Verified Results

See [RESULTS.md](RESULTS.md) for experimental evidence that the trio pattern works:
- Solo FAIL → Trio PASS on fullstack features
- +2.8 avg functionality score improvement
- Evaluator catches real bugs that solo agents miss
