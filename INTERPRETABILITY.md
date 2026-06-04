# Interpretability

> **Status:** Stage 8 is implemented. Activation capture, linear probes,
> clean/corrupted activation patching, and attention analysis run end to end on a
> trained small Bayesian transformer and write inspectable artefacts and figures.
> All findings are about small, fully synthetic model organisms (a tiny smoke
> checkpoint and a stronger medium one). **No claim is made about frontier models,
> and no result here transfers to them.**

## What is analysed

The behavioural evals ask whether an agent reasons well under uncertainty. The
interpretability track asks *how* a model represents that reasoning internally:

- **Posterior beliefs** — is the Bayesian posterior bucket linearly decodable
  from the activations?
- **Risk flags** — is the safe/risky distinction represented?
- **Action decisions** — is the buy/pass decision represented, and is it
  *causally* driven by the evidence?
- **Confidence** — is the confidence bucket represented?

We analyse the Stage 7 checkpoint trained by
`mimirbench/training/train_small_transformer.py` on deterministic synthetic
Bayesian traces. Because we own the generator, the exact posterior and the final
action/risk labels are known, so we know precisely what an interpretability
method should be able to recover.

## Why small synthetic models are appropriate

Running mechanistic interpretability directly on frontier models is hard and
confounded: unknown pretraining data, no ground-truth posterior, and enormous
scale. MimirBench uses a **model-organism** approach instead — a tiny, fully
controlled transformer trained on a generator we wrote. This buys:

- **Ground truth.** We know the true posterior and decision for every input, so
  probe targets and patching directions are exact, not guessed.
- **Determinism.** Traces, counterfactuals, captures, probes, and patches are all
  seed-controlled and reproducible on CPU with no downloads.
- **Falsifiability.** Each experiment states what would count as a negative
  result, and negative results are reported as-is.

The cost is external validity: a mechanism found here is evidence about *this*
model only. That trade — honesty and control over scale and transfer — is the
whole point.

## Activation capture

`mimirbench/interpretability/activation_capture.py`

- `ActivationCapturer` registers forward hooks on named modules and records their
  outputs during a no-grad pass (the generic "named module hooks" tool).
- `capture_trace_activations` runs the model's instrumented forward over a batch
  of traces and mean-pools each site over the un-padded sequence — exactly the
  pooling the classification heads see — producing one feature vector per trace
  per site.
- Captured sites: the embedding output, and per block the attention-sub-block
  output (`blocks.i.attn_out`), MLP-sub-block output (`blocks.i.mlp_out`), and
  the residual stream after the block (`blocks.i.resid_post`).
- Output is a `.npz` of arrays plus a `.json` sidecar holding the checkpoint
  path, dataset split, site names, tensor shapes, trace IDs, and per-trace labels.

The instrumented forward (`SmallTransformerForTracePrediction.forward_instrumented`)
reproduces the default forward to ~1e-7 at every un-padded position; it exists so
we can expose the residual stream, per-head attention weights, and clean patch
sites without disturbing the default training path.

## Linear probes

`mimirbench/interpretability/probes.py`

A ridge classifier (sklearn `RidgeClassifier` when available, a closed-form NumPy
one-hot ridge fallback otherwise) is fit on a train split of captured activations
and evaluated on held-out val/test splits. For each (site, label) we report train
/ val / test accuracy, the class distribution, a confusion matrix, and — crucially
— the **majority-class baseline**, so accuracy is always read relative to chance.

## Activation patching

`mimirbench/interpretability/{counterfactuals,activation_patching}.py`

`counterfactuals.py` builds minimal pairs from the Stage 7 machinery: a **clean**
trace and a **corrupted** trace that share prior, likelihood, and payoff but whose
evidence points at a different hypothesis (plus order-control and distractor
variants). The same `compute_trace_targets` used in training labels both sides.

`activation_patching.py` then, for each pair and site: runs the clean input and
caches activations; runs the corrupted input; and re-runs the corrupted input with
one site overwritten by the clean activation. The headline metric is

```text
causal_effect = P(clean target | patched corrupted) - P(clean target | corrupted)
```

where the "clean target" is the model's own clean-run decision. We also report a
recovery rate over the pairs whose prediction the corruption actually flipped.

## Attention analysis

`mimirbench/interpretability/attention_analysis.py`

Input tokens are grouped into prior / likelihood / evidence / payoff-risk spans.
For each layer and head we report attention entropy (how diffuse the head is) and
the attention mass placed on each token group, plus the top attended positions.

## What would count as causal evidence

- A patch at a specific site that **consistently** moves the corrupted prediction
  back to the clean decision: a high recovery rate and a positive causal effect
  concentrated at that site (and not at others).
- A probe direction whose **ablation** measurably degrades the matching decision.
- An attention head whose evidence-reading behaviour correlates with patch effects.

## What would NOT count as causal evidence

- **High probe accuracy alone.** Decodability is correlational; a feature can be
  present in activations without being used by the model.
- **Causal effects within noise**, or recovery rates near the corruption's flip
  rate.
- **Trivial restoration.** Patching the full final residual stream necessarily
  reproduces the clean output; that is a sanity check, not localisation.
- **Anything transferring to larger or frontier models.**

## Findings on the current checkpoint (honest summary)

The shipped checkpoint is deliberately tiny (1 layer, `d_model=32`, 2 heads,
trained 2 epochs on 128 traces). On it:

- **Probes:** the action and risk-flag labels are linearly decodable above the
  majority baseline; the 20-way posterior bucket is only weakly decodable; the
  confidence bucket sits at baseline (a negative result).
- **Patching:** because the model mean-pools and the decision heads are close to
  constant on these pairs, corrupting the evidence barely moves the prediction, so
  causal effects and recovery rates are small. Full-residual-stream and embedding
  patches restore the clean output (the expected sanity check); isolated attn/MLP
  sub-block patches do not.
- **Attention:** attention is near-uniform/diffuse, with no strong
  evidence-reading head.

Exact numbers are in `RESULTS.md` and in each run's
`reports/interpretability/<run>/INTERPRETABILITY_REPORT.md`. Read the probe and
patching results together: the representation encodes the decision above chance,
but on this underpowered model the decision is only weakly evidence-driven.

## Findings on the medium checkpoint (a narrow causal result)

The tiny checkpoint was undertrained, so there was no learned computation to
localise. A stronger **medium** model organism (2 layers, `d_model=128`, 4 heads,
321,455 parameters, trained on 12,000 traces) was therefore trained and analysed
with `configs/interp_bayes_all_medium.yaml` (256 traces/split, 128 counterfactual
pairs). Full numbers are in `RESULTS.md`; the honest summary:

- **Probes:** every label is now strongly decodable. The 20-way posterior bucket
  reaches 0.984 test accuracy (baseline 0.297) at `blocks.1.resid_post`; action
  and risk hit 1.000; confidence 1.000. Decodability has clearly improved over the
  tiny model — but it is still only decodability.
- **Patching — the causal part.** Corrupting the evidence now actually flips the
  model's action on 122/128 pairs (the tiny model had zero flips), so recovery
  rates mean something. Patching the **layer-0 attention sub-block output** from
  the clean run into the corrupted run restores the clean action on **118/122**
  flipped pairs (0.967) and the clean posterior bucket on 116/128 (0.906), whereas
  patching the **layer-0 MLP sub-block output** restores **0/122** and **0/128**.
  Layer-1 attention behaves the same (119/122); layer-1 MLP only partially
  (88/122). The `embed` and full `resid_post` sites recover 100% as the expected
  sanity checks (a full-stream patch reproduces the clean forward), not as
  localisation.
- **Attention:** layer 0 puts 0.485 attention mass on the evidence tokens (vs
  0.077 on the prior) and layer 1 shifts to the prior (0.415), independently
  consistent with the patching result.

Read together, the sub-block patching contrast (attention recovers the decision,
the layer-0 MLP does not) plus the evidence-reading attention is evidence that
**the attention sub-blocks — layer-0 attention especially — causally carry this
model's learned evidence-to-decision computation**. This is a positive causal
result, but a deliberately narrow one: it is full-sequence (not per-token or
per-head) patching on a single synthetic checkpoint and seed, with mean pooling
before the heads, no SAE, and no transfer to frontier models.

## Running it

```bash
pip install -e ".[ml]"               # torch is required for the model paths
mimirbench run-interpretability configs/interp_bayes_all_tiny.yaml
mimirbench inspect-interpretability reports/interpretability/interp_bayes_all_tiny

# The medium model organism (the one with the causal patching result):
mimirbench run-interpretability configs/interp_bayes_all_medium.yaml
mimirbench inspect-interpretability reports/interpretability/interp_bayes_all_medium
```

Single-experiment configs also exist: `interp_bayes_probes_tiny.yaml`,
`interp_bayes_patching_tiny.yaml`, `interp_bayes_attention_tiny.yaml`. If the
checkpoint or torch is unavailable, the runner writes a *pending* report rather
than failing, and the infrastructure remains fully tested.

## Limitations

- The model is tiny, fully synthetic, and trained on a narrow Bayesian generator;
  mean pooling dilutes individual-token effects.
- Probe and patching numbers are specific to this checkpoint and seed.
- Near-zero and negative results are expected for an underpowered model organism
  and are reported without spin.
- Sparse autoencoders remain optional future work (`sae_features.py` is a config
  scaffold only).
- These experiments characterise one small model. They are not evidence about
  frontier-model internals.
