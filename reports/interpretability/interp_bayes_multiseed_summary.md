# Interpretability multi-seed summary

This note records exactly how many seeds of the medium model-organism
interpretability pipeline have **actually been run**, so no claim of "across five
seeds" is made unless five runs completed.

## Status

| Component | Seed(s) actually run | Status |
| --- | --- | --- |
| Medium checkpoint training | 123 | **actually run** (one checkpoint/seed) |
| Stage 8 interpretability (`interp_bayes_all_medium`) | 123 | **actually run** (single-seed only) |
| Extended interpretability (`interp_bayes_medium_extended`) | 123 | **actually run** (single-seed only) |
| Multi-seed replication (seeds 124–128) | — | **reproducibility-ready, not executed** |

**Headline honesty:** every interpretability number in this repository comes from
**one checkpoint and one seed (123)**. The results are single-seed only. They are
not "across five seeds", not multi-seed replicated, and not pending due to a
missing checkpoint — the checkpoint exists locally and the single seed genuinely
ran.

## What single-seed run produced

- The medium checkpoint (321,455 params, 2 layers, d_model=128, 4 heads) reaches
  ~0.990 held-out posterior-bucket accuracy and 1.000 action/risk accuracy.
- Whole-site activation patching (`reports/interpretability/interp_bayes_all_medium/`)
  localises the causal evidence-to-decision signal to the **attention sub-blocks**
  (layer-0 attention restores the clean action on 118/122 flipped pairs; layer-0
  MLP restores 0/122).
- Extended, position-resolved analysis
  (`reports/interpretability/interp_bayes_medium_extended/`) adds three controls:
  - **Token-group patching:** patching a *single* token group's positions
    (evidence / prior / payoff-risk) of any one sub-block recovers the action on
    ≤2% of flipped pairs. The evidence→decision signal is therefore *distributed*
    across positions (the encoder mean-pools), not localised to the evidence
    token positions — reported as an honest negative result.
  - **Mismatched-donor control:** at `blocks.0.attn_out`, a matched whole-site
    patch recovers the action on 0.967 of flipped pairs, while a clean donor from
    an unrelated same-length example recovers only 0.533 (posterior bucket: 0.906
    matched vs 0.211 mismatched). The whole-site patch restores the *specific*
    clean computation, not a generic activation shift.
  - **Label-shuffle probe control:** the action probe at `blocks.1.mlp_out` scores
    1.000 on real labels and 0.484 (below the 0.594 majority baseline) on shuffled
    labels, confirming the probe reads genuine structure rather than noise.

## Reproducing additional seeds (not executed here)

The multi-seed configuration is reproducibility-ready. To replicate across five
seeds locally (CPU-only, no API calls), for each `SEED` in `123 124 125 126 127`:

1. Copy `configs/train_small_transformer_bayes_medium.yaml`, set both `run.seed`
   and `data.seed` to `SEED` and `run.output_dir` to a per-seed directory, then
   `mimirbench train-small-transformer <that-config>`.
2. Copy `configs/interp_bayes_medium_extended.yaml`, point `model.checkpoint_path`
   / `model.vocab_path` at the per-seed checkpoint and `run.output_dir` at a
   per-seed output, then `mimirbench run-extended-interpretability <that-config>`.
3. Aggregate the per-seed `summary.json` files and update the table above with the
   mean ± standard deviation across the seeds that actually completed.

Seeds 124–128 were **not** run in this session because training five medium
checkpoints on CPU exceeds the local compute budget. Until they are run, treat all
interpretability findings as single-seed.

## Caveats

- One narrow synthetic Bayesian/risk generator; deterministic, CPU-only.
- Position-resolved patching is at the token-group level only; it does not isolate
  individual heads or neurons and uses no sparse autoencoder.
- Nothing here transfers to frontier-model internals and must not be read that way.
