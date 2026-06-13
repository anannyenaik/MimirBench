# full_scale_reference_validation

- Run ID: `full_scale_reference_validation-20260607T000659`
- Timestamp: `2026-06-07T00:06:59Z`
- Agent: `reference` (`reference`)
- Number of tasks: `6000`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 1000 | 1 | 1 | 0 | 0 |
| auctions | 1000 | 1 | 1 | 0 | 0 |
| bayesian_games | 1000 | 1 | 1 | 0 | 0 |
| hidden_regimes | 1000 | 1 | 1 | 0 | 0 |
| market_making | 1000 | 0.999174 | 1 | 0 | 0 |
| prediction_markets | 1000 | 1 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.999862`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.199337`
- Latency p50 ms: `0.0908`
- Latency p95 ms: `0.57972`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `0.199337`
- p50 latency ms: `0.0908`
- p95 latency ms: `0.57972`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `1`
- `adverse_selection_penalty`: `0`
- `answer_sum`: `1`
- `calibration_proxy`: `1`
- `correct_constraint_identified`: `1`
- `expected_value_abs_error`: `0`
- `expected_value_error`: `0`
- `expected_value_rel_error`: `0`
- `fair_probability_error`: `0`
- `inventory_risk_score`: `1`
- `posterior_l1_error`: `0`
- `posterior_max_error`: `0`
- `posterior_tv_error`: `0`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `0`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.995869`
- `unsafe_action`: `0`

## Failure Examples

No failures recorded.

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a reference solver sanity check, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
