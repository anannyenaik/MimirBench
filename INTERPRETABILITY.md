# Interpretability

MimirBench uses controlled synthetic transformers to study how evidence is
represented and used in strategic decisions. The programme combines activation
capture, linear probes, causal patching, attention analysis, robustness probes,
and six-seed model-organism replication.

## What is analysed

The behavioural evals ask whether an agent reasons well under uncertainty. The
interpretability track asks *how* a model represents that reasoning internally:

- **Posterior beliefs** — is the Bayesian posterior bucket linearly decodable
  from the activations?
- **Risk flags** — is the safe/risky distinction represented?
- **Action decisions** — is the buy/pass decision represented, and is it
  *causally* driven by the evidence?
- **Confidence** — is the confidence bucket represented?

We analyse the synthetic checkpoint trained by
`mimirbench/training/train_small_transformer.py` on deterministic synthetic
Bayesian traces. Because we own the generator, the exact posterior and the final
action/risk labels are known, so we know precisely what an interpretability
method should be able to recover.

## Why small synthetic models are appropriate

Mechanistic interpretability on frontier models is confounded by unknown
pretraining data, unavailable ground-truth posteriors, and scale. MimirBench uses
a **model-organism** approach: a compact, fully
controlled transformer trained on a generator we wrote. This buys:

- **Ground truth.** We know the true posterior and decision for every input, so
  probe targets and patching directions are exact, not guessed.
- **Determinism.** Traces, counterfactuals, captures, probes, and patches are all
  seed-controlled and reproducible on CPU with no downloads.
- **Falsifiability.** Each experiment states what would count as a negative
  result, and negative results are reported as-is.

The resulting mechanisms are specific to this controlled model family; external
validity is addressed explicitly in the limitations section.

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
we can expose the residual stream, per-head attention weights, projected
per-head outputs, token-position activations, and clean patch sites without
disturbing the default training path.

## Linear probes

`mimirbench/interpretability/probes.py`

A ridge classifier (sklearn `RidgeClassifier` when available, a closed-form NumPy
one-hot ridge fallback otherwise) is fit on a train split of captured activations
and evaluated on held-out val/test splits. For each (site, label) we report train
/ val / test accuracy, the class distribution, a confusion matrix, and — crucially
— the **majority-class baseline**, so accuracy is always read relative to chance.

## Activation patching

`mimirbench/interpretability/{counterfactuals,activation_patching}.py`

`counterfactuals.py` builds minimal pairs from the training machinery: a **clean**
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

## Causal Evidence Criteria

- A patch at a specific site that **consistently** moves the corrupted prediction
  back to the clean decision: a high recovery rate and a positive causal effect
  concentrated at that site (and not at others).
- A probe direction whose **ablation** measurably degrades the matching decision.
- An attention head whose evidence-reading behaviour correlates with patch effects.

## Insufficient Evidence

- **High probe accuracy alone.** Decodability is correlational; a feature can be
  present in activations without being used by the model.
- **Causal effects within noise**, or recovery rates near the corruption's flip
  rate.
- **Trivial restoration.** Patching the full final residual stream necessarily
  reproduces the clean output; that is a sanity check, not localisation.
- **Anything transferring to larger or frontier models.**

## Tiny Checkpoint Findings

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

## Medium Checkpoint Findings

The tiny checkpoint was undertrained and did not expose a learned computation to
localise. A stronger **medium** model organism (2 layers, `d_model=128`, 4 heads,
321,455 parameters, trained on 12,000 traces) was therefore trained and analysed
with `configs/interp_bayes_all_medium.yaml` (256 traces/split, 128 counterfactual
pairs). Full numbers are in `RESULTS.md`:

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
result, but a deliberately narrow one. The six-seed per-head and
individual-position analysis below shows that the result does not localise to a
single stable head or token position. There is no SAE-level analysis and no
transfer to frontier models.

## Position-Resolved Patching and Negative Controls

`mimirbench/interpretability/{token_group_patching,extended_interpretability}.py`

The whole-site result above cannot say *which token positions* carry the signal,
so `mimirbench run-extended-interpretability configs/interp_bayes_medium_extended.yaml`
adds three deterministic experiments on the medium checkpoint. Artefacts:
`reports/interpretability/interp_bayes_medium_extended/EXTENDED_INTERPRETABILITY_REPORT.md`.

- **Token-group (position-resolved) patching.** Each sub-block site is patched
  *only* at the positions of one token group (prior / evidence / payoff-risk).
  Because the corruption changes only the evidence tokens, prior/payoff-risk are
  negative controls. **Result:** patching any single token group's
  positions recovers the flipped action on ≤2% of pairs — including the evidence
  group. The evidence→decision signal is therefore **distributed across positions**
  (the encoder mean-pools, and attention spreads the evidence everywhere), not
  localised to the evidence token positions. This is reported as a negative result
  and refines the whole-site claim rather than overturning it.
- **Mismatched-donor negative control.** At `blocks.0.attn_out`, a matched
  whole-site patch recovers the action on **0.967** of flipped pairs, while a clean
  donor from an unrelated same-length example recovers only **0.533** (posterior
  bucket: 0.906 matched vs 0.211 mismatched). The patch restores the *specific*
  clean computation, not a generic activation shift.
- **Label-shuffle probe control.** The action probe at `blocks.1.mlp_out` scores
  **1.000** on real labels and **0.484** (below the 0.594 majority baseline) on
  shuffled labels, confirming the probe reads genuine structure, not noise.

**Six-seed model-organism replication.** The extended findings above — attention-concentrated
whole-site recovery, ≤~2% token-group recovery, the mismatched-donor gap, and the
label-shuffle collapse — are **replicated across six independently trained
synthetic checkpoints (seeds 123–128)**. Each seed independently resamples the
training data, the weight initialisation, and the probe/patch set. Across the six
seeds the layer-0 *MLP* action recovery is **0.000 on every seed** while layer-0/
layer-1 *attention* recovery is 0.96/0.99 (mean); single-token-group recovery
stays ≤2.6%; the mismatched-donor action gap averages 0.96 (matched) vs 0.50
(mismatched); and the shuffled-label probe collapses to ≤ baseline on every seed.
The seed-123 numbers quoted above are the worked example; the per-seed table and
mean/range are in
[`reports/interpretability/interp_bayes_multiseed_summary.md`](reports/interpretability/interp_bayes_multiseed_summary.md).
Regenerate with
`mimirbench run-multiseed-interpretability configs/interp_bayes_medium_multiseed.yaml`
(CPU; no API calls).

## Per-Head and Individual-Token Analysis

`mimirbench/interpretability/head_token_analysis.py`

`mimirbench run-head-token-interpretability configs/interp_bayes_medium_multiseed.yaml`
uses the saved seed 123–128 checkpoints and runs:

- matched and mismatched-donor patching of one projected attention-head output
  at a time;
- zero-ablation of each head, with a random-position ablation control;
- one-position-at-a-time patching at both attention sub-block outputs, followed
  only then by semantic token-group aggregation.

All six seeds completed. The result **confirms but refines** the attention
sub-block story:

- no head is strongest on more than one seed; the best mean single-head action
  recovery is 0.141;
- per-head mismatched-donor recovery is lower but still substantial for some
  heads, so the per-head control does not isolate a clean donor-specific circuit;
- zero-ablation shows distributed necessity, with the largest mean degradation
  0.051 action accuracy and 0.314 posterior-bucket accuracy;
- individual token-position action recovery is effectively zero, confirming that
  no isolated position explains the whole-site result.

This supports an attention-mediated but distributed computation. It does not
support a clean circuit claim. Full tables and seed ranges:
[`reports/interpretability/interp_bayes_head_token_summary.md`](reports/interpretability/interp_bayes_head_token_summary.md).

## Reproduction

```bash
pip install -e ".[ml]"               # torch is required for the model paths
mimirbench run-interpretability configs/interp_bayes_all_tiny.yaml
mimirbench inspect-interpretability reports/interpretability/interp_bayes_all_tiny

# The medium model organism (the one with the causal patching result):
mimirbench run-interpretability configs/interp_bayes_all_medium.yaml
mimirbench inspect-interpretability reports/interpretability/interp_bayes_all_medium

# Extended, position-resolved patching plus negative controls:
mimirbench run-extended-interpretability configs/interp_bayes_medium_extended.yaml

# Six-seed model-organism replication across seeds 123-128:
# trains any missing per-seed checkpoint, reruns the whole-site + extended
# pipeline and a held-out eval per seed, and writes a mean/range aggregate.
mimirbench run-multiseed-interpretability configs/interp_bayes_medium_multiseed.yaml

# Per-head patching/ablation and individual-position patching across saved seeds:
mimirbench run-head-token-interpretability configs/interp_bayes_medium_multiseed.yaml
```

Single-experiment configs also exist: `interp_bayes_probes_tiny.yaml`,
`interp_bayes_patching_tiny.yaml`, `interp_bayes_attention_tiny.yaml`. If the
checkpoint or torch is unavailable, the runner writes a *pending* report rather
than failing, and the infrastructure remains fully tested.

## Limitations

- The model is tiny, fully synthetic, and trained on a narrow Bayesian generator;
  mean pooling dilutes individual-token effects.
- The worked seed-123 numbers are checkpoint-specific; the headline
  interpretability claims are aggregated across seeds 123–128.
- Near-zero and negative results are expected for an underpowered model organism
  and are reported without spin.
- Sparse autoencoders remain optional future work (`sae_features.py` is a config
  scaffold only).
- Per-head patching and ablation do not isolate neurons or SAE features; zero
  ablation can also move activations off distribution.
- These experiments characterise one small model. They are not evidence about
  frontier-model internals.
