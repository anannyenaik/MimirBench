# leaderboard_openai_all_envs_direct_tiny__openai_gpt_4_1_mini_direct_all_envs_tiny__direct

- Run ID: `leaderboard_openai_all_envs_direct_tiny__openai_gpt_4_1_mini_direct_all_envs_tiny__direct-20260602T204111`
- Timestamp: `2026-06-02T20:41:11Z`
- Agent: `openai_gpt_4_1_mini_direct_all_envs_tiny::direct` (`direct`)
- Number of tasks: `30`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 5 | 0.84 | 1 | 0 | 0 |
| auctions | 5 | 0.301022 | 0 | 0 | 0 |
| bayesian_games | 5 | 0.708451 | 0.2 | 0 | 0 |
| hidden_regimes | 5 | 0.73678 | 0 | 0 | 0 |
| market_making | 5 | 0.506973 | 0.6 | 0 | 0 |
| prediction_markets | 5 | 0.524835 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.60301`
- Pass rate: `0.3`
- Violation rate: `0.0666667`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1815.12`
- Latency p50 ms: `1748.89`
- Latency p95 ms: `2521.37`

## Cost and Latency

- Total input tokens: `13637`
- Total output tokens: `2623`
- Total tokens: `16260`
- Estimated total cost (USD): `0.00965` (estimated over 30 model tasks)
- Mean latency ms: `1815.12`
- p50 latency ms: `1748.89`
- p95 latency ms: `2521.37`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.925`
- `action_optimality`: `0.291455`
- `adverse_selection_penalty`: `0.169769`
- `answer_sum`: `1`
- `calibration_proxy`: `0.64456`
- `correct_constraint_identified`: `0.2`
- `expected_value_abs_error`: `2.59367`
- `expected_value_error`: `0.103849`
- `expected_value_rel_error`: `3.93746`
- `fair_probability_error`: `0.0580798`
- `inventory_risk_score`: `0.46`
- `posterior_l1_error`: `0.554769`
- `posterior_max_error`: `0.291549`
- `posterior_tv_error`: `0.277384`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0.141135`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.2`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.579722`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.437122` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.404806` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.889223` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.842596` violations=`[]` error=`None`
- `auctions/auctions-123` score=`0` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
