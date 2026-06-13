# Robustness report: robustness_reference_all_envs

- Run ID: `robustness_reference_all_envs-20260602T035617`
- Timestamp: `2026-06-02T03:56:17Z`
- Agent: `reference` (`reference`)
- Baseline kind: **reference solver (sanity check)**
- Environments: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Variant types: emotional_pressure, irrelevant_context, misleading_authority, order_permutation, paraphrase, prompt_injection_style, recent_outcome_bias, risk_pressure, unit_scale_change, urgency_pressure
- Base tasks: `90`
- Variants: `435`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Overall robustness metrics

- `paraphrase_consistency_rate`: `1`
- `mean_score_drop`: `1.32169e-18`
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
| adversarial_risk | 75 | 0 | 0 | 0 | 0 | 0 |
| auctions | 75 | 1 | 0 | 0 | 0 | 0 |
| bayesian_games | 75 | 1 | 7.40149e-18 | 0 | 0 | 0 |
| hidden_regimes | 60 | 1 | 0 | 0 | 0 | 0 |
| market_making | 75 | 0 | 0 | 0 | 0 | 0 |
| prediction_markets | 75 | 1 | 0 | 0 | 0 | 0 |

## Variant-type breakdown

| Variant type | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| emotional_pressure | 30 | 0 | 0 | 0 | 0 | 0 |
| irrelevant_context | 75 | 0 | 0 | 0 | 0 | 0 |
| misleading_authority | 75 | 0 | 0 | 0 | 0 | 0 |
| order_permutation | 15 | 0 | 3.70074e-17 | 0 | 0 | 0 |
| paraphrase | 60 | 1 | 0 | 0 | 0 | 0 |
| prompt_injection_style | 30 | 0 | 0 | 0 | 0 | 0 |
| recent_outcome_bias | 45 | 0 | 0 | 0 | 0 | 0 |
| risk_pressure | 60 | 0 | 0 | 0 | 0 | 0 |
| unit_scale_change | 15 | 0 | 0 | 0 | 0 | 0 |
| urgency_pressure | 30 | 0 | 0 | 0 | 0 | 0 |

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
