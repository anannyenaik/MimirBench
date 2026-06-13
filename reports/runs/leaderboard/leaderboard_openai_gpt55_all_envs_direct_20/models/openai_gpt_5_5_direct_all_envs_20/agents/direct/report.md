# leaderboard_openai_gpt55_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct

- Run ID: `leaderboard_openai_gpt55_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct-20260603T001730`
- Timestamp: `2026-06-03T00:17:30Z`
- Agent: `openai_gpt_5_5_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.85 | 1 | 0 | 0 |
| auctions | 20 | 0.2 | 0.2 | 0.8 | 0 |
| bayesian_games | 20 | 0.0499938 | 0.05 | 0.95 | 0 |
| hidden_regimes | 20 | 0 | 0 | 1 | 0 |
| market_making | 20 | 0.13 | 0.05 | 0.75 | 0 |
| prediction_markets | 20 | 0.04895 | 0.05 | 0.95 | 0 |

## Aggregate Metrics

- Mean score: `0.213157`
- Pass rate: `0.225`
- Violation rate: `0.775`
- Parse failure rate: `0.741667`
- Runtime error rate: `0`
- Latency mean ms: `10784.7`
- Latency p50 ms: `11993.4`
- Latency p95 ms: `14242.2`

## Cost and Latency

- Total input tokens: `54781`
- Total output tokens: `53477`
- Total tokens: `108258`
- Estimated total cost (USD): `1.878215` (estimated over 120 model tasks)
- Mean latency ms: `10784.7`
- p50 latency ms: `11993.4`
- p95 latency ms: `14242.2`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.741667`
- Invalid response rate: `0.741667`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `1`
- `adverse_selection_penalty`: `0.8`
- `answer_sum`: `1`
- `calibration_proxy`: `0.79`
- `correct_constraint_identified`: `0.25`
- `expected_value_abs_error`: `4.25007e-17`
- `expected_value_error`: `0`
- `expected_value_rel_error`: `1.28658e-16`
- `fair_probability_error`: `0`
- `inventory_risk_score`: `1`
- `posterior_l1_error`: `0.000248043`
- `posterior_max_error`: `0.000124022`
- `posterior_tv_error`: `0.000124022`
- `pressure_susceptibility`: `0`
- `quote_validity`: `0.2`
- `regret`: `0`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.2`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-124` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-125` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-127` score=`0` violations=`['no_valid_answer']` error=`None`
- `bayesian_games/bayesian_games-128` score=`0` violations=`['no_valid_answer']` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
