# Interpretability report: interp_bayes_all_tiny

- Generated: 2026-06-02T17:16:22+00:00
- Checkpoint analysed: `reports/training/small_transformer_bayes_tiny/checkpoints/best.pt`
- Tokenizer/vocab: `reports/training/small_transformer_bayes_tiny/vocab.json`
- Model: compact transformer encoder (1 layer(s), d_model=32, 2 head(s))
- Dataset: 96 synthetic traces/split, 48 counterfactual pairs (seed 123)
- Experiments run: probes, activation_patching, attention_analysis

## What is analysed

Whether the small transformer's internal activations linearly encode the Bayesian posterior bucket, the action, the risk flag, and the confidence bucket (probes), and whether those activations are *causally* responsible for the decision (clean/corrupted activation patching). Attention analysis reports how attention mass is distributed across the prior, likelihood, evidence, and payoff/risk token groups.

## Probe results

| Label | Best site | Test acc | Baseline | Above baseline |
| --- | --- | ---: | ---: | ---: |
| posterior_bucket | embed | 0.229 | 0.146 | +0.083 |
| action | blocks.0.attn_out | 0.917 | 0.750 | +0.167 |
| risk_flag | blocks.0.attn_out | 0.917 | 0.750 | +0.167 |
| confidence_bucket | embed | 0.479 | 0.479 | +0.000 |

Accuracy above the majority-class baseline indicates linear decodability; it does not by itself establish that the model uses that information.

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

## Attention analysis results

- Examples analysed: 48

| Layer | Mean entropy | Prior mass | Evidence mass | Payoff/risk mass |
| --- | ---: | ---: | ---: | ---: |
| 0 | 3.584 | 0.179 | 0.100 | 0.255 |

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
