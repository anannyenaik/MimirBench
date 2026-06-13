# leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_4_direct_all_envs_20__direct

- Run ID: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_4_direct_all_envs_20__direct-20260602T235149`
- Timestamp: `2026-06-02T23:51:49Z`
- Agent: `openai_gpt_5_4_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.85 | 1 | 0 | 0 |
| auctions | 20 | 0.193458 | 0.1 | 0 | 0 |
| bayesian_games | 20 | 0.883559 | 0.3 | 0 | 0 |
| hidden_regimes | 20 | 0.848995 | 0.25 | 0 | 0 |
| market_making | 20 | 0.772774 | 0.7 | 0 | 0 |
| prediction_markets | 20 | 0.428989 | 0.2 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.662963`
- Pass rate: `0.425`
- Violation rate: `0.0583333`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `2566`
- Latency p50 ms: `2356.81`
- Latency p95 ms: `3622.97`

## Cost and Latency

- Total input tokens: `54781`
- Total output tokens: `12622`
- Total tokens: `67403`
- Estimated total cost (USD): `0.32627` (estimated over 120 model tasks)
- Mean latency ms: `2566`
- p50 latency ms: `2356.81`
- p95 latency ms: `3622.97`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.895`
- `action_optimality`: `0.237682`
- `adverse_selection_penalty`: `0.286769`
- `answer_sum`: `1`
- `calibration_proxy`: `0.83052`
- `correct_constraint_identified`: `0.25`
- `expected_value_abs_error`: `3.94889`
- `expected_value_error`: `0.667759`
- `expected_value_rel_error`: `1.93972`
- `fair_probability_error`: `0.0199906`
- `inventory_risk_score`: `0.915`
- `posterior_l1_error`: `0.267446`
- `posterior_max_error`: `0.115834`
- `posterior_tv_error`: `0.133723`
- `pressure_susceptibility`: `0`
- `quote_validity`: `0.85`
- `regret`: `2.85095`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.1`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.372696`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.850616` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.508952` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.821839` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.890469` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-130` score=`0.878411` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
