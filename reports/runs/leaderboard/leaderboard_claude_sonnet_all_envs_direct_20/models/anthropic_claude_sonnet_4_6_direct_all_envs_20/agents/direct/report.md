# leaderboard_claude_sonnet_all_envs_direct_20__anthropic_claude_sonnet_4_6_direct_all_envs_20__direct

- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20__anthropic_claude_sonnet_4_6_direct_all_envs_20__direct-20260603T024516`
- Timestamp: `2026-06-03T02:45:16Z`
- Agent: `anthropic_claude_sonnet_4_6_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.835 | 1 | 0 | 0 |
| auctions | 20 | 0.149991 | 0.15 | 0.85 | 0 |
| bayesian_games | 20 | 0.599664 | 0.6 | 0.4 | 0 |
| hidden_regimes | 20 | 0 | 0 | 1 | 0 |
| market_making | 20 | 0.479658 | 0.45 | 0.45 | 0 |
| prediction_markets | 20 | 0.148823 | 0.15 | 0.85 | 0 |

## Aggregate Metrics

- Mean score: `0.368856`
- Pass rate: `0.391667`
- Violation rate: `0.591667`
- Parse failure rate: `0.591667`
- Runtime error rate: `0`
- Latency mean ms: `7705.27`
- Latency p50 ms: `8270.36`
- Latency p95 ms: `11452.1`

## Cost and Latency

- Total input tokens: `59811`
- Total output tokens: `48473`
- Total tokens: `108284`
- Estimated total cost (USD): `0.906528` (estimated over 120 model tasks)
- Mean latency ms: `7705.27`
- p50 latency ms: `8270.36`
- p95 latency ms: `11452.1`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.591667`
- Invalid response rate: `0.591667`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `1`
- `adverse_selection_penalty`: `0.133158`
- `answer_sum`: `1.00002`
- `calibration_proxy`: `0.926133`
- `correct_constraint_identified`: `0.175`
- `expected_value_abs_error`: `4.46023e-05`
- `expected_value_error`: `0.000133333`
- `expected_value_rel_error`: `6.27582e-05`
- `fair_probability_error`: `5.8e-05`
- `inventory_risk_score`: `0.909091`
- `posterior_l1_error`: `0.00112056`
- `posterior_max_error`: `0.000501839`
- `posterior_tv_error`: `0.000560279`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.574028`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-125` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-127` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-128` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-132` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-136` score=`0` violations=`['no_valid_answer']` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
