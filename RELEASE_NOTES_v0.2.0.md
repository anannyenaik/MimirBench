# MimirBench v0.2.0

**Current stable review target.** This alpha-stage research release makes
MimirBench's real-model evidence honest and inspectable: an official benchmark
protocol, statistical validity over saved artefacts, replicated local-only
interpretability, and release/artifact hygiene. **No paid model API calls are made
by anything in this release**; all real-model statistics are computed from saved
artefacts.

## Highlights

- **Official benchmark protocol** ([BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md)):
  strict-512 and best-valid tracks, plus explicit classification of every saved
  row as clean, protocol-limited, provider-failed, rescue probe, smoke,
  diagnostic, or non-model.
- **Statistical validity** ([STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md)):
  seeded 95% bootstrap CIs and task-aligned paired deltas computed from saved
  `results.jsonl` only. No model is run.
- **Six-seed interpretability replication**: independently trained synthetic
  checkpoints for seeds 123-128 reproduce the attention-sub-block result and its
  negative controls.
- **Per-head and individual-token causal analysis**: projected head outputs are
  patchable and ablatable, and attention-site positions are patched one at a time
  before semantic aggregation.
- **Artifact inspectability**: [ARTIFACTS.md](ARTIFACTS.md) and
  [MODEL_CARD_medium.md](MODEL_CARD_medium.md) document release assets,
  gitignored weights, SHA256 checksums, and exact reproduction commands.

## Headline real-model rows

These are synthetic, pilot 20-tasks-per-environment rows from saved artefacts.
They do not establish broad provider superiority.

| Row | Track | Mean (95% CI) |
| --- | --- | --- |
| OpenAI `gpt-5.4` | strict-512 clean | 0.6630 [0.5997, 0.7203] |
| Gemini Flash (`thinking_budget=0`) | best-valid clean | 0.7454 [0.6965, 0.7936] |
| Claude Sonnet 4.6 (`max_tokens=1536`) | best-valid clean | 0.8567 [0.8173, 0.8930] |
| Gemini Pro Preview (`thinking_level=low`) | best-valid clean | 0.8545 [0.8178, 0.8884] |

Full classification and paired deltas:
[statistical_validity_existing_artifacts.md](reports/runs/leaderboard/statistical_validity_existing_artifacts.md).

## Replicated interpretability result

Seeds **123-128 all completed** on the same narrow synthetic Bayesian/risk model
organism setup:

- layer-0 attention mean action recovery: **0.964**;
- layer-0 MLP action recovery: **0.000 on every seed**;
- layer-1 attention mean action recovery: **0.989**;
- matched/mismatched donor action recovery: **0.964 / 0.496**;
- real/shuffled-label action-probe accuracy: **1.000 / 0.471**.

Per-head and individual-position analysis refines rather than overturns that
result. No head dominates consistently across seeds; the best mean single-head
action recovery is **0.141**, while the largest mean zero-ablation degradation is
**0.051 action accuracy** and **0.314 posterior-bucket accuracy**. Individual
token-position action recovery is effectively zero. The evidence-to-decision
computation is attention-mediated but distributed across heads and positions; the
evidence does **not** support a clean circuit claim.

Reports:
[multi-seed summary](reports/interpretability/interp_bayes_multiseed_summary.md) and
[per-head/token summary](reports/interpretability/interp_bayes_head_token_summary.md).

## Convenience release assets

The [v0.2.0 GitHub release](https://github.com/anannyenaik/MimirBench/releases/tag/v0.2.0)
includes the medium `best.pt` checkpoint and `vocab.json` as convenience assets.
The `.pt` checkpoint remains gitignored in the repository and is reproducible
from the committed config.

| Asset | SHA256 |
| --- | --- |
| `best.pt` | `3f273cfe70d94e42c0f1b0440b9a907203c6260e6e03e02eff6ad5f4eaa1c546` |
| `vocab.json` | `d7a994c5a616d4326250483528ff0cd06f933b05c41cf7d735f428d64ba2ecfa` |

## Caveats

- Synthetic deterministic tasks and a pilot model leaderboard.
- No trading claim or claim of trading usefulness.
- No broad provider-superiority claim.
- No frontier-model interpretability transfer.
- Per-head patching/ablation is not SAE- or neuron-level analysis.
