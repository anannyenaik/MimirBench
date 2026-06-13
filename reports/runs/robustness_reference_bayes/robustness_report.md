# Robustness report: robustness_reference_bayes

- Run ID: `robustness_reference_bayes-20260602T035617`
- Timestamp: `2026-06-02T03:56:17Z`
- Agent: `reference` (`reference`)
- Baseline kind: **reference solver (sanity check)**
- Environments: bayesian_games
- Variant types: emotional_pressure, irrelevant_context, misleading_authority, order_permutation, paraphrase
- Base tasks: `25`
- Variants: `125`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Overall robustness metrics

- `paraphrase_consistency_rate`: `1`
- `mean_score_drop`: `7.10543e-18`
- `worst_score_drop`: `4.44089e-16`
- `action_flip_rate`: `0`
- `invalid_response_increase`: `0`
- `unsafe_action_increase`: `0`
- `risk_violation_increase`: `0`
- `pressure_susceptibility_rate`: `0`
- `order_invariance_rate`: `1`
- `distractor_robustness_rate`: `1`

## Environment breakdown

| Environment | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 125 | 1 | 7.10543e-18 | 0 | 0 | 0 |

## Variant-type breakdown

| Variant type | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| emotional_pressure | 25 | 0 | 0 | 0 | 0 | 0 |
| irrelevant_context | 25 | 0 | 0 | 0 | 0 | 0 |
| misleading_authority | 25 | 0 | 0 | 0 | 0 | 0 |
| order_permutation | 25 | 0 | 3.55271e-17 | 0 | 0 | 0 |
| paraphrase | 25 | 1 | 0 | 0 | 0 | 0 |

## Top failure cases

No failure cases were extracted.

## Scope and Limitations

- Robustness compares an agent on a base task versus deterministic, answer-preserving (or precisely-rescaled) variants of it.
- Variants are built from fixed templates and text banks, not from a language model; see ROBUSTNESS.md for the taxonomy and rationale.
- For answer-preserving variants a changed final action counts against robustness unless it is provably equivalent.
- Reference robustness is a wiring/sanity check: the deterministic solver reads structured metadata, so it is robust by construction. It is NOT a model result.

## Artefacts

- `robustness_results.jsonl`: per-variant records.
- `robustness_summary.json`: machine-readable metrics.
- `robustness_report.md`: this report.
- `failure_cases.jsonl` / `failure_cases.md`: ranked diagnostic failures.
