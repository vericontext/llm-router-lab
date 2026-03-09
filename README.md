# LLM Router Lab

Systematic testing and comparison of LLM routing solutions (OpenRouter, LiteLLM, OpenAI-compatible endpoints).

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in API keys
cp .env.example .env

# Run a benchmark
python scripts/run_benchmark.py --routers openrouter --models gpt-4o --scenarios basic_completion

# Compare results
python scripts/compare.py results/*.json --format table
```

## Project Structure

```
config/          # YAML configuration (routers, models, scenarios index)
src/llm_router_lab/
  providers/     # Router adapters (OpenRouter, LiteLLM, OpenAI-compat)
  scenarios/     # Scenario loader + built-in programmatic scenarios
  runner.py      # Async benchmark runner
  metrics.py     # Timing and usage measurement
  report.py      # Output formatting (table, CSV, markdown)
scenarios/       # YAML test scenario definitions
scripts/         # CLI entry points
results/         # Benchmark output (gitignored)
```

## Adding a New Router

1. **If it's OpenAI-compatible**: Just add an entry to `config/routers.yaml` and model mappings to `config/models.yaml`. No code needed.

2. **If it needs custom logic**: Create `src/llm_router_lab/providers/your_router.py`:
   - Subclass `RouterProvider` (or `OpenAICompatProvider` if mostly compatible)
   - Implement `complete()` and `stream()`
   - Register in `runner.py:PROVIDER_CLASSES`

## Adding a Scenario

Create a YAML file in `scenarios/`:

```yaml
name: my_scenario
description: What this tests

defaults:
  model: gpt-4o
  temperature: 0.7

cases:
  - name: test_case_1
    messages:
      - role: user
        content: "Your prompt here"
```

## Running Tests

```bash
uv run pytest tests/
```
