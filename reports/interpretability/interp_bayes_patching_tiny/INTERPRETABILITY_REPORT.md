# Interpretability report: interp_bayes_patching_tiny

- Generated: 2026-06-02T17:16:15+00:00
- Checkpoint analysed: `reports/training/small_transformer_bayes_tiny/checkpoints/best.pt`
- Tokenizer/vocab: `reports/training/small_transformer_bayes_tiny/vocab.json`
- Model: compact transformer encoder (1 layer(s), d_model=32, 2 head(s))
- Dataset: 64 synthetic traces/split, 48 counterfactual pairs (seed 123)
- Experiments run: activation_patching

## What is analysed

Whether the small transformer's internal activations linearly encode the Bayesian posterior bucket, the action, the risk flag, and the confidence bucket (probes), and whether those activations are *causally* responsible for the decision (clean/corrupted activation patching). Attention analysis reports how attention mass is distributed across the prior, likelihood, evidence, and payoff/risk token groups.

## Activation patching results

- Counterfactual pairs: 48
- Best action-recovery site: n/a

| Site | Action causal effect | Action recovery | Label recovery |
| --- | ---: | ---: | ---: |
| embed | 0.000 | n/a | 1.000 |
| blocks.0.attn_out | -0.000 | n/a | 0.000 |
| blocks.0.mlp_out | 0.000 | n/a | 0.000 |
| blocks.0.resid_post | 0.000 | n/a | 1.000 |

`causal_effect = P(clean target | patched) - P(clean target | corrupted)`. Recovery rate is computed over pairs whose prediction the corruption flipped.

## What would count as causal evidence

- A patch at a specific site that consistently moves the corrupted prediction back to the clean decision (high recovery rate, positive causal effect concentrated at that site).
- A probe direction whose ablation degrades the matching decision.

## What would NOT count as causal evidence

- High probe accuracy alone (decodability is correlational, not causal).
- Causal effects within noise, or recovery rates near the flip rate.
- Any result here transferring to larger or frontier models.

## Limitations and caveats

- The model is tiny (see header), fully synthetic, and trained on a narrow Bayesian generator; mean pooling dilutes individual token effects.
- Probe/patching numbers are specific to this checkpoint and seed.
- Negative or near-zero results are reported as-is and are expected for an underpowered model organism.
- These results characterise one small, fully synthetic Bayesian transformer. They are not evidence about frontier-model internals and must not be read that way.
