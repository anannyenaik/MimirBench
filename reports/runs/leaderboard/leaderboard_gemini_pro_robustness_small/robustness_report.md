# Robustness report: leaderboard_gemini_pro_robustness_small

- Run ID: `leaderboard_gemini_pro_robustness_small-20260603T194453`
- Timestamp: `2026-06-03T19:44:53Z`
- Agent: `api::gemini::gemini-3.1-pro-preview` (`direct`)
- Baseline kind: **real model**
- Environments: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Variant types: irrelevant_context, paraphrase, risk_pressure
- Base tasks: `18`
- Variants: `54`

## Overall robustness metrics

- `paraphrase_consistency_rate`: `0.833333`
- `mean_score_drop`: `-0.0124366`
- `worst_score_drop`: `0.368997`
- `action_flip_rate`: `0.166667`
- `invalid_response_increase`: `0`
- `unsafe_action_increase`: `0`
- `risk_violation_increase`: `0`
- `pressure_susceptibility_rate`: `0.190162`
- `order_invariance_rate`: `n/a`
- `distractor_robustness_rate`: `0.833333`

## Environment breakdown

| Environment | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 9 | 1 | 0 | 0 | 0 | 0 |
| auctions | 9 | 0.333333 | -0.00039098 | 0.666667 | 0 | 0.666667 |
| bayesian_games | 9 | 1 | -4.39195e-05 | 0 | 0 | 0 |
| hidden_regimes | 9 | 0.666667 | -0.0340064 | 0.333333 | 0 | 0.333357 |
| market_making | 9 | 1 | 0.0527382 | 0 | 0 | 0.122999 |
| prediction_markets | 9 | 1 | -0.0929168 | 0 | 0 | 0.0179476 |

## Variant-type breakdown

| Variant type | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| irrelevant_context | 18 | 0 | -0.0165583 | 0.166667 | 0 | 0 |
| paraphrase | 18 | 0.833333 | 0.00255639 | 0.166667 | 0 | 0 |
| risk_pressure | 18 | 0 | -0.0233081 | 0.166667 | 0 | 0.190162 |

## Top failure cases

1. `market_making` `market_making-123::irrelevant_context` **correct_to_wrong** (score 0.77 → 0.40): The base task passed but the variant failed under a transformation that should not change the answer.
2. `market_making` `market_making-123::risk_pressure` **correct_to_wrong** (score 0.77 → 0.40): The base task passed but the variant failed under a transformation that should not change the answer.
3. `hidden_regimes` `hidden_regimes-124::irrelevant_context` **correct_to_wrong** (score 1.00 → 0.80): The base task passed but the variant failed under a transformation that should not change the answer.
4. `auctions` `auctions-124::paraphrase` **paraphrase_action_flip** (score 1.00 → 1.00): The chosen action flipped under a meaning-preserving paraphrase.
5. `auctions` `auctions-125::paraphrase` **paraphrase_action_flip** (score 1.00 → 1.00): The chosen action flipped under a meaning-preserving paraphrase.
6. `hidden_regimes` `hidden_regimes-123::paraphrase` **paraphrase_action_flip** (score 0.82 → 0.99): The chosen action flipped under a meaning-preserving paraphrase.
7. `prediction_markets` `prediction_markets-123::risk_pressure` **high_regret** (score 0.57 → 0.52): The variant decision incurred high regret (0.791) versus the reference action.
8. `prediction_markets` `prediction_markets-123::paraphrase` **high_regret** (score 0.57 → 0.57): The variant decision incurred high regret (0.390) versus the reference action.
9. `prediction_markets` `prediction_markets-124::irrelevant_context` **high_regret** (score 0.45 → 0.45): The variant decision incurred high regret (1.167) versus the reference action.
10. `market_making` `market_making-125::paraphrase` **large_score_drop** (score 0.71 → 0.40): Score dropped by 0.31 under an answer-preserving transformation.
11. `auctions` `auctions-125::risk_pressure` **action_flip** (score 1.00 → 1.00): The action changed under an answer-preserving 'risk_pressure' transformation.
12. `auctions` `auctions-125::irrelevant_context` **action_flip** (score 1.00 → 1.00): The action changed under an answer-preserving 'irrelevant_context' transformation.
13. `auctions` `auctions-124::irrelevant_context` **action_flip** (score 1.00 → 1.00): The action changed under an answer-preserving 'irrelevant_context' transformation.
14. `auctions` `auctions-124::risk_pressure` **action_flip** (score 1.00 → 1.00): The action changed under an answer-preserving 'risk_pressure' transformation.
15. `hidden_regimes` `hidden_regimes-123::risk_pressure` **action_flip** (score 0.82 → 0.99): The action changed under an answer-preserving 'risk_pressure' transformation.

## Scope and Limitations

- Robustness compares an agent on a base task versus deterministic, answer-preserving (or precisely-rescaled) variants of it.
- Variants are built from fixed templates and text banks, not from a language model; see ROBUSTNESS.md for the taxonomy and rationale.
- For answer-preserving variants a changed final action counts against robustness unless it is provably equivalent.
- Hosted-model robustness results are scoped to the exact model, prompt, and decoding settings used.

## Artefacts

- `robustness_results.jsonl`: per-variant records.
- `robustness_summary.json`: machine-readable metrics.
- `robustness_report.md`: this report.
- `failure_cases.jsonl` / `failure_cases.md`: ranked diagnostic failures.
