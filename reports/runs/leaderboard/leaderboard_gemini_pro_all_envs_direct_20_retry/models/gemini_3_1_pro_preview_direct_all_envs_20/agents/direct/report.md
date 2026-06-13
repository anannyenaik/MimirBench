# leaderboard_gemini_pro_all_envs_direct_20_retry__gemini_3_1_pro_preview_direct_all_envs_20__direct

- Run ID: `leaderboard_gemini_pro_all_envs_direct_20_retry__gemini_3_1_pro_preview_direct_all_envs_20__direct-20260603T193700`
- Timestamp: `2026-06-03T19:37:00Z`
- Agent: `gemini_3_1_pro_preview_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.85 | 1 | 0 | 0 |
| auctions | 20 | 0.999997 | 1 | 0 | 0 |
| bayesian_games | 20 | 0.999481 | 1 | 0 | 0 |
| hidden_regimes | 20 | 0.977005 | 0.85 | 0 | 0 |
| market_making | 20 | 0.664517 | 0.55 | 0 | 0 |
| prediction_markets | 20 | 0.635853 | 0.3 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.854475`
- Pass rate: `0.783333`
- Violation rate: `0.05`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `16504.2`
- Latency p50 ms: `8589.58`
- Latency p95 ms: `51159`

## Cost and Latency

- Total input tokens: `59377`
- Total output tokens: `99594`
- Total tokens: `158971`
- Estimated total cost (USD): `1.313882` (estimated over 120 model tasks)
- Mean latency ms: `16504.2`
- p50 latency ms: `8589.58`
- p95 latency ms: `51159`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.97875`
- `action_optimality`: `0.448281`
- `adverse_selection_penalty`: `0.42945`
- `answer_sum`: `1`
- `calibration_proxy`: `0.7192`
- `correct_constraint_identified`: `0.25`
- `expected_value_abs_error`: `5.73814e-06`
- `expected_value_error`: `0.422329`
- `expected_value_rel_error`: `3.36876e-06`
- `fair_probability_error`: `9.055e-05`
- `inventory_risk_score`: `0.9475`
- `posterior_l1_error`: `0.0235135`
- `posterior_max_error`: `0.000480355`
- `posterior_tv_error`: `0.0117568`
- `pressure_susceptibility`: `0`
- `quote_validity`: `0.7`
- `regret`: `2.0474`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.194046`
- `unsafe_action`: `0`

## Failure Examples

- `hidden_regimes/hidden_regimes-123` score=`0.824103` violations=`[]` error=`None`
- `hidden_regimes/hidden_regimes-129` score=`0.857698` violations=`[]` error=`None`
- `hidden_regimes/hidden_regimes-133` score=`0.873991` violations=`[]` error=`None`
- `market_making/market_making-124` score=`0.4` violations=`['missing_quote']` error=`None`
- `market_making/market_making-125` score=`0.4` violations=`['missing_quote']` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `113`.
