# MimirBench

**Evaluating and interpreting strategic reasoning in language-model agents under uncertainty.**

[![CI](https://github.com/anannyenaik/MimirBench/actions/workflows/ci.yml/badge.svg)](https://github.com/anannyenaik/MimirBench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-pre--alpha-orange)

MimirBench is a reproducible evaluation harness for agents that must update
beliefs, estimate expected value, and respect constraints under uncertainty. It
pairs deterministic synthetic environments with deterministic graders, reference
solvers, configurable agent backends, response caching, structured result
writers, and honest reports.

> **Current stable review target: v0.2.0.** This is a synthetic-evals /
> research-engineering project, not a trading system. All real-model statistics are
> computed from saved artefacts; see [RELEASE_NOTES_v0.2.0.md](RELEASE_NOTES_v0.2.0.md).

**Documentation map:**
[BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) ·
[STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md) ·
[RESULTS.md](RESULTS.md) ·
[ROBUSTNESS.md](ROBUSTNESS.md) ·
[INTERPRETABILITY.md](INTERPRETABILITY.md) ·
[TRAINING.md](TRAINING.md) ·
[ARTIFACTS.md](ARTIFACTS.md) ·
[MODEL_CARD_medium.md](MODEL_CARD_medium.md) ·
[reports/INDEX.md](reports/INDEX.md)

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
[TRAINING.md](TRAINING.md)). The `tiny` config is a CPU smoke test; the `medium`
config is the model organism that actually learns the task and yields the causal
interpretability result:

```bash
# Tiny smoke artefact (fast, does not learn the task):
mimirbench generate-traces configs/train_small_transformer_bayes_tiny.yaml
mimirbench train-small-transformer configs/train_small_transformer_bayes_tiny.yaml

# Medium model organism (the headline checkpoint):
mimirbench train-small-transformer configs/train_small_transformer_bayes_medium.yaml
mimirbench eval-small-transformer configs/eval_small_transformer_bayes_medium.yaml
mimirbench inspect-training reports/training/small_transformer_bayes_medium
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
`reflective`, `tool`, and `small_transformer`. Supported API providers are:

- `openai`
- `anthropic`
- `gemini`
- `generic_http`

Local Hugging Face remains optional through `type: local`. Optional API/local
dependencies are imported lazily, so importing `mimirbench` does not require
`openai`, `anthropic`, `google-genai`, `torch`, or `transformers`. See
[MODELS.md](MODELS.md) and [TOOLS.md](TOOLS.md) for details.

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

MimirBench is pre-alpha, with deterministic synthetic environments, real-model
provider integrations, preliminary hosted-model artefacts, and a small synthetic
transformer/interp track now checked in:

- Six deterministic synthetic environment families are implemented:
  `bayesian_games`, `auctions`, `hidden_regimes`, `market_making`,
  `prediction_markets`, and `adversarial_risk`.
- Real-model provider support exists for OpenAI, Anthropic/Claude, Gemini,
  generic HTTP, and optional local Hugging Face models.
- Real-model leaderboard artefacts have been generated for OpenAI, Claude, and
  Gemini. Every row is classified by track (strict-512 / best-valid) or as a
  protocol/probe/diagnostic artefact — see [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md)
  and the classification table in [reports/INDEX.md](reports/INDEX.md). Bootstrap
  CIs over the saved sample are in
  [STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md).
- Strongest comparable OpenAI **strict-512** direct row: `gpt-5.4`.
- Strongest **best-valid** Claude direct row: Claude Sonnet 4.6 at
  `max_tokens=1536`.
- Strongest **best-valid** Gemini direct row: `gemini-3.1-pro-preview` with
  `thinking_level=low` (cache-backed retry; provider-load caveat).
- Gemini `gemini-3.5-flash` with `thinking_budget=0` is the strongest best-valid
  non-Pro Gemini row.
- Best-valid rows are not identical-decoding; cross-provider differences mix
  capability with each provider's documented protocol.
- Robustness probes exist for OpenAI `gpt-5.4`, Claude Sonnet 4.6, Gemini Flash,
  and Gemini Pro.
- OpenAI forced Bayesian tool-use was run as a diagnostic and gave negligible
  gain over direct answering with higher latency.
- Claude and Gemini forced-tool runs were deliberately skipped.
- Responses are parsed and repaired deterministically, with no LLM judge and no
  hidden chain-of-thought collection.
- A medium synthetic Bayesian/risk transformer is trained and analysed end to
  end (Stage 7/8): 321,455 parameters, 12,000 train / 2,000 val / 2,000 test
  traces. On 2,000 held-out tasks it reaches a posterior-bucket accuracy of about
  0.990, action accuracy 1.000, risk accuracy 1.000, and a mean posterior error
  of about 0.0162.
- Mechanistic interpretability on that checkpoint yields a narrow causal
  model-organism result: corruption flipped the action on 122/128 clean/corrupted
  pairs, layer-0 attention patching restored the correct action on 118/122 flipped
  pairs, layer-0 MLP patching restored 0/122, and layer-1 attention restored
  119/122. This is specific to the medium synthetic checkpoint and does not
  transfer to frontier models.
- The earlier tiny checkpoint is kept only as the original CPU smoke artefact
  (undertrained, near-zero/negative interpretability) — not as a current result.
- All results are preliminary, synthetic, direct-agent unless labelled otherwise,
  and not statistically conclusive.
- Main model comparisons use a single seed/schedule; the interpretability result
  uses one checkpoint/seed. Whole-site patching is complemented by
  position-resolved (token-group) patching and negative controls
  ([extended report](reports/interpretability/interp_bayes_medium_extended/EXTENDED_INTERPRETABILITY_REPORT.md)),
  but there is still no per-head or SAE-level circuit analysis, and findings are
  single-seed (123).
- Small-model interpretability findings do not transfer to frontier-model
  internals.
- This is not a trading bot, live trading system, market-beating claim, trading-
  usefulness claim, or solved AI-safety benchmark.

## Headline Findings

MimirBench surfaces environment-specific differences rather than a single
uniformly dominant model. Across 20 tasks per environment, stronger/newer models
did not dominate every environment. Protocol choices mattered: Claude Sonnet
required a larger output budget for clean JSON, and Gemini models required
explicit thinking/output settings. Robustness probes surfaced paraphrase and
risk-pressure sensitivity concentrated in market-making, auctions, and
prediction-market tasks.

In the trained medium synthetic transformer, patching attention activations from
clean into corrupted prompts restored the correct action on 118/122 flipped
pairs, providing a narrow causal model-organism result specific to that
checkpoint. These are synthetic, deterministic tasks; the comparisons are not
statistically conclusive, carry no trading-usefulness claim, and the
small-model interpretability does not transfer to frontier models.

## Where To Look

- Protocol & statistics: [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md),
  [STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md), and the generated
  [statistical validity table](reports/runs/leaderboard/statistical_validity_existing_artifacts.md)
- [RESULTS.md](RESULTS.md) · [reports/INDEX.md](reports/INDEX.md)
- [OpenAI model ladder comparison](reports/runs/leaderboard/openai_model_ladder_20env_comparison.md)
- [Claude model ladder comparison](reports/runs/leaderboard/claude_model_ladder_direct_20env_comparison.md)
- [Gemini model ladder comparison](reports/runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md)
- [Gemini robustness comparison](reports/runs/leaderboard/gemini_strongest_robustness_comparison.md)
- Interpretability: [INTERPRETABILITY.md](INTERPRETABILITY.md), the
  [extended report](reports/interpretability/interp_bayes_medium_extended/EXTENDED_INTERPRETABILITY_REPORT.md),
  and the [multi-seed status](reports/interpretability/interp_bayes_multiseed_summary.md)
- Artifacts & reproduction: [ARTIFACTS.md](ARTIFACTS.md),
  [MODEL_CARD_medium.md](MODEL_CARD_medium.md), [TRAINING.md](TRAINING.md)

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
   tool-use policies, tool-use audit logs, and cost/latency reporting.~~ Done -
   see [MODELS.md](MODELS.md) and [TOOLS.md](TOOLS.md).
2. ~~Stage 6: comparison runner, plots, model cards, report index, failure
   taxonomy, and paper-style results infrastructure.~~ Done.
3. ~~Stage 7: synthetic Bayesian traces, compact transformer training,
   checkpoint evaluation, plots, and model cards.~~ Done.
4. ~~Stage 8: mechanistic interpretability on the trained checkpoint - activation
   capture, linear probes, clean/corrupted activation patching, attention
   analysis, circuit configs, and interpretability reports.~~ Done - see
   [INTERPRETABILITY.md](INTERPRETABILITY.md). Findings describe one small
   synthetic model only; no frontier-model claim is made.
5. ~~Real-model provider phase: OpenAI, Claude, and Gemini direct leaderboard
   artefacts plus targeted robustness probes.~~ Done. Provider-specific protocol
   settings and caveats remain part of the reported result.
6. ~~Train a larger synthetic Bayesian/risk transformer and rerun
   interpretability to seek a causal model-organism result.~~ Done - the medium
   checkpoint (321,455 params) learns the task and yields a narrow causal
   patching result; see [INTERPRETABILITY.md](INTERPRETABILITY.md) and
   [RESULTS.md](RESULTS.md). The finding is specific to that synthetic
   checkpoint and makes no frontier-model claim.
7. Stage 9: a paper-style report consolidating evals, robustness, training, and
   interpretability, with polished figures, tables, and limitations.

## What This Is Not

- Not a trading bot.
- Not a claim to beat markets.
- Not a live trading system.
- Not a solved AI-safety benchmark.

All data is synthetic and seed-generated.

## License

MIT - see [LICENSE](LICENSE).
