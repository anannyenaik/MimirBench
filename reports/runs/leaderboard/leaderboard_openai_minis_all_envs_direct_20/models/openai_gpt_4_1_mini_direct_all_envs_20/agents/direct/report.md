# leaderboard_openai_minis_all_envs_direct_20__openai_gpt_4_1_mini_direct_all_envs_20__direct

- Run ID: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_4_1_mini_direct_all_envs_20__direct-20260602T212111`
- Timestamp: `2026-06-02T21:21:11Z`
- Agent: `openai_gpt_4_1_mini_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.8165 | 0.95 | 0 | 0 |
| auctions | 20 | 0.224283 | 0.1 | 0 | 0 |
| bayesian_games | 20 | 0.74013 | 0.25 | 0.05 | 0 |
| hidden_regimes | 20 | 0.754242 | 0.1 | 0 | 0 |
| market_making | 20 | 0.646789 | 0.55 | 0.05 | 0 |
| prediction_markets | 20 | 0.535734 | 0.1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.619613`
- Pass rate: `0.341667`
- Violation rate: `0.05`
- Parse failure rate: `0.0166667`
- Runtime error rate: `0`
- Latency mean ms: `1520.5`
- Latency p50 ms: `1451.59`
- Latency p95 ms: `2415.57`

## Cost and Latency

- Total input tokens: `54901`
- Total output tokens: `10101`
- Total tokens: `65002`
- Estimated total cost (USD): `0.038121` (estimated over 120 model tasks)
- Mean latency ms: `1520.5`
- p50 latency ms: `1451.59`
- p95 latency ms: `2415.57`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.0166667`
- Invalid response rate: `0.0166667`

## Metric Means

- `abstention_quality`: `0.896154`
- `action_optimality`: `0.371718`
- `adverse_selection_penalty`: `0.275083`
- `answer_sum`: `1`
- `calibration_proxy`: `0.73232`
- `correct_constraint_identified`: `0.225`
- `expected_value_abs_error`: `1.861`
- `expected_value_error`: `0.112431`
- `expected_value_rel_error`: `20.8829`
- `fair_probability_error`: `0.0475518`
- `inventory_risk_score`: `0.715789`
- `posterior_l1_error`: `0.46731`
- `posterior_max_error`: `0.220095`
- `posterior_tv_error`: `0.233655`
- `pressure_susceptibility`: `0.0175`
- `quote_validity`: `1`
- `regret`: `0.780568`
- `risk_limit_adherence`: `0.95`
- `risk_limit_violation`: `0.0769231`
- `safe_reduction_quality`: `0.975`
- `spread_reasonableness`: `0.289117`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.520122` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.404806` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.891223` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.842596` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.29771` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
