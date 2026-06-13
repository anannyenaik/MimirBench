# Synthetic Transformer Training

MimirBench trains compact transformers on deterministic synthetic Bayesian
traces to provide inspectable model organisms for mechanistic interpretability.

## Why Train A Small Model

Frontier models are hard to instrument and confounded by unknown pretraining data.
MimirBench therefore trains a small model on a fully controlled generator where
the exact posterior, decision labels, and risk labels are known. Once a model
learns these labels, the interpretability programme can identify where those
features are represented and used.

## Synthetic Trace Generation

Trace generation lives in `mimirbench/training/synthetic_traces.py`.

Each trace contains:

- a prior distribution over hypotheses;
- a likelihood table for discrete signals;
- an observation sequence;
- the exact posterior from the canonical Bayes calculator;
- a posterior bucket label for hypothesis A;
- action, EV, risk, confidence, and concise rationale-class labels.

The generator is deterministic from seed and split. Train, validation, and test
IDs include the split name, so split overlap is easy to detect.

## Target Labels

The supervised heads predict:

- `posterior_bucket`
- `action`
- `ev_bucket`
- `risk_flag`
- `confidence_bucket`
- `rationale_class`

The targets are final labels only. MimirBench does not generate, request, or
store hidden chain-of-thought.

## Tokenizer

`mimirbench/training/tokenizer.py` implements a deterministic regex tokenizer
with no external tokenizer dependency. The vocabulary is built from generated
training traces and saved as `vocab.json`. It supports `<pad>`, `<bos>`, `<eos>`,
`<unk>`, `<sep>`, fixed sequence length, padding, and attention masks.

## Architecture

`mimirbench/training/small_transformer.py` implements a compact PyTorch
transformer with token embeddings, positional embeddings, a small transformer
encoder stack, an optional LM head, and supervised classification heads. Torch is
imported only when training or checkpoint inference is invoked.

## Run the Tiny Smoke Configuration

Install the ML extra first:

```bash
pip install -e ".[ml]"
```

Generate traces without training:

```bash
mimirbench generate-traces configs/train_small_transformer_bayes_tiny.yaml
```

Train the tiny smoke model:

```bash
mimirbench train-small-transformer configs/train_small_transformer_bayes_tiny.yaml
```

Expected artefacts:

```text
reports/training/small_transformer_bayes_tiny/
  config_resolved.yaml
  vocab.json
  train_traces.jsonl
  val_traces.jsonl
  test_traces.jsonl
  metrics.jsonl
  summary.json
  checkpoints/best.pt
  checkpoints/final.pt
  figures/training_loss.png
  figures/validation_accuracy.png
```

## Evaluate the Checkpoint

```bash
mimirbench eval-small-transformer configs/eval_small_transformer_bayes.yaml
```

This writes:

```text
reports/runs/small_transformer_bayes_eval/
  results.jsonl
  summary.json
  report.md
  figures/
```

The evaluation computes posterior-bucket accuracy, action accuracy, risk accuracy,
confidence accuracy, approximate posterior error, regret, invalid-response rate,
and latency summaries.

## Inspect a Run

```bash
mimirbench inspect-training reports/training/small_transformer_bayes_tiny
```

The command prints dataset size, model size, best validation metrics, checkpoint
paths, figure paths, and model-card path.

## Medium Model Organism

The tiny config is a smoke test; it does not learn the task. To produce a model
whose internals are worth probing, train the medium config:

```bash
mimirbench train-small-transformer configs/train_small_transformer_bayes_medium.yaml
mimirbench eval-small-transformer  configs/eval_small_transformer_bayes_medium.yaml
```

The medium model is 2 layers, `d_model=128`, 4 heads (321,455 parameters),
trained on a deterministic split of 12,000 training / 2,000 validation / 2,000
test traces (2–10 observations each) for up to 30 epochs with early stopping
(best epoch 25), CPU-only and dropout-free. It reaches near-perfect held-out
action/risk accuracy (1.000 / 1.000), a 20-way posterior bucket accuracy of
~0.990, and ~0.0162 mean posterior error on the 2,000 unseen test tasks (eval
seed 20000, disjoint from the training seed). A single data-size ablation
(`configs/train_small_transformer_bayes_medium_ablation_data2k.yaml`, 2,000
traces, identical architecture, identical validation split) shows the binary
action/risk heads saturate from little data while the 20-way posterior bucket is
the data-hungry head. Exact numbers and the comparison table live in
`RESULTS.md` ("Larger Small-Transformer Model Organism").

This medium checkpoint is the one the medium interpretability run
analyses, and the one that yields a (narrow, synthetic) positive causal patching
result.

### Checkpoints and reproducibility

The binary `.pt` checkpoint files (`checkpoints/best.pt`, `checkpoints/final.pt`)
are **gitignored** (see `.gitignore`); they are not committed. Everything needed
to regenerate them bit-for-bit is committed: the training config, the resolved
config, the deterministic trace generator, `vocab.json`, and a fixed seed (123,
CPU, dropout 0). Re-running `train-small-transformer` on the same config
reproduces the checkpoint, and the committed `summary.json`, `metrics.jsonl`,
figures, and model card under `reports/training/small_transformer_bayes_medium/`
record the numbers without needing the weights.

## Interpretability

Checkpoints include the model config, label vocabularies, tokenizer payload, and
run metadata. The supervised heads create clean targets for linear probes and
activation patching, which the interpretability pipeline implements end to end:

- activation capture hooks (`mimirbench/interpretability/activation_capture.py`);
- linear probes for posterior, risk, action, and confidence
  (`probes.py`);
- clean/corrupted Bayesian prompt pairs (`counterfactuals.py`);
- activation patching (`activation_patching.py`);
- attention analysis (`attention_analysis.py`);
- a config-driven runner, reports, and figures (`runner.py`).

Run it once the checkpoint exists:

```bash
mimirbench run-interpretability configs/interp_bayes_all_tiny.yaml
mimirbench inspect-interpretability reports/interpretability/interp_bayes_all_tiny
```

See `INTERPRETABILITY.md` for methods, findings, and limitations. The interpretability
results describe this small synthetic model only and make no frontier-model claim.

## Limitations

- The model is small and synthetic; it is not a frontier model.
- The generator is narrow and currently Bayesian-task focused.
- Good held-out synthetic metrics would not prove open-ended strategic reasoning.
- No external datasets or model downloads are used.
- Results belong in `RESULTS.md` only after artefacts are actually generated.
