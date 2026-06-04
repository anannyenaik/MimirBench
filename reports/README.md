# Reports

Curated, human-readable outputs of MimirBench runs. Unlike the git-ignored raw
artifacts under `runs/`/`artifacts/`, everything here is **intentionally committed**
and **reproducible from a config + seed + model version**.

## Start here

- [`INDEX.md`](INDEX.md) — the main report navigator. It lists every committed
  baseline, robustness, comparison, leaderboard, interpretability, and training
  artefact with its path and headline number.
- [`../RESULTS.md`](../RESULTS.md) — the narrative results document with the
  full caveats. **Read generated reports together with the caveats there:** they
  are synthetic and preliminary.

## Contents

- [`INDEX.md`](INDEX.md) — generated index of all committed artefacts.
- [`model_cards/`](model_cards/) — one card per evaluated model/agent: setup,
  headline metrics, known limitations.
- [`runs/`](runs/) — committed run reports: reference/mock smoke tests, the
  deterministic tool baseline, real-model leaderboards (OpenAI, Claude, Gemini),
  robustness probes, and the small-transformer evaluations.
- [`training/`](training/) — small-transformer training artefacts (metrics,
  curves, model cards) for the tiny and medium model organisms.
- [`interpretability/`](interpretability/) — activation-patching, probe, and
  attention artefacts and figures for the tiny and medium checkpoints.
- [`failure_cases.md`](failure_cases.md) — curated, seeded examples of specific
  reasoning failures.

Standalone cross-provider comparison notes live under `runs/leaderboard/`, e.g.
[`runs/leaderboard/openai_model_ladder_20env_comparison.md`](runs/leaderboard/openai_model_ladder_20env_comparison.md),
[`runs/leaderboard/claude_model_ladder_direct_20env_comparison.md`](runs/leaderboard/claude_model_ladder_direct_20env_comparison.md),
and [`runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md`](runs/leaderboard/gemini_model_ladder_direct_20env_comparison.md).

## Rules

- **No fabricated numbers.** A report is added only when it is backed by a real run.
- **Always reproducible.** Every report names the environment, seed(s), `n_tasks`,
  agent, and model version so it can be regenerated.
- **Honest framing.** All committed results are synthetic and preliminary, not
  statistically conclusive, and carry no trading-usefulness claim. Interpretability
  results describe one small synthetic checkpoint and do not transfer to frontier
  models. Report limitations, not just point estimates.
