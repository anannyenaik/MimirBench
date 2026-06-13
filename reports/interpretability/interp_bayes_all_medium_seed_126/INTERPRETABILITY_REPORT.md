# Interpretability report: interp_bayes_all_medium_seed_126

- Generated: 2026-06-06T21:14:35+00:00
- Checkpoint analysed: `reports/training/small_transformer_bayes_medium_seed_126/checkpoints/best.pt`
- Tokenizer/vocab: `reports/training/small_transformer_bayes_medium_seed_126/vocab.json`
- Model: compact transformer encoder (2 layer(s), d_model=128, 4 head(s))
- Dataset: 256 synthetic traces/split, 128 counterfactual pairs (seed 126)
- Experiments run: probes, activation_patching, attention_analysis

## What is analysed

Whether the small transformer's internal activations linearly encode the Bayesian posterior bucket, the action, the risk flag, and the confidence bucket (probes), and whether those activations are *causally* responsible for the decision (clean/corrupted activation patching). Attention analysis reports how attention mass is distributed across the prior, likelihood, evidence, and payoff/risk token groups.

## Probe results

| Label | Best site | Test acc | Baseline | Above baseline |
| --- | --- | ---: | ---: | ---: |
| posterior_bucket | blocks.1.mlp_out | 0.906 | 0.289 | +0.617 |
| action | blocks.1.attn_out | 1.000 | 0.562 | +0.438 |
| risk_flag | blocks.1.attn_out | 1.000 | 0.562 | +0.438 |
| confidence_bucket | blocks.1.mlp_out | 1.000 | 0.812 | +0.188 |

Accuracy above the majority-class baseline indicates linear decodability; it does not by itself establish that the model uses that information.

## Activation patching results

- Counterfactual pairs: 128
- Best action-recovery site: embed

| Site | Action causal effect | Action recovery | Label recovery |
| --- | ---: | ---: | ---: |
| embed | 0.914 | 1.000 | 1.000 |
| blocks.0.attn_out | 0.888 | 0.974 | 0.930 |
| blocks.0.mlp_out | -0.000 | 0.000 | 0.000 |
| blocks.0.resid_post | 0.914 | 1.000 | 1.000 |
| blocks.1.attn_out | 0.904 | 1.000 | 0.975 |
| blocks.1.mlp_out | 0.590 | 0.650 | 0.746 |
| blocks.1.resid_post | 0.914 | 1.000 | 1.000 |

`causal_effect = P(clean target | patched) - P(clean target | corrupted)`. Recovery rate is computed over pairs whose prediction the corruption flipped.

## Attention analysis results

- Examples analysed: 64

| Layer | Mean entropy | Prior mass | Evidence mass | Payoff/risk mass |
| --- | ---: | ---: | ---: | ---: |
| 0 | 2.552 | 0.157 | 0.356 | 0.210 |
| 1 | 3.246 | 0.201 | 0.134 | 0.216 |

## What would count as causal evidence

- A patch at a specific site that consistently moves the corrupted prediction back to the clean decision (high recovery rate, positive causal effect concentrated at that site).
- A probe direction whose ablation degrades the matching decision.

## Insufficient Evidence

- High probe accuracy alone (decodability is correlational, not causal).
- Causal effects within noise, or recovery rates near the flip rate.
- Any result here transferring to larger or frontier models.

## Scope and Limitations

- The model is tiny (see header), fully synthetic, and trained on a narrow Bayesian generator; mean pooling dilutes individual token effects.
- Probe/patching numbers are specific to this checkpoint and seed.
- Negative or near-zero results are reported as-is and are expected for an underpowered model organism.
- These results characterise one small, fully synthetic Bayesian transformer. They are not evidence about frontier-model internals and must not be read that way.
