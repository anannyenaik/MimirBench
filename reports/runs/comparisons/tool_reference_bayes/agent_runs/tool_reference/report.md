# tool_reference_bayes_tool_reference

- Run ID: `tool_reference_bayes_tool_reference-20260602T061002`
- Timestamp: `2026-06-02T06:10:02Z`
- Agent: `tool_reference` (`tool`)
- Number of tasks: `20`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 20 | 1 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `1`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.40381`
- Latency p50 ms: `0.36625`
- Latency p95 ms: `0.670855`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `0.40381`
- p50 latency ms: `0.36625`
- p95 latency ms: `0.670855`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Tool Use

- Tool call rate: `1`
- Invalid tool call rate: `0`
- Tool error rate: `0`
- Mean tool steps: `1`
- Final answer after tool rate: `1`
- Tool result ignored rate: `0`
- See `tool_audit.jsonl` / `tool_audit.md` for the full trace.

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0`
- `posterior_max_error`: `0`
- `posterior_tv_error`: `0`

## Failure Examples

No failures recorded.

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
