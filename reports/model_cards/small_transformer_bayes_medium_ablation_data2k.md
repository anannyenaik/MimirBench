# Model card: small_transformer_bayes_medium_ablation_data2k

## Identity

- Model name: `small_transformer_bayes_medium_ablation_data2k`
- Model type: compact synthetic Bayesian trace transformer
- Training run directory: `reports\training\small_transformer_bayes_medium_ablation_data2k`
- Created from actual training artefacts: `yes`

## Architecture

- Architecture: `compact_transformer_encoder`
- Parameter count: `321455`
- Target heads: `posterior_bucket, action, ev_bucket, risk_flag, confidence_bucket, rationale_class`
- Model config: `{"d_model": 128, "dim_feedforward": 256, "dropout": 0.0, "lm_loss_weight": 0.0, "max_seq_len": 128, "n_heads": 4, "n_layers": 2, "num_actions": 2, "num_confidence_buckets": 3, "num_ev_buckets": 7, "num_posterior_buckets": 20, "num_rationale_classes": 4, "num_risk_flags": 2, "pad_token_id": 0, "vocab_size": 137}`

## Training Data

- Data source: deterministic synthetic Bayesian traces generated inside MimirBench
- Synthetic traces: train=`2000`, val=`2000`, test=`2000`
- Data config: `{"max_observations": 10, "min_observations": 2, "num_hypotheses": 2, "num_test": 2000, "num_train": 2000, "num_val": 2000, "payoff": {"decision_cost": 0.0, "loss_if_not_A": 1.0, "reward_if_A": 1.0, "risk_tolerance": 0.35}, "posterior_buckets": 20, "seed": 123, "signal_reliability": 0.75}`
- Stored targets are final labels and concise rationale classes only; hidden chain-of-thought is not generated or stored.

## Training Config

- Optimisation config: `{"batch_size": 64, "device": "cpu", "early_stopping_patience": 5, "epochs": 30, "grad_clip": 1.0, "learning_rate": 0.001, "weight_decay": 0.01}`
- Full resolved config: `reports\training\small_transformer_bayes_medium_ablation_data2k\config_resolved.yaml`

## Validation Metrics

- Best epoch: `30`
- Best validation metrics: `{"epoch": 30, "train_loss": 0.15830374395847321, "val_action_accuracy": 0.9985, "val_confidence_bucket_accuracy": 0.9925, "val_ev_bucket_accuracy": 0.9845, "val_loss": 0.22216769063472747, "val_posterior_bucket_accuracy": 0.962, "val_rationale_class_accuracy": 0.994, "val_risk_flag_accuracy": 0.998}`

## Held-Out MimirBench Metrics

- Held-out checkpoint evaluation has not been run for this card.

## Interpretability Readiness

- Checkpoints include model config, label vocabularies, tokenizer vocabulary, and reproducibility metadata.
- The supervised heads expose posterior bucket, action, EV, risk, confidence, and rationale-class targets for later probes.
- The model is small enough for CPU smoke runs and later activation-capture experiments.

## Checkpoints

- Best checkpoint: `reports\training\small_transformer_bayes_medium_ablation_data2k\checkpoints\best.pt`
- Final checkpoint: `reports\training\small_transformer_bayes_medium_ablation_data2k\checkpoints\final.pt`
- Tokenizer vocabulary: `reports\training\small_transformer_bayes_medium_ablation_data2k\vocab.json`

## Known Limitations

- This is a small synthetic model, not a frontier model.
- Training traces come from a narrow deterministic Bayesian generator and do not represent open-ended strategic reasoning.
- Metrics should not be interpreted as evidence of real-world trading, forecasting, or deployment usefulness.
- No external model downloads, external datasets, or LLM judges are used.
