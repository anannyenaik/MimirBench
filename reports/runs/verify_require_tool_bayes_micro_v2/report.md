# verify_require_tool_bayes_micro_v2

- Run ID: `verify_require_tool_bayes_micro_v2-20260602T231157`
- Timestamp: `2026-06-02T23:11:57Z`
- Agent: `tool::openai::gpt-5.4-mini` (`tool`)
- Number of tasks: `3`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 3 | 0.999637 | 1 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.999637`
- Pass rate: `1`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `5131.19`
- Latency p50 ms: `3436.58`
- Latency p95 ms: `8348.32`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `5131.19`
- p50 latency ms: `3436.58`
- p95 latency ms: `8348.32`
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
- `posterior_l1_error`: `0.000726886`
- `posterior_max_error`: `0.000329702`
- `posterior_tv_error`: `0.000363443`

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
