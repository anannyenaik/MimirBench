# leaderboard_gemini_flash_all_envs_direct_20_thinking0__gemini_3_5_flash_direct_all_envs_20_thinking0__direct

- Run ID: `leaderboard_gemini_flash_all_envs_direct_20_thinking0__gemini_3_5_flash_direct_all_envs_20_thinking0__direct-20260603T054317`
- Timestamp: `2026-06-03T05:43:17Z`
- Agent: `gemini_3_5_flash_direct_all_envs_20_thinking0::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.88 | 1 | 0 | 0 |
| auctions | 20 | 0.495045 | 0.25 | 0.05 | 0 |
| bayesian_games | 20 | 0.860836 | 0.3 | 0 | 0 |
| hidden_regimes | 20 | 0.871691 | 0.15 | 0 | 0 |
| market_making | 20 | 0.782985 | 0.75 | 0 | 0 |
| prediction_markets | 20 | 0.581761 | 0.2 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.745386`
- Pass rate: `0.441667`
- Violation rate: `0.025`
- Parse failure rate: `0.00833333`
- Runtime error rate: `0`
- Latency mean ms: `1651.8`
- Latency p50 ms: `1573.44`
- Latency p95 ms: `1985.39`

## Cost and Latency

- Total input tokens: `59377`
- Total output tokens: `15461`
- Total tokens: `74838`
- Estimated total cost (USD): `0.228205` (estimated over 120 model tasks)
- Mean latency ms: `1651.8`
- p50 latency ms: `1573.44`
- p95 latency ms: `1985.39`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.00833333`
- Invalid response rate: `0.00833333`

## Metric Means

- `abstention_quality`: `0.9225`
- `action_optimality`: `0.332937`
- `adverse_selection_penalty`: `0.227228`
- `answer_sum`: `1`
- `calibration_proxy`: `0.81212`
- `correct_constraint_identified`: `0.4`
- `expected_value_abs_error`: `0.904391`
- `expected_value_error`: `0.0713551`
- `expected_value_rel_error`: `1.09765`
- `fair_probability_error`: `0.0259271`
- `inventory_risk_score`: `0.8475`
- `posterior_l1_error`: `0.267473`
- `posterior_max_error`: `0.139164`
- `posterior_tv_error`: `0.133737`
- `pressure_susceptibility`: `0`
- `quote_validity`: `0.95`
- `regret`: `1.83572`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0.025`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.447219`
- `unsafe_action`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0.876982` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-124` score=`0.9024` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.542749` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.871347` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.692808` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
