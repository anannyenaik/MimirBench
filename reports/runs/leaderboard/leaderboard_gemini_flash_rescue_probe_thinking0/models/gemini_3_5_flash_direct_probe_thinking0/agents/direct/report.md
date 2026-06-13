# leaderboard_gemini_flash_rescue_probe_thinking0__gemini_3_5_flash_direct_probe_thinking0__direct

- Run ID: `leaderboard_gemini_flash_rescue_probe_thinking0__gemini_3_5_flash_direct_probe_thinking0__direct-20260603T054140`
- Timestamp: `2026-06-03T05:41:40Z`
- Agent: `gemini_3_5_flash_direct_probe_thinking0::direct` (`direct`)
- Number of tasks: `6`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 1 | 0.8 | 1 | 0 | 0 |
| auctions | 1 | 0.999994 | 1 | 0 | 0 |
| bayesian_games | 1 | 0.876982 | 0 | 0 | 0 |
| hidden_regimes | 1 | 0.856897 | 0 | 0 | 0 |
| market_making | 1 | 0.642692 | 0 | 0 | 0 |
| prediction_markets | 1 | 0.795958 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.828754`
- Pass rate: `0.333333`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1829.81`
- Latency p50 ms: `1729.17`
- Latency p95 ms: `2640.78`

## Cost and Latency

- Total input tokens: `2915`
- Total output tokens: `776`
- Total tokens: `3691`
- Estimated total cost (USD): `0.011357` (estimated over 6 model tasks)
- Mean latency ms: `1829.81`
- p50 latency ms: `1729.17`
- p95 latency ms: `2640.78`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `0.735243`
- `adverse_selection_penalty`: `0.439634`
- `answer_sum`: `1`
- `calibration_proxy`: `0.8154`
- `correct_constraint_identified`: `0`
- `expected_value_abs_error`: `6.83605e-06`
- `expected_value_error`: `0.200347`
- `expected_value_rel_error`: `6.20496e-06`
- `fair_probability_error`: `0.00015`
- `inventory_risk_score`: `0.5`
- `posterior_l1_error`: `0.266121`
- `posterior_max_error`: `0.123018`
- `posterior_tv_error`: `0.133061`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0.109166`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.168185`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0.876982` violations=`[]` error=`None`
- `hidden_regimes/hidden_regimes-123` score=`0.856897` violations=`[]` error=`None`
- `market_making/market_making-123` score=`0.642692` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-123` score=`0.795958` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
