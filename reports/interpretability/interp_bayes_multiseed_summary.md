# Interpretability multi-seed summary

This note records exactly how many seeds of the medium model-organism
interpretability pipeline have **actually been run**, so every claim below is
backed by a completed run rather than an aspiration.

## Status

| Component | Seeds actually run | Status |
| --- | --- | --- |
| Medium checkpoint training | 123, 124, 125, 126, 127, 128 | **actually run** (6 independent checkpoints) |
| Whole-site interpretability (`interp_bayes_all_medium`) | 123, 124, 125, 126, 127, 128 | **actually run** (6 seeds) |
| Extended interpretability (`interp_bayes_medium_extended`) | 123, 124, 125, 126, 127, 128 | **actually run** (6 seeds) |
| Held-out test evaluation (fresh n=2000 draw) | 123, 124, 125, 126, 127, 128 | **actually run** (6 seeds) |

**Principal finding:** extended medium-model interpretability is now **replicated
across six independently trained synthetic checkpoints** (seeds 123–128). Each
seed independently resamples the training data, the weight initialisation, **and**
the interpretability probe/patch set, so these are genuinely independent draws,
not one dataset re-analysed. The evidence-to-decision mechanism remains
concentrated in attention-mediated activations on every seed; token-group-only
interventions show distributed positional dependence on every seed; and the
negative controls reduce recovery substantially on every seed.

All runs are local, deterministic, and CPU-only: **no API calls, no downloads**. The
aggregate machine record is
[`interp_bayes_multiseed_summary.json`](interp_bayes_multiseed_summary.json);
per-seed checkpoint hashes are in
[`interp_bayes_multiseed/checkpoints_sha256.txt`](interp_bayes_multiseed/checkpoints_sha256.txt).

## Architecture and dataset (identical across seeds)

- Compact transformer encoder: **2 layers, d_model 128, 4 heads, 321,455
  parameters**, dropout 0 (fully deterministic).
- Dataset sizes: **12,000 train / 2,000 val / 2,000 test** synthetic Bayesian
  traces per seed; `min_observations=2`, `max_observations=10`,
  `signal_reliability=0.75`, 20 posterior buckets, `risk_tolerance=0.35`.
- This is the *same* full setup as the original seed-123 medium model, not a
  reduced replication.

## Per-seed results

Held-out test accuracy is on a fresh, unseen n=2000 synthetic draw (distinct from
training/validation). "L0 attn", "L0 mlp", "L1 attn" are whole-site activation-
patching **action-recovery** rates over flipped counterfactual pairs.

| Seed | best epoch | held-out action / posterior / risk | L0 attn | L0 mlp | L1 attn | token-grp max | mismatch matched / mismatched (action) | label-shuffle real / shuffled | replicated |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | :---: |
| 123 | 25 | 1.000 / 0.993 / 1.000 | 0.967 | 0.000 | 0.975 | 0.016 | 0.967 / 0.533 | 1.000 / 0.484 | ✅ |
| 124 | 11 | 1.000 / 0.990 / 1.000 | 0.974 | 0.000 | 0.983 | 0.026 | 0.974 / 0.530 | 1.000 / 0.438 | ✅ |
| 125 | 21 | 1.000 / 0.990 / 1.000 | 0.984 | 0.000 | 0.992 | 0.000 | 0.984 / 0.556 | 1.000 / 0.375 | ✅ |
| 126 | 15 | 1.000 / 0.989 / 1.000 | 0.974 | 0.000 | 1.000 | 0.009 | 0.974 / 0.436 | 1.000 / 0.430 | ✅ |
| 127 | 21 | 1.000 / 0.991 / 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 / 0.451 | 1.000 / 0.539 | ✅ |
| 128 | 17 | 0.999 / 0.992 / 0.999 | 0.881 | 0.000 | 0.984 | 0.016 | 0.881 / 0.468 | 1.000 / 0.563 | ✅ |

## Aggregate across the 6 seeds (mean [min, max])

| Metric | Mean | Range |
| --- | ---: | --- |
| Held-out action accuracy | 1.000 | [0.9995, 1.000] |
| Held-out posterior-bucket accuracy | 0.991 | [0.989, 0.993] |
| Held-out risk-flag accuracy | 1.000 | [0.9995, 1.000] |
| Validation posterior-bucket accuracy | 0.991 | [0.987, 0.994] |
| **Layer-0 attention** action recovery | **0.964** | **[0.881, 1.000]** |
| **Layer-0 MLP** action recovery | **0.000** | **[0.000, 0.000]** |
| **Layer-1 attention** action recovery | **0.989** | **[0.975, 1.000]** |
| Layer-0 attention posterior recovery | 0.850 | [0.633, 0.938] |
| Token-group (single-group) max action recovery | 0.011 | [0.000, 0.026] |
| Mismatched-donor action recovery: matched | 0.964 | [0.881, 1.000] |
| Mismatched-donor action recovery: mismatched | 0.496 | [0.436, 0.556] |
| Mismatched-donor posterior recovery: matched | 0.850 | [0.633, 0.938] |
| Mismatched-donor posterior recovery: mismatched | 0.182 | [0.133, 0.234] |
| Label-shuffle probe: real labels | 1.000 | [1.000, 1.000] |
| Label-shuffle probe: shuffled labels | 0.471 | [0.375, 0.563] |

## Did the original causal story replicate? Yes: on all six seeds

Each seed independently passes all four pre-registered checks
(see `mimirbench/interpretability/multiseed.py` for the exact thresholds):

1. **Evidence→decision is concentrated in the attention sub-blocks.** On every
   seed the whole-site patch at layer-0 *attention* restores the clean action on
   0.88–1.00 of flipped pairs and layer-1 attention on 0.98–1.00, while the
   layer-0 *MLP* restores it on **exactly 0.000**, the cleanest part of the
   result and identical across all six checkpoints.
2. **Token-group-only interventions are distributed.** Patching a single token
   group's positions (evidence / prior / payoff-risk) of any one sub-block
   recovers the action on at most 2.6% of flipped pairs (mean 1.1%). The encoder
   mean-pools, so the signal is distributed across positions rather than localised
   to the evidence token positions. This is reported as a negative result, and it
   holds on every seed.
3. **The patch restores a *specific* computation (mismatched-donor control).** At
   `blocks.0.attn_out`, a matched donor recovers the action on 0.96 of flipped
   pairs (mean) but an unrelated same-length donor recovers only 0.50; for the
   posterior bucket the gap is 0.85 (matched) vs 0.18 (mismatched). The whole-site
   patch restores the clean computation, not a generic activation shift.
4. **The probe reads structure, not noise (label-shuffle control).** The action
   probe at `blocks.1.mlp_out` scores 1.000 on real labels on every seed and
   collapses to 0.38–0.56 (at or below the majority baseline) on shuffled labels.

The lower end of every attention range comes from seed 128 (layer-0 attention
action recovery 0.881, posterior recovery 0.633); it still clears every threshold
and reproduces the qualitative story. No seed failed and none was skipped.

## Reproducing

Local-only, CPU, no API calls:

```bash
mimirbench run-multiseed-interpretability configs/interp_bayes_medium_multiseed.yaml
```

The runner trains any missing per-seed checkpoint, runs whole-site + extended
interpretability and a held-out evaluation per seed, and rewrites
`interp_bayes_multiseed_summary.json`. `skip_existing: true` reuses the curated
seed-123 artefacts and lets the batch resume after an interruption. Heavy
regenerable artefacts (synthetic traces, activation dumps, per-row patching logs,
held-out eval rows) are gitignored; the per-seed summaries, patching summaries,
reports, and figures are kept.

## Scope and Limitations

- One narrow synthetic Bayesian/risk generator; deterministic, CPU-only. Six
  seeds establish seed-to-seed stability of *this* model organism, not generality
  across architectures or task families.
- Position-resolved patching is at the token-group level only; it does not isolate
  individual heads or neurons and uses no sparse autoencoder.
- Held-out and validation accuracies are near-ceiling by design (the generator is
  learnable); they show each checkpoint genuinely learned the task, which is what
  makes the causal localisation meaningful.
- Nothing here transfers to frontier-model internals and must not be read that way.
