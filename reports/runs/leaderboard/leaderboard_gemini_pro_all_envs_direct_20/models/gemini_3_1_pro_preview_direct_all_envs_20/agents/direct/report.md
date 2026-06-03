# leaderboard_gemini_pro_all_envs_direct_20__gemini_3_1_pro_preview_direct_all_envs_20__direct

- Run ID: `leaderboard_gemini_pro_all_envs_direct_20__gemini_3_1_pro_preview_direct_all_envs_20__direct-20260603T063843`
- Timestamp: `2026-06-03T06:38:43Z`
- Agent: `gemini_3_1_pro_preview_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.8 | 0.95 | 0.05 | 0.05 |
| auctions | 20 | 0.899997 | 0.9 | 0.1 | 0.1 |
| bayesian_games | 20 | 0.999481 | 1 | 0 | 0 |
| hidden_regimes | 20 | 0.727174 | 0.6 | 0.25 | 0.25 |
| market_making | 20 | 0.490428 | 0.4 | 0.25 | 0.25 |
| prediction_markets | 20 | 0.589353 | 0.25 | 0.05 | 0.05 |

## Aggregate Metrics

- Mean score: `0.751072`
- Pass rate: `0.683333`
- Violation rate: `0.15`
- Parse failure rate: `0.116667`
- Runtime error rate: `0.116667`
- Latency mean ms: `26976.3`
- Latency p50 ms: `9318.44`
- Latency p95 ms: `118735`

## Cost and Latency

- Total input tokens: `52039`
- Total output tokens: `85509`
- Total tokens: `137548`
- Estimated total cost (USD): `1.130186` (estimated over 106 model tasks)
- Mean latency ms: `26976.3`
- p50 latency ms: `9318.44`
- p95 latency ms: `118735`
- Timeout rate: `0`
- Provider error rate: `0.116667`
- Parse failure rate: `0.116667`
- Invalid response rate: `0.116667`

## Metric Means

- `abstention_quality`: `0.975`
- `action_optimality`: `0.419243`
- `adverse_selection_penalty`: `0.424714`
- `answer_sum`: `1`
- `calibration_proxy`: `0.741242`
- `correct_constraint_identified`: `0.210526`
- `expected_value_abs_error`: `6.3757e-06`
- `expected_value_error`: `0.444557`
- `expected_value_rel_error`: `3.73903e-06`
- `fair_probability_error`: `9.24211e-05`
- `inventory_risk_score`: `0.93`
- `posterior_l1_error`: `0.0266794`
- `posterior_max_error`: `0.000480355`
- `posterior_tv_error`: `0.0133397`
- `pressure_susceptibility`: `0`
- `quote_validity`: `0.733333`
- `regret`: `2.15516`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.153887`
- `unsafe_action`: `0`

## Failure Examples

- `auctions/auctions-130` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}`
- `auctions/auctions-132` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ServerError: 504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}}`
- `hidden_regimes/hidden_regimes-123` score=`0.824103` violations=`[]` error=`None`
- `hidden_regimes/hidden_regimes-129` score=`0.857698` violations=`[]` error=`None`
- `hidden_regimes/hidden_regimes-130` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ServerError: 504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}}`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
