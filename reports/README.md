# Reports

Curated, human-readable outputs of MimirBench runs. The committed reports are
reproducible from a config, seed, and model version; raw caches and large binary
artefacts remain gitignored.

## Start here

- [`INDEX.md`](INDEX.md): the main report navigator. It lists every committed
  baseline, robustness, comparison, leaderboard, interpretability, and training
  artefact with its path and headline number.
- [`../RESULTS.md`](../RESULTS.md): the narrative results document and its
  consolidated scope and limitations.

## Contents

- [`INDEX.md`](INDEX.md): generated index of all committed artefacts.
- [`model_cards/`](model_cards/): one card per evaluated model/agent: setup,
  headline metrics, known limitations.
- [`runs/`](runs/): committed run reports: reference/mock smoke tests, the
  deterministic tool baseline, hosted-model leaderboards (OpenAI, Claude, Gemini),
  robustness probes, and the small-transformer evaluations.
- [`training/`](training/): small-transformer training artefacts (metrics,
  curves, model cards) for the tiny and medium model organisms.
- [`interpretability/`](interpretability/): activation-patching, probe, and
  attention artefacts and figures for the tiny and medium checkpoints.
- [`failure_cases.md`](failure_cases.md): curated, seeded examples of specific
  reasoning failures.

Standalone cross-provider comparison notes live under `runs/leaderboard/`, e.g.
[`runs/leaderboard/openai_model_ladder_20env_comparison.md`](runs/leaderboard/openai_model_ladder_20env_comparison.md),
[`runs/leaderboard/claude_model_ladder_direct_20env_comparison.md`](runs/leaderboard/claude_model_ladder_direct_20env_comparison.md),
and [`runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md`](runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md).

## Rules

- **Artefact-backed evidence.** A report is added only when it is backed by a
  reproducible run.
- **Always reproducible.** Every report names the environment, seed(s), `n_tasks`,
  agent, and model version so it can be regenerated.
- **Explicit scope.** Hosted-model rows are pilot evaluations on a synthetic
  benchmark. Interpretability findings describe controlled synthetic model
  organisms. Each report states its limitations alongside its point estimates.
