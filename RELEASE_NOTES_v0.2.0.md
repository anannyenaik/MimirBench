# MimirBench v0.2.0

**Current stable review target.** This release makes MimirBench's real-model
evidence honest and inspectable: an official benchmark protocol, statistical
validity over saved artefacts, deepened local-only interpretability, and
release/artifact hygiene. **No paid API calls are made by anything in this
release** — all real-model statistics are computed from saved artefacts.

## Highlights

- **Official benchmark protocol** ([BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md)):
  two tracks — *strict-512* (identical-decoding) and *best-valid* (each provider's
  documented minimum-valid settings) — plus explicit rules classifying every saved
  row as clean / protocol-limited / provider-failed / rescue probe / smoke /
  diagnostic / non-model.
- **Statistical validity** ([STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md)):
  `mimirbench statistical-validity` computes seeded 95% bootstrap CIs (mean score,
  pass, parse-fail, risk-violation), task-aligned paired deltas, n, and latency from
  saved `results.jsonl` only, writing
  `reports/runs/leaderboard/statistical_validity_existing_artifacts.md`. **No model
  is run.**
- **Row reclassification**: curated track labels are emitted into
  [reports/INDEX.md](reports/INDEX.md), so protocol/probe artefacts are never read as
  capability.
- **Deepened interpretability** (local-only):
  `mimirbench run-extended-interpretability` adds position-resolved (token-group)
  patching, a mismatched-donor negative control, and a label-shuffle probe control
  on the medium checkpoint.
- **Artifact inspectability**: [ARTIFACTS.md](ARTIFACTS.md) and
  [MODEL_CARD_medium.md](MODEL_CARD_medium.md) document committed vs gitignored
  artefacts, SHA256 checksums, and exact reproduce commands.
- **Hygiene fix**: pytest no longer rewrites tracked `reports/model_cards/` files.

## Headline real-model rows (synthetic, 20/env, single seed)

| Row | Track | Mean (95% CI) |
| --- | --- | --- |
| OpenAI `gpt-5.4` | strict-512 clean | 0.6630 [0.5997, 0.7203] |
| Gemini Flash (`thinking_budget=0`) | best-valid clean | 0.7454 [0.6965, 0.7936] |
| Claude Sonnet 4.6 (`max_tokens=1536`) | best-valid clean | 0.8567 [0.8173, 0.8930] |
| Gemini Pro Preview (`thinking_level=low`) | best-valid clean | 0.8545 [0.8178, 0.8884] |

Protocol-limited rows (gpt-5.5 at default temp/512, Claude Sonnet at 512, Gemini
Flash default-thinking at 512) are retained as documented findings, not capability
scores. Full table and paired deltas:
[statistical_validity_existing_artifacts.md](reports/runs/leaderboard/statistical_validity_existing_artifacts.md).

## Interpretability result (single seed 123, synthetic model organism)

- Whole-site patching localises the causal evidence→decision signal to the
  **attention sub-blocks** (layer-0 attention restores the action on 118/122 flipped
  pairs; layer-0 MLP restores 0/122).
- Extended controls: matched whole-site patch recovers 0.967 of flipped actions vs
  0.533 for an unrelated donor; single token-group patches recover ≤2% (the signal
  is distributed across positions); the action probe scores 1.000 real vs 0.484
  shuffled. Single-seed only — see
  [reports/interpretability/interp_bayes_multiseed_summary.md](reports/interpretability/interp_bayes_multiseed_summary.md).

## Caveats

- Synthetic deterministic tasks; pilot 20/env, single seed/schedule; pilot CIs only.
- No trading claim, no broad provider-superiority claim, no statistical-significance
  claim, no frontier-model interpretability transfer.
- The medium checkpoint is gitignored; regenerate it deterministically (see
  [ARTIFACTS.md](ARTIFACTS.md)).

## Creating the release (run by a maintainer)

No GitHub release currently exists. To create v0.2.0 after validation passes:

```bash
git tag -a v0.2.0 -m "MimirBench v0.2.0"
git push origin v0.2.0
gh release create v0.2.0 --title "MimirBench v0.2.0" --notes-file RELEASE_NOTES_v0.2.0.md
```

Optionally attach the medium checkpoint as a release asset (see ARTIFACTS.md);
do not commit `.pt` weights to the tree.
