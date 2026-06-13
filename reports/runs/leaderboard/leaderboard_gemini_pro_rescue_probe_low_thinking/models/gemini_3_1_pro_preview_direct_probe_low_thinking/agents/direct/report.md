# leaderboard_gemini_pro_rescue_probe_low_thinking__gemini_3_1_pro_preview_direct_probe_low_thinking__direct

- Run ID: `leaderboard_gemini_pro_rescue_probe_low_thinking__gemini_3_1_pro_preview_direct_probe_low_thinking__direct-20260603T063601`
- Timestamp: `2026-06-03T06:36:01Z`
- Agent: `gemini_3_1_pro_preview_direct_probe_low_thinking::direct` (`direct`)
- Number of tasks: `6`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 1 | 0.8 | 1 | 0 | 0 |
| auctions | 1 | 1 | 1 | 0 | 0 |
| bayesian_games | 1 | 0.999507 | 1 | 0 | 0 |
| hidden_regimes | 1 | 0.824103 | 0 | 0 | 0 |
| market_making | 1 | 0.768997 | 1 | 0 | 0 |
| prediction_markets | 1 | 0.493182 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.814298`
- Pass rate: `0.666667`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `7671.46`
- Latency p50 ms: `6868.99`
- Latency p95 ms: `11471.9`

## Cost and Latency

- Total input tokens: `2915`
- Total output tokens: `3577`
- Total tokens: `6492`
- Estimated total cost (USD): `0.048754` (estimated over 6 model tasks)
- Mean latency ms: `7671.46`
- p50 latency ms: `6868.99`
- p95 latency ms: `11471.9`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `0.179488`
- `adverse_selection_penalty`: `0.411515`
- `answer_sum`: `1`
- `calibration_proxy`: `0.9846`
- `correct_constraint_identified`: `0`
- `expected_value_abs_error`: `5e-11`
- `expected_value_error`: `1.66065`
- `expected_value_rel_error`: `4.53841e-11`
- `fair_probability_error`: `0.00015`
- `inventory_risk_score`: `1`
- `posterior_l1_error`: `0.176389`
- `posterior_max_error`: `0.00049255`
- `posterior_tv_error`: `0.0881947`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `1.04853`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.153621`
- `unsafe_action`: `0`

## Failure Examples

- `hidden_regimes/hidden_regimes-123` score=`0.824103` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-123` score=`0.493182` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
