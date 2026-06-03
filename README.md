# MimirBench

**Evaluating and interpreting strategic reasoning in language-model agents under uncertainty.**

[![CI](https://github.com/your-org/mimirbench/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/mimirbench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-pre--alpha-orange)

MimirBench is a reproducible evaluation harness for agents that must update
beliefs, estimate expected value, and respect constraints under uncertainty. It
pairs deterministic synthetic environments with deterministic graders, reference
solvers, configurable agent backends, response caching, structured result
writers, and honest reports.

## Environments

| Family | Question it probes | Status |
| --- | --- | --- |
| `bayesian_games` | Posterior updating from a likelihood model | Implemented and registered |
| `auctions` | Expected-surplus reasoning in second-price auctions | Implemented and registered |
| `hidden_regimes` | Sequential belief filtering in a hidden Markov model | Implemented and registered |
| `market_making` | Toy quote decisions under inventory, loss, and adverse-selection constraints | Implemented and registered |
| `prediction_markets` | Binary markets separating belief, price, edge, and limits | Implemented and registered |
| `adversarial_risk` | Obeying hard risk limits under adversarial pressure | Implemented and registered |

Ground truth lives in `GradingKey`, while real agents receive only `Task`.
Reference solvers and explicitly diagnostic mock agents are the only components
allowed to use answers directly.

## Installation

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Optional extras are not needed for the core harness or tests:

```bash
pip install -e ".[ml]"       # torch + transformers
pip install -e ".[api]"      # openai-compatible API clients
pip install -e ".[interp]"   # transformer-lens tooling
pip install -e ".[all]"      # optional extras
```

## Quickstart

```bash
mimirbench list-envs
mimirbench validate-config configs/eval_mock_bayes.yaml
mimirbench run-eval configs/eval_reference_bayes.yaml
mimirbench run-eval configs/eval_reference_all_envs.yaml
mimirbench summarise-run reports/runs/all_envs_reference_smoke
mimirbench list-variant-types
mimirbench run-robustness configs/robustness_mock_all_envs.yaml
mimirbench summarise-robustness reports/runs/robustness_mock_all_envs
```

Stage 5 adds real-model and tool-agent commands (see [MODELS.md](MODELS.md) and
[TOOLS.md](TOOLS.md)):

```bash
mimirbench check-provider openai            # package/key check; never prints the key
mimirbench estimate-run-cost configs/eval_api_openai_bayes_smoke.yaml
mimirbench run-eval configs/eval_tool_reference_bayes.yaml   # deterministic tool baseline
mimirbench inspect-failures reports/runs/tool_reference_bayes
mimirbench inspect-tool-audit reports/runs/tool_reference_bayes
mimirbench run-leaderboard configs/leaderboard/leaderboard_all_available_tiny.yaml
mimirbench summarise-leaderboard reports/runs/leaderboard/leaderboard_all_available_tiny
# Real model runs require keys/weights and are never run by the test suite:
# mimirbench run-eval configs/eval_api_openai_bayes_smoke.yaml
# mimirbench run-leaderboard configs/leaderboard/leaderboard_all_available_tiny.yaml --allow-real-models
```

Stage 7 adds the synthetic small-transformer training pipeline (see
[TRAINING.md](TRAINING.md)):

```bash
mimirbench generate-traces configs/train_small_transformer_bayes_tiny.yaml
mimirbench train-small-transformer configs/train_small_transformer_bayes_tiny.yaml
mimirbench eval-small-transformer configs/eval_small_transformer_bayes.yaml
mimirbench inspect-training reports/training/small_transformer_bayes_tiny
```

Eval configs write these artefacts under the configured output directory:

- `results.jsonl` - one serialisable record per task
- `summary.json` - aggregate metrics and run metadata
- `report.md` - a human-readable report with explicit caveats

Robustness configs write:

- `robustness_results.jsonl` - base-vs-variant comparison records
- `robustness_summary.json` - robustness metrics and run metadata
- `robustness_report.md` - a human-readable robustness report
- `failure_cases.jsonl` / `failure_cases.md` - ranked diagnostic failures

Leaderboard configs write:

- `leaderboard_summary.json` - provider status, pending models, rows, paired metrics, and caveats
- `leaderboard_report.md` - score, robustness, risk, parse, cost, and latency table
- `headline_candidates.md` - deterministic candidate findings only when supported by saved artefacts
- `paired_deltas.jsonl` - direct/tool/reflective deltas aligned by environment, task ID, seed, and variant ID where applicable

In Python, the legacy single-environment API still works:

```python
from mimirbench import EvalConfig, run_eval

report = run_eval(EvalConfig(environment="bayesian_games", n_tasks=20, seed=0))
print(report.mean_score, report.pass_rate)
```

## Config-Driven Runs

Stage 2 YAML files use this shape:

```yaml
run:
  name: bayes_mock_smoke
  seed: 123
  output_dir: reports/runs/bayes_mock_smoke
  cache: true
  max_workers: 1

agent:
  type: mock
  behaviour: random_valid
  seed: 123

environments:
  - name: bayesian_games
    num_tasks: 100
    seed: 123

reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
```

Supported agent config types are `reference`, `mock`, `api`, `local`, `direct`,
`reflective`, `tool`, and `small_transformer`. The `api` type supports `openai`,
`anthropic`, and a generic OpenAI-compatible HTTP endpoint; the `tool` type
supports a deterministic `reference` policy and a model-backed `model` policy.
Optional API/local
dependencies are imported lazily, so importing `mimirbench` does not require
`openai`, `anthropic`, `torch`, or `transformers`. See [MODELS.md](MODELS.md) and
[TOOLS.md](TOOLS.md) for details.

## Adding a New Agent

Add or update `mimirbench/agents/resolver.py`, then provide a concrete
`BaseAgent` implementation. Keep optional dependencies lazy and do not pass
`GradingKey` to real agents. A config-driven API agent looks like:

```yaml
agent:
  type: api
  provider: openai
  model: gpt-4.1-mini
  temperature: 0
  max_retries: 3
```

Local models use `type: local` and `model_name: ...`. Diagnostic baselines that
use answers must be labelled as reference or mock baselines, never model runs.

## Current Status

MimirBench is pre-alpha, but the Stage 7 synthetic training pipeline is now in place:

- Six deterministic environment families are registered and runnable:
  `bayesian_games`, `auctions`, `hidden_regimes`, `market_making`,
  `prediction_markets`, and `adversarial_risk`.
- Agent resolution supports reference, mock, API (OpenAI / Anthropic / generic
  HTTP), local (Hugging Face), direct, reflective, tool, and small-transformer
  agents.
- A provider-agnostic `ModelClient` interface backs real models with bounded
  retries, timeouts, token usage, and optional cost estimation; provider SDKs are
  lazy and never required for the core harness or tests.
- Responses are parsed and repaired deterministically (no LLM judge), with parse
  errors recorded rather than raised.
- A safe tool-using agent runs a bounded act/observe loop over deterministic,
  sandboxed tools with per-environment allow-lists and full audit logs.
- Runs report token usage, cost (only when pricing is configured), and latency
  percentiles alongside parse/invalid/timeout/provider-error rates.
- Robustness evaluation, structured records, caching, and report writers remain
  first-class.
- Stage 6 comparison plots, model cards, report index generation, and failure
  taxonomy infrastructure are implemented.
- Stage 7 synthetic Bayesian trace generation, tokenizer, compact transformer,
  checkpoint training/evaluation, plots, and model cards are implemented. Torch
  remains optional for ordinary imports.
- The real-model leaderboard pipeline is implemented with provider checks,
  tiny configs, paired direct/tool/reflective comparisons, pending summaries,
  and evidence-gated headline candidates.
- `ruff`, `mypy`, and `pytest` pass without optional model dependencies.

There are no real model benchmark results yet. The checked-in reports under
`reports/runs/` are reference-solver, mock-baseline, and deterministic
tool-reference sanity checks generated by the harness - not model runs. Real
leaderboard rows remain pending unless providers are usable and execution is
explicitly permitted with `--allow-real-models`. See
[RESULTS.md](RESULTS.md) for exact numbers and caveats, [MODELS.md](MODELS.md) and
[TOOLS.md](TOOLS.md) for real-model and tool usage, and
[ROBUSTNESS.md](ROBUSTNESS.md) for the robustness methodology. See
[TRAINING.md](TRAINING.md) for the small synthetic transformer workflow.

## Avoiding Overclaiming

- Label every run as `reference solver`, `deterministic baseline`,
  `local stub/mock baseline`, or `real model run`.
- Do not report GPT, Claude, Gemini, or other model numbers unless credentials or
  weights were supplied and artefacts were actually generated.
- Reference scores are sanity checks for generation and grading, not model scores.
- Mock baselines test scoring sensitivity and parser behavior, not intelligence.
- MimirBench never asks for hidden chain-of-thought; records store concise
  reasoning summaries and structured answers only.

## Roadmap

1. ~~Stage 5: real API/local model integration, response parsing/repair, safe
   tool-use policies, tool-use audit logs, and cost/latency reporting.~~ Done —
   see [MODELS.md](MODELS.md) and [TOOLS.md](TOOLS.md).
2. ~~Stage 6: comparison runner, plots, model cards, report index, failure
   taxonomy, and paper-style results infrastructure.~~ Done.
3. ~~Stage 7: synthetic Bayesian traces, compact transformer training,
   checkpoint evaluation, plots, and model cards.~~ Done.
4. ~~Stage 8: mechanistic interpretability on the trained checkpoint — activation
   capture, linear probes, clean/corrupted activation patching, attention
   analysis, circuit configs, and interpretability reports.~~ Done — see
   [INTERPRETABILITY.md](INTERPRETABILITY.md). Findings describe one small
   synthetic model only; no frontier-model claim is made.
5. Stage 9: a paper-style report consolidating evals, robustness, training, and
   interpretability, with polished figures, tables, and limitations.

## What This Is Not

- Not a trading bot.
- Not a claim to beat markets.
- Not a live trading system.
- Not a solved AI-safety benchmark.

All data is synthetic and seed-generated.

## License

MIT - see [LICENSE](LICENSE).
