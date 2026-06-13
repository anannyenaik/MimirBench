# Statistical validity

MimirBench's hosted-model numbers are a **pilot**: 20 tasks per environment, six
environments, a single seed/schedule, and a synthetic task distribution. This
document defines the uncertainty analysis and the correct interpretation of the
generated tables.

> **One-line framing:** every interval here is a *pilot CI over the saved
> synthetic sample*, quantifying resampling noise on that fixed sample — **not** a
> population-level benchmark claim.

## Method

The analysis lives in
[`mimirbench/analysis/statistical_validity.py`](mimirbench/analysis/statistical_validity.py)
and is run with:

```bash
mimirbench statistical-validity
```

This command **never runs a model**. It reads the per-task `results.jsonl` files
already saved under `reports/runs/leaderboard/` and computes, with a seeded
percentile bootstrap (`n_resamples=2000`, 95%):

- **mean-score 95% CI** — bootstrap over per-task scores;
- **pass-rate CI**, **parse-failure-rate CI**, **risk-violation-rate CI** —
  bootstrap over the per-task 0/1 indicators;
- **paired model deltas** — computed only over tasks whose
  `(environment, task_id, seed)` actually align in both rows; otherwise the pair is
  reported as an *unpaired descriptive comparison*;
- **per-row n** and **p50/p95 latency**.

The generated canonical table is written to
[`reports/runs/leaderboard/statistical_validity_existing_artifacts.md`](reports/runs/leaderboard/statistical_validity_existing_artifacts.md)
with the columns:

`Model | Track | n | Mean | 95% CI | Pass | Parse fail | Risk violation | Cost | p50/p95 latency | Caveat`

## Planning for larger hosted-model runs

The implemented full protocol is described in
[FULL_BENCHMARK_PROTOCOL.md](FULL_BENCHMARK_PROTOCOL.md). A saved-artefact-only
planning command estimates approximate mean-score CI widths under the pilot,
100/environment x 3-seed, and 200/environment x 5-seed designs:

```bash
mimirbench power-plan-full-benchmark
```

The generated report is
[`reports/runs/leaderboard/full_benchmark_power_plan.md`](reports/runs/leaderboard/full_benchmark_power_plan.md).
**These are planning estimates based on pilot variance, not results from unrun
hosted-model evaluations.** Because the pilot has one seed, it cannot estimate
seed-to-seed variation; full runs must report that variation directly.

## Interpreting Paired Deltas

A paired delta is `candidate − baseline` over aligned tasks. A 95% bootstrap CI
that **excludes 0** indicates the paired difference is unlikely to be sampling
noise *on this sample*. It is **not** a population-level significance test, and with
a single seed it cannot speak to seed-to-seed variation.

On the current saved sample (n = 120 aligned tasks per pair), the deltas whose CI
excludes 0 include `gpt-5.4` over `gpt-5.4-mini`, Claude Sonnet 4.6 (1536) and
Gemini Pro Preview both over `gpt-5.4`, and Gemini Pro over Gemini Flash; the
`gpt-4.1-mini` vs `gpt-5.4` and Sonnet-1536 vs Gemini-Pro deltas have CIs that
**include 0** (indistinguishable on this sample). Read the generated table for the
exact intervals; do not paraphrase them as "significantly better".

## Tracks and comparability

Rows are grouped by the tracks defined in
[BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md):

- **strict-track clean** rows share the 512-token budget and decoding protocol and
  are directly comparable.
- **best-valid clean** rows use each provider's documented minimum-valid settings;
  cross-provider deltas there are **not identical-decoding**.
- **protocol-limited** rows are included for completeness but reflect
  output-budget/protocol behaviour, not capability.

## Scope and Limitations

- **Single seed/schedule.** CIs capture resampling noise over one fixed task
  schedule, not variation across seeds.
- **Synthetic task distribution.** Deterministic synthetic environments; the CIs do
  not generalise to real-world or live tasks.
- **Not identical-decoding across providers** on the best-valid track.
- **No broad superiority or trading claim.** These are model-ranking diagnostics for
  this synthetic benchmark only.
- **No pilot significance claim.** Narrow pilot intervals or paired deltas do not
  justify describing the current hosted-model rows as statistically significant.
