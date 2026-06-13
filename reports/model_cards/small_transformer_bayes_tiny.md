# Model card: small_transformer_bayes_tiny

## Identity

- Model name: `small_transformer_bayes_tiny`
- Model type: compact synthetic Bayesian trace transformer
- Training run directory: `reports\training\small_transformer_bayes_tiny`
- Created from actual training artefacts: `yes`

## Architecture

- Architecture: `compact_transformer_encoder`
- Parameter count: `22669`
- Target heads: `posterior_bucket, action, ev_bucket, risk_flag, confidence_bucket, rationale_class`
- Model config: `{"d_model": 32, "dim_feedforward": 64, "dropout": 0.0, "lm_loss_weight": 0.0, "max_seq_len": 128, "n_heads": 2, "n_layers": 1, "num_actions": 2, "num_confidence_buckets": 3, "num_ev_buckets": 7, "num_posterior_buckets": 20, "num_rationale_classes": 4, "num_risk_flags": 2, "pad_token_id": 0, "vocab_size": 135}`

## Training Data

- Data source: deterministic synthetic Bayesian traces generated inside MimirBench
- Synthetic traces: train=`128`, val=`32`, test=`32`
- Data config: `{"max_observations": 6, "min_observations": 1, "num_hypotheses": 2, "num_test": 32, "num_train": 128, "num_val": 32, "payoff": {"decision_cost": 0.0, "loss_if_not_A": 1.0, "reward_if_A": 1.0, "risk_tolerance": 0.35}, "posterior_buckets": 20, "seed": 123, "signal_reliability": 0.7}`
- Stored targets are final labels and concise rationale classes only; hidden chain-of-thought is not generated or stored.

## Training Config

- Optimisation config: `{"batch_size": 32, "device": "cpu", "early_stopping_patience": null, "epochs": 2, "grad_clip": 1.0, "learning_rate": 0.001, "weight_decay": 0.01}`
- Full resolved config: `reports\training\small_transformer_bayes_tiny\config_resolved.yaml`

## Validation Metrics

- Best epoch: `2`
- Best validation metrics: `{"epoch": 2, "train_loss": 8.54984426498413, "val_action_accuracy": 0.25, "val_confidence_bucket_accuracy": 0.59375, "val_ev_bucket_accuracy": 0.15625, "val_loss": 8.5946683883667, "val_posterior_bucket_accuracy": 0.15625, "val_rationale_class_accuracy": 0.28125, "val_risk_flag_accuracy": 0.75}`

## Held-Out MimirBench Metrics

- Held-out evaluation summary: `{"action_accuracy": 0.4453125, "approx_posterior_abs_error_mean": 0.4510692918970604, "confidence_bucket_accuracy": 0.5703125, "invalid_response_rate": 0.0, "latency_mean_ms": 27.30671171866561, "latency_p50_ms": 10.482450001291, "latency_p95_ms": 129.0135750034096, "posterior_bucket_accuracy": 0.0546875, "regret_mean": 0.26037435970090295, "risk_flag_accuracy": 0.5546875}`
- Evaluation run directory: `reports\runs\small_transformer_bayes_eval`

## Interpretability Readiness

- Checkpoints include model config, label vocabularies, tokenizer vocabulary, and reproducibility metadata.
- The supervised heads expose posterior bucket, action, EV, risk, confidence, and rationale-class targets for later probes.
- The model is small enough for CPU smoke runs and later activation-capture experiments.

## Checkpoints

- Best checkpoint: `reports\training\small_transformer_bayes_tiny\checkpoints\best.pt`
- Final checkpoint: `reports\training\small_transformer_bayes_tiny\checkpoints\final.pt`
- Tokenizer vocabulary: `reports\training\small_transformer_bayes_tiny\vocab.json`

## Scope and Limitations

- This is a small synthetic model, not a frontier model.
- Training traces come from a narrow deterministic Bayesian generator and do not represent open-ended strategic reasoning.
- Metrics should not be interpreted as evidence of real-world trading, forecasting, or deployment usefulness.
- No external model downloads, external datasets, or LLM judges are used.
