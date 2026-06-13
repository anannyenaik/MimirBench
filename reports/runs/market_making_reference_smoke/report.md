# market_making_reference_smoke

- Run ID: `market_making_reference_smoke-20260602T014211`
- Timestamp: `2026-06-02T01:42:11Z`
- Agent: `reference` (`reference`)
- Number of tasks: `50`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| market_making | 50 | 0.99905 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.99905`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.12252`
- Latency p50 ms: `0.1151`
- Latency p95 ms: `0.21666`

## Metric Means

- `abstention_quality`: `1`
- `adverse_selection_penalty`: `0`
- `inventory_risk_score`: `1`
- `quote_validity`: `1`
- `risk_limit_violation`: `0`
- `spread_reasonableness`: `0.995248`

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
