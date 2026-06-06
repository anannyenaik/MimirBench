# Extended interpretability report: interp_bayes_medium_extended_seed_124

- Generated: 2026-06-06T20:22:38+00:00
- Checkpoint analysed: `reports/training/small_transformer_bayes_medium_seed_124/checkpoints/best.pt`
- Model: compact transformer encoder (2 layers, d_model=128, 4 heads)
- Counterfactual pairs: 128 (seed 124)

All experiments are local, deterministic, CPU-only; no model is downloaded and no API is called.

## Position-resolved (token-group) activation patching

Each sub-block site is patched **only at the positions of one token group**. The corruption changes only the evidence (observation) tokens, so the `prior` and `payoff_risk` groups are honest negative controls: restoring them should recover the decision far less than restoring `evidence`.

| Site | Group | Action recovery | Mean action causal effect | n flipped |
| --- | --- | ---: | ---: | ---: |
| blocks.0.attn_out | evidence | 0.009 | 0.007 | 117 |
| blocks.0.attn_out | prior | 0.017 | 0.013 | 117 |
| blocks.0.attn_out | payoff_risk | 0.026 | 0.023 | 117 |
| blocks.0.mlp_out | evidence | 0.000 | 0.000 | 117 |
| blocks.0.mlp_out | prior | 0.000 | 0.000 | 117 |
| blocks.0.mlp_out | payoff_risk | 0.000 | 0.000 | 117 |
| blocks.0.resid_post | evidence | 0.009 | 0.013 | 117 |
| blocks.0.resid_post | prior | 0.017 | 0.013 | 117 |
| blocks.0.resid_post | payoff_risk | 0.026 | 0.023 | 117 |
| blocks.1.attn_out | evidence | 0.000 | 0.001 | 117 |
| blocks.1.attn_out | prior | 0.000 | 0.004 | 117 |
| blocks.1.attn_out | payoff_risk | 0.017 | 0.018 | 117 |
| blocks.1.mlp_out | evidence | 0.000 | 0.000 | 117 |
| blocks.1.mlp_out | prior | 0.000 | 0.001 | 117 |
| blocks.1.mlp_out | payoff_risk | 0.000 | 0.003 | 117 |
| blocks.1.resid_post | evidence | 0.000 | 0.001 | 117 |
| blocks.1.resid_post | prior | 0.000 | 0.003 | 117 |
| blocks.1.resid_post | payoff_risk | 0.017 | 0.018 | 117 |

Recovery is computed over pairs whose action the corruption flipped. A high `evidence` recovery with low `prior` / `payoff_risk` recovery localises the causal evidence-to-decision signal to the evidence token positions.

## Mismatched-donor negative control

At `blocks.0.attn_out`, each flipped pair is patched with its own clean activation (matched) and with a clean activation from an unrelated same-length example (mismatched).

| Head | Matched recovery | Mismatched recovery | n flipped | n with donor |
| --- | ---: | ---: | ---: | ---: |
| action | 0.974 | 0.530 | 117 | 117 |
| posterior_bucket | 0.844 | 0.133 | 128 | 128 |

A matched recovery well above the mismatched recovery confirms the patch restores the *specific* clean computation, not a generic activation shift.

## Label-shuffle probe control

- Site / label: `blocks.1.mlp_out` / `action`
- Real probe test accuracy: `1.000`
- Shuffled-label probe test accuracy: `0.438`
- Majority baseline: `0.516`

A genuine signal collapses to ~baseline when labels are shuffled; a large real-minus-shuffled gap indicates the probe reads structure, not noise.

## Limitations and caveats

- One checkpoint, one seed, one narrow synthetic Bayesian/risk generator.
- Position-resolved patching is at the token-group level; it does not isolate individual heads or neurons, and uses no sparse autoencoder.
- Negative or near-zero results are reported as-is.
- These results characterise one small, fully synthetic Bayesian transformer. They are not evidence about frontier-model internals and must not be read that way.
