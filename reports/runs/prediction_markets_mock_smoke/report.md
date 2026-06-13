# prediction_markets_mock_smoke

- Run ID: `prediction_markets_mock_smoke-20260602T014223`
- Timestamp: `2026-06-02T01:42:23Z`
- Agent: `mock::random_valid` (`mock`)
- Number of tasks: `50`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| prediction_markets | 50 | 0.244629 | 0.02 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.244629`
- Pass rate: `0.02`
- Violation rate: `0.2`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.094938`
- Latency p50 ms: `0.0947`
- Latency p95 ms: `0.132335`

## Metric Means

- `abstention_quality`: `0.769`
- `action_optimality`: `0.152257`
- `calibration_proxy`: `0.681068`
- `expected_value_error`: `0.29198`
- `fair_probability_error`: `0.320362`
- `regret`: `1.89799`
- `risk_limit_violation`: `0.2`

## Failure Examples

- `prediction_markets/prediction_markets-123` score=`0.128165` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-124` score=`0.16004` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-125` score=`0` violations=`['budget_limit']` error=`None`
- `prediction_markets/prediction_markets-126` score=`0.150311` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-127` score=`0.50732` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
