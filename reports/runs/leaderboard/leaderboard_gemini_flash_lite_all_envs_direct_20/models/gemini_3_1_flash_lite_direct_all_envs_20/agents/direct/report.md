# leaderboard_gemini_flash_lite_all_envs_direct_20__gemini_3_1_flash_lite_direct_all_envs_20__direct

- Run ID: `leaderboard_gemini_flash_lite_all_envs_direct_20__gemini_3_1_flash_lite_direct_all_envs_20__direct-20260603T052929`
- Timestamp: `2026-06-03T05:29:29Z`
- Agent: `gemini_3_1_flash_lite_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.8 | 0.95 | 0.05 | 0 |
| auctions | 20 | 0.197183 | 0.15 | 0.1 | 0 |
| bayesian_games | 20 | 0.806853 | 0.2 | 0 | 0 |
| hidden_regimes | 20 | 0.86787 | 0.2 | 0 | 0 |
| market_making | 20 | 0.657497 | 0.65 | 0 | 0 |
| prediction_markets | 20 | 0.591715 | 0.25 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.65352`
- Pass rate: `0.4`
- Violation rate: `0.0666667`
- Parse failure rate: `0.0166667`
- Runtime error rate: `0`
- Latency mean ms: `1115.12`
- Latency p50 ms: `736.324`
- Latency p95 ms: `904.635`

## Cost and Latency

- Total input tokens: `59377`
- Total output tokens: `14179`
- Total tokens: `73556`
- Estimated total cost (USD): `0.036121` (estimated over 120 model tasks)
- Mean latency ms: `1115.12`
- p50 latency ms: `736.324`
- p95 latency ms: `904.635`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.0166667`
- Invalid response rate: `0.025`

## Metric Means

- `abstention_quality`: `0.87625`
- `action_optimality`: `0.393447`
- `adverse_selection_penalty`: `0.199189`
- `answer_sum`: `0.99`
- `calibration_proxy`: `0.778`
- `correct_constraint_identified`: `0.210526`
- `expected_value_abs_error`: `36.9788`
- `expected_value_error`: `0.112091`
- `expected_value_rel_error`: `19.9279`
- `fair_probability_error`: `0.0433937`
- `inventory_risk_score`: `0.7`
- `posterior_l1_error`: `0.325277`
- `posterior_max_error`: `0.19194`
- `posterior_tv_error`: `0.162638`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0.264899`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.125`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.539645`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.872321` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.280729` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.706646` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.696445` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-129` score=`0.91095` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
