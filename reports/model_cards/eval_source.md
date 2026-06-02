# Model card: eval_source

## Identity

- Model name: `eval_source`
- Model type: compact synthetic Bayesian trace transformer
- Training run directory: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\training`
- Created from actual training artefacts: `yes`

## Architecture

- Architecture: `compact_transformer_encoder`
- Parameter count: `6683`
- Target heads: `posterior_bucket, action, ev_bucket, risk_flag, confidence_bucket, rationale_class`
- Model config: `{"d_model": 16, "dim_feedforward": 32, "dropout": 0.0, "lm_loss_weight": 0.0, "max_seq_len": 96, "n_heads": 2, "n_layers": 1, "num_actions": 2, "num_confidence_buckets": 3, "num_ev_buckets": 7, "num_posterior_buckets": 20, "num_rationale_classes": 4, "num_risk_flags": 2, "pad_token_id": 0, "vocab_size": 69}`

## Training Data

- Data source: deterministic synthetic Bayesian traces generated inside MimirBench
- Synthetic traces: train=`8`, val=`4`, test=`4`
- Data config: `{"max_observations": 6, "min_observations": 1, "num_hypotheses": 2, "num_test": 4, "num_train": 8, "num_val": 4, "payoff": {"decision_cost": 0.0, "loss_if_not_A": 1.0, "reward_if_A": 1.0, "risk_tolerance": 0.35}, "posterior_buckets": 20, "seed": 2, "signal_reliability": 0.7}`
- Stored targets are final labels and concise rationale classes only; hidden chain-of-thought is not generated or stored.

## Training Config

- Optimisation config: `{"batch_size": 4, "device": "cpu", "early_stopping_patience": null, "epochs": 1, "grad_clip": 1.0, "learning_rate": 0.001, "weight_decay": 0.01}`
- Full resolved config: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\training\config_resolved.yaml`

## Validation Metrics

- Best epoch: `1`
- Best validation metrics: `{"epoch": 1, "train_loss": 8.851172924041748, "val_action_accuracy": 0.75, "val_confidence_bucket_accuracy": 0.25, "val_ev_bucket_accuracy": 0.0, "val_loss": 8.543505668640137, "val_posterior_bucket_accuracy": 0.0, "val_rationale_class_accuracy": 0.5, "val_risk_flag_accuracy": 0.75}`

## Held-Out MimirBench Metrics

- Held-out evaluation summary: `{"action_accuracy": 0.5, "approx_posterior_abs_error_mean": 0.3907249880901354, "confidence_bucket_accuracy": 0.75, "invalid_response_rate": 0.0, "latency_mean_ms": 85.72639999329112, "latency_p50_ms": 87.4149499941268, "latency_p95_ms": 101.09588999621337, "posterior_bucket_accuracy": 0.0, "regret_mean": 0.3111261872455902, "risk_flag_accuracy": 0.5}`
- Evaluation run directory: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\eval`

## Interpretability Readiness

- Checkpoints include model config, label vocabularies, tokenizer vocabulary, and reproducibility metadata.
- The supervised heads expose posterior bucket, action, EV, risk, confidence, and rationale-class targets for later probes.
- The model is small enough for CPU smoke runs and later activation-capture experiments.

## Checkpoints

- Best checkpoint: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\training\checkpoints\best.pt`
- Final checkpoint: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\training\checkpoints\final.pt`
- Tokenizer vocabulary: `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-AN\pytest-361\test_small_transformer_eval_sm0\training\vocab.json`

## Known Limitations

- This is a small synthetic model, not a frontier model.
- Training traces come from a narrow deterministic Bayesian generator and do not represent open-ended strategic reasoning.
- Metrics should not be interpreted as evidence of real-world trading, forecasting, or deployment usefulness.
- No external model downloads, external datasets, or LLM judges are used.
