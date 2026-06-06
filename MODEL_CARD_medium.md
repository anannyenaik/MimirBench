# Model card: medium synthetic Bayesian/risk transformer

A curated, human-readable card for the **medium model organism** — the checkpoint
that learns the synthetic Bayesian-to-decision mapping and yields MimirBench's
narrow causal interpretability result. The auto-generated companion card is
[`reports/model_cards/small_transformer_bayes_medium.md`](reports/model_cards/small_transformer_bayes_medium.md).

> This is a small, fully synthetic model organism. **No frontier-model claim is
> made and nothing here transfers to frontier-model internals.**

## Architecture

| Property | Value |
| --- | ---: |
| Architecture | compact transformer encoder (`nn.TransformerEncoder`, post-norm) |
| Layers | 2 |
| Attention heads | 4 |
| Hidden size (`d_model`) | 128 |
| Feed-forward | 256 |
| Parameters | 321,455 |
| Vocab size | 137 |
| Dropout | 0.0 (deterministic) |
| Output heads | posterior_bucket (20-way), action (2), ev_bucket (7), risk_flag (2), confidence_bucket (3), rationale_class (4) |

## Training data generator

- **Source:** deterministic synthetic Bayesian traces generated inside MimirBench
  (`mimirbench/training/synthetic_traces.py`), not external data.
- Each trace is a Bayesian-updating problem: a prior, a likelihood table, a
  sequence of observations, and a payoff/risk configuration; targets are the
  Bayes-optimal posterior bucket, action, EV bucket, risk flag, confidence bucket,
  and a rationale class.
- **Generator settings:** `num_hypotheses=2`, `min_observations=2`,
  `max_observations=10`, `signal_reliability=0.75`, `posterior_buckets=20`,
  payoff `{reward_if_A=1.0, loss_if_not_A=1.0, decision_cost=0.0, risk_tolerance=0.35}`.
- **Stored targets are final labels and concise rationale classes only**; no hidden
  chain-of-thought is generated or stored.

## Dataset sizes and seed

| Split | Count |
| --- | ---: |
| train | 12,000 |
| val | 2,000 |
| test | 2,000 |

- **Seed:** 123 (single seed). Dropout 0, CPU — fully deterministic.
- The held-out eval uses a **disjoint seed (20000)** and the `test`-split
  generator, so eval tasks were never trained on. Splits are content-disjoint (no
  shared input string across train/val/test), verified in
  `tests/test_medium_milestone.py`.

## Training configuration

`batch_size=64`, `epochs=30` (early stopping, best at epoch 25), `learning_rate=1e-3`,
`weight_decay=0.01`, `grad_clip=1.0`, `device=cpu`. Full resolved config:
`reports/training/small_transformer_bayes_medium/config_resolved.yaml`.

## Held-out metrics (2,000 unseen tasks, seed 20000)

| Metric | Value |
| --- | ---: |
| posterior bucket accuracy (20-way) | 0.990000 |
| action accuracy | 1.000000 |
| risk flag accuracy | 1.000000 |
| confidence bucket accuracy | 0.997500 |
| approx. posterior absolute error (mean) | 0.016229 |
| mean regret | 0.005701 |
| invalid response rate | 0.000000 |

Best validation metrics (epoch 25): val loss 0.031958, action/risk/rationale
accuracy 1.000, posterior-bucket accuracy 0.9935, confidence 0.998, EV 0.9985.

## Intended use

- A **model organism** for mechanistic interpretability under known ground truth:
  probes, clean/corrupted activation patching, attention analysis, and the
  position-resolved extensions in
  [`reports/interpretability/interp_bayes_medium_extended/`](reports/interpretability/interp_bayes_medium_extended/).
- A CPU-friendly checkpoint for reproducing the narrow causal patching result.
- A convenience copy of `best.pt` and its `vocab.json` is attached to the
  [v0.2.0 GitHub release](https://github.com/anannyenaik/MimirBench/releases/tag/v0.2.0).
  The release asset is optional: the checkpoint remains reproducible from the
  committed training config.

## Limitations

- This card documents one checkpoint (seed 123). The interpretability *result* it
  supports is **replicated across six independently trained checkpoints (seeds
  123–128)** — see
  [`reports/interpretability/interp_bayes_multiseed_summary.md`](reports/interpretability/interp_bayes_multiseed_summary.md).
  It remains one narrow synthetic Bayesian/risk generator.
- The encoder mean-pools before the heads, so whole-site patching localises at the
  sub-block level. Per-head patching/ablation and individual-position patching
  refine the result: no head dominates consistently across seeds, and isolated
  token-position patches have effectively zero action recovery. See
  [`interp_bayes_head_token_summary.md`](reports/interpretability/interp_bayes_head_token_summary.md).
- Strong held-out metrics show the model learned the generator, not open-ended or
  real-world strategic reasoning.
- No hidden chain-of-thought; all labels are deterministic outputs of public task
  data.
- **Nothing here transfers to frontier-model internals.**

## Checksums (release assets and locally generated copy; checkpoint not committed)

`.pt` files are gitignored (see [ARTIFACTS.md](ARTIFACTS.md)); these SHA256 hashes
record the locally generated artefacts. The v0.2.0 release assets for `best.pt`
and `vocab.json` have the same hashes.

| File | SHA256 | Bytes |
| --- | --- | ---: |
| `checkpoints/best.pt` | `3f273cfe70d94e42c0f1b0440b9a907203c6260e6e03e02eff6ad5f4eaa1c546` | 1,301,217 |
| `checkpoints/final.pt` | `137ec5d15241557ebc25d7f33a56ec45736c043b9780afe28b9eb43f98d96d89` | 1,301,263 |
| `vocab.json` | `d7a994c5a616d4326250483528ff0cd06f933b05c41cf7d735f428d64ba2ecfa` | 2,025 |

> PyTorch container differences across versions/platforms can change the byte-level
> hash for identical weights; if so, validate via the held-out metrics above.

## Reproduce exactly

```bash
pip install -e ".[ml]"
mimirbench train-small-transformer configs/train_small_transformer_bayes_medium.yaml
mimirbench eval-small-transformer  configs/eval_small_transformer_bayes_medium.yaml
mimirbench run-interpretability          configs/interp_bayes_all_medium.yaml
mimirbench run-extended-interpretability configs/interp_bayes_medium_extended.yaml
mimirbench run-head-token-interpretability configs/interp_bayes_medium_multiseed.yaml
```
