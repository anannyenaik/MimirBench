# leaderboard_openai_minis_all_envs_direct_20__openai_gpt_5_4_mini_direct_all_envs_20__direct

- Run ID: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_5_4_mini_direct_all_envs_20__direct-20260602T212421`
- Timestamp: `2026-06-02T21:24:21Z`
- Agent: `openai_gpt_5_4_mini_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.825 | 1 | 0 | 0 |
| auctions | 20 | 0.0326323 | 0 | 0 | 0 |
| bayesian_games | 20 | 0.807899 | 0.25 | 0 | 0 |
| hidden_regimes | 20 | 0.801071 | 0.05 | 0 | 0 |
| market_making | 20 | 0.719257 | 0.6 | 0 | 0 |
| prediction_markets | 20 | 0.482639 | 0.1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.611416`
- Pass rate: `0.333333`
- Violation rate: `0.0166667`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1308.37`
- Latency p50 ms: `1146.07`
- Latency p95 ms: `1821.88`

## Cost and Latency

- Total input tokens: `54781`
- Total output tokens: `11140`
- Total tokens: `65921`
- Estimated total cost (USD): `0.091214` (estimated over 120 model tasks)
- Mean latency ms: `1308.37`
- p50 latency ms: `1146.07`
- p95 latency ms: `1821.88`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.865`
- `action_optimality`: `0.427853`
- `adverse_selection_penalty`: `0.173306`
- `answer_sum`: `1.00003`
- `calibration_proxy`: `0.81438`
- `correct_constraint_identified`: `0.125`
- `expected_value_abs_error`: `14.001`
- `expected_value_error`: `0.141958`
- `expected_value_rel_error`: `302.845`
- `fair_probability_error`: `0.108749`
- `inventory_risk_score`: `0.78`
- `posterior_l1_error`: `0.391031`
- `posterior_max_error`: `0.188677`
- `posterior_tv_error`: `0.195515`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0.917249`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.05`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.364138`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.707207` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.196331` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.721471` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.735467` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-130` score=`0.695508` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
