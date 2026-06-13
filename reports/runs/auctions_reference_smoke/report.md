# auctions_reference_smoke

- Run ID: `auctions_reference_smoke-20260602T010928`
- Timestamp: `2026-06-02T01:09:28Z`
- Agent: `reference` (`reference`)
- Number of tasks: `100`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| auctions | 100 | 1 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `1`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.065906`
- Latency p50 ms: `0.06155`
- Latency p95 ms: `0.106355`

## Metric Means

- `expected_value_abs_error`: `0`
- `expected_value_rel_error`: `0`

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
