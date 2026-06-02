# prediction_markets_reference_smoke

- Run ID: `prediction_markets_reference_smoke-20260602T014211`
- Timestamp: `2026-06-02T01:42:11Z`
- Agent: `reference` (`reference`)
- Number of tasks: `50`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| prediction_markets | 50 | 1 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `1`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.118544`
- Latency p50 ms: `0.1159`
- Latency p95 ms: `0.19075`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `1`
- `calibration_proxy`: `1`
- `expected_value_error`: `0`
- `fair_probability_error`: `0`
- `regret`: `0`
- `risk_limit_violation`: `0`

## Failure Examples

No failures recorded.

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- This is a reference solver sanity check, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
