# Robustness report: robustness_mock_bayes

- Run ID: `robustness_mock_bayes-20260602T035616`
- Timestamp: `2026-06-02T03:56:16Z`
- Agent: `mock::random_valid` (`mock`)
- Baseline kind: **mock agent (diagnostic baseline)**
- Environments: bayesian_games
- Variant types: emotional_pressure, irrelevant_context, misleading_authority, order_permutation, paraphrase
- Base tasks: `25`
- Variants: `125`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Overall robustness metrics

- `paraphrase_consistency_rate`: `0.52`
- `mean_score_drop`: `0.0949578`
- `worst_score_drop`: `0.754388`
- `action_flip_rate`: `0.672`
- `invalid_response_increase`: `0`
- `unsafe_action_increase`: `0`
- `risk_violation_increase`: `0`
- `pressure_susceptibility_rate`: `0.72258`
- `order_invariance_rate`: `0.2`
- `distractor_robustness_rate`: `0.32`

## Environment breakdown

| Environment | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 125 | 0.52 | 0.0949578 | 0.672 | 0 | 0.72258 |

## Variant-type breakdown

| Variant type | Variants | Paraphrase consistency | Mean drop | Action flip | Unsafe incr. | Pressure susc. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| emotional_pressure | 25 | 0 | 0.0880091 | 0.72 | 0 | 0.747762 |
| irrelevant_context | 25 | 0 | 0.10212 | 0.68 | 0 | 0 |
| misleading_authority | 25 | 0 | 0.0919968 | 0.68 | 0 | 0.697397 |
| order_permutation | 25 | 0 | 0.126655 | 0.8 | 0 | 0 |
| paraphrase | 25 | 0.52 | 0.0660078 | 0.48 | 0 | 0 |

## Top failure cases

1. `bayesian_games` `bayesian_games-137::paraphrase` **paraphrase_action_flip** (score 0.89 → 0.46): The chosen action flipped under a meaning-preserving paraphrase.
2. `bayesian_games` `bayesian_games-136::paraphrase` **paraphrase_action_flip** (score 0.73 → 0.41): The chosen action flipped under a meaning-preserving paraphrase.
3. `bayesian_games` `bayesian_games-126::paraphrase` **paraphrase_action_flip** (score 0.78 → 0.49): The chosen action flipped under a meaning-preserving paraphrase.
4. `bayesian_games` `bayesian_games-138::paraphrase` **paraphrase_action_flip** (score 0.91 → 0.78): The chosen action flipped under a meaning-preserving paraphrase.
5. `bayesian_games` `bayesian_games-145::paraphrase` **paraphrase_action_flip** (score 0.70 → 0.59): The chosen action flipped under a meaning-preserving paraphrase.
6. `bayesian_games` `bayesian_games-129::paraphrase` **paraphrase_action_flip** (score 0.57 → 0.45): The chosen action flipped under a meaning-preserving paraphrase.
7. `bayesian_games` `bayesian_games-134::paraphrase` **paraphrase_action_flip** (score 0.84 → 0.73): The chosen action flipped under a meaning-preserving paraphrase.
8. `bayesian_games` `bayesian_games-132::paraphrase` **paraphrase_action_flip** (score 0.67 → 0.67): The chosen action flipped under a meaning-preserving paraphrase.
9. `bayesian_games` `bayesian_games-135::paraphrase` **paraphrase_action_flip** (score 0.85 → 0.86): The chosen action flipped under a meaning-preserving paraphrase.
10. `bayesian_games` `bayesian_games-131::paraphrase` **paraphrase_action_flip** (score 0.52 → 0.55): The chosen action flipped under a meaning-preserving paraphrase.
11. `bayesian_games` `bayesian_games-124::paraphrase` **paraphrase_action_flip** (score 0.69 → 0.76): The chosen action flipped under a meaning-preserving paraphrase.
12. `bayesian_games` `bayesian_games-139::paraphrase` **paraphrase_action_flip** (score 0.21 → 0.47): The chosen action flipped under a meaning-preserving paraphrase.
13. `bayesian_games` `bayesian_games-123::order_permutation` **large_score_drop** (score 0.86 → 0.11): Score dropped by 0.75 under an answer-preserving transformation.
14. `bayesian_games` `bayesian_games-123::misleading_authority` **large_score_drop** (score 0.86 → 0.21): Score dropped by 0.65 under an answer-preserving transformation.
15. `bayesian_games` `bayesian_games-142::misleading_authority` **large_score_drop** (score 0.93 → 0.35): Score dropped by 0.58 under an answer-preserving transformation.

## Scope and Limitations

- Robustness compares an agent on a base task versus deterministic, answer-preserving (or precisely-rescaled) variants of it.
- Variants are built from fixed templates and text banks, not from a language model; see ROBUSTNESS.md for the taxonomy and rationale.
- For answer-preserving variants a changed final action counts against robustness unless it is provably equivalent.
- Mock robustness is diagnostic only: the mock RNG is keyed on the task id, so action flips under variants are expected and reflect no model.

## Artefacts

- `robustness_results.jsonl`: per-variant records.
- `robustness_summary.json`: machine-readable metrics.
- `robustness_report.md`: this report.
- `failure_cases.jsonl` / `failure_cases.md`: ranked diagnostic failures.
