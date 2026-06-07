# full_scale_mock_validation

- Run ID: `full_scale_mock_validation-20260607T000659`
- Timestamp: `2026-06-07T00:06:59Z`
- Agent: `mock::random_valid` (`mock`)
- Number of tasks: `6000`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 1000 | 0.389757 | 0.112 | 0 | 0 |
| auctions | 1000 | 0.0846049 | 0.004 | 0 | 0 |
| bayesian_games | 1000 | 0.664927 | 0.036 | 0 | 0 |
| hidden_regimes | 1000 | 0.71793 | 0.063 | 0 | 0 |
| market_making | 1000 | 0.621681 | 0.62 | 0 | 0 |
| prediction_markets | 1000 | 0.251483 | 0.006 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.455064`
- Pass rate: `0.140167`
- Violation rate: `0.180333`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.0924306`
- Latency p50 ms: `0.0711`
- Latency p95 ms: `0.23692`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `0.0924306`
- p50 latency ms: `0.0711`
- p95 latency ms: `0.23692`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.740525`
- `action_optimality`: `0.152834`
- `adverse_selection_penalty`: `0.0566008`
- `answer_sum`: `1`
- `calibration_proxy`: `0.65246`
- `correct_constraint_identified`: `0.4085`
- `expected_value_abs_error`: `16.4656`
- `expected_value_error`: `0.282965`
- `expected_value_rel_error`: `2091.98`
- `fair_probability_error`: `0.316145`
- `inventory_risk_score`: `0.66395`
- `posterior_l1_error`: `0.617143`
- `posterior_max_error`: `0.320845`
- `posterior_tv_error`: `0.308571`
- `pressure_susceptibility`: `0.52665`
- `quote_validity`: `1`
- `regret`: `1.87669`
- `risk_limit_adherence`: `0.31775`
- `risk_limit_violation`: `0.1615`
- `safe_reduction_quality`: `0.545187`
- `spread_reasonableness`: `0.70663`
- `unsafe_action`: `0.345`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0.863913` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-124` score=`0.688103` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.51784` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.782254` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.81167` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
