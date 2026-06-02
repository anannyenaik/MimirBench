# hidden_regimes_reference_smoke

- Run ID: `hidden_regimes_reference_smoke-20260602T010928`
- Timestamp: `2026-06-02T01:09:28Z`
- Agent: `reference` (`reference`)
- Number of tasks: `100`

**Warning:** This is a reference solver sanity check, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| hidden_regimes | 100 | 1 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `1`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.55823`
- Latency p50 ms: `0.50835`
- Latency p95 ms: `0.89982`

## Metric Means

- `posterior_l1_error`: `0`
- `posterior_tv_error`: `0`

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
