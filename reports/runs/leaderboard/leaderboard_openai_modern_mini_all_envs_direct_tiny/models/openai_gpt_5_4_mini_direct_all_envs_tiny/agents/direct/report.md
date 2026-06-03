# leaderboard_openai_modern_mini_all_envs_direct_tiny__openai_gpt_5_4_mini_direct_all_envs_tiny__direct

- Run ID: `leaderboard_openai_modern_mini_all_envs_direct_tiny__openai_gpt_5_4_mini_direct_all_envs_tiny__direct-20260602T210801`
- Timestamp: `2026-06-02T21:08:01Z`
- Agent: `openai_gpt_5_4_mini_direct_all_envs_tiny::direct` (`direct`)
- Number of tasks: `30`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 5 | 0.84 | 1 | 0 | 0 |
| auctions | 5 | 0 | 0 | 0 | 0 |
| bayesian_games | 5 | 0.739376 | 0.4 | 0 | 0 |
| hidden_regimes | 5 | 0.791247 | 0 | 0 | 0 |
| market_making | 5 | 0.594964 | 0.4 | 0 | 0 |
| prediction_markets | 5 | 0.296165 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.543625`
- Pass rate: `0.3`
- Violation rate: `0.0333333`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1433.96`
- Latency p50 ms: `1205.25`
- Latency p95 ms: `2751.56`

## Cost and Latency

- Total input tokens: `13607`
- Total output tokens: `2765`
- Total tokens: `16372`
- Estimated total cost (USD): `0.022646` (estimated over 30 model tasks)
- Mean latency ms: `1433.96`
- p50 latency ms: `1205.25`
- p95 latency ms: `2751.56`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.835`
- `action_optimality`: `0.121584`
- `adverse_selection_penalty`: `0.159712`
- `answer_sum`: `1`
- `calibration_proxy`: `0.78856`
- `correct_constraint_identified`: `0.2`
- `expected_value_abs_error`: `17.4805`
- `expected_value_error`: `0.177705`
- `expected_value_rel_error`: `37.4891`
- `fair_probability_error`: `0.16048`
- `inventory_risk_score`: `0.46`
- `posterior_l1_error`: `0.469377`
- `posterior_max_error`: `0.260624`
- `posterior_tv_error`: `0.234688`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `3.29007`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.1`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.352793`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.739122` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.199245` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.781212` violations=`[]` error=`None`
- `auctions/auctions-123` score=`0` violations=`[]` error=`None`
- `auctions/auctions-124` score=`0` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
