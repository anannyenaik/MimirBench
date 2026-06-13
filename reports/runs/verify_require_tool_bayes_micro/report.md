# verify_require_tool_bayes_micro

- Run ID: `verify_require_tool_bayes_micro-20260602T221536`
- Timestamp: `2026-06-02T22:15:36Z`
- Agent: `tool::openai::gpt-5.4-mini` (`tool`)
- Number of tasks: `3`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 3 | 0.619711 | 0.333333 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.619711`
- Pass rate: `0.333333`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `4858.61`
- Latency p50 ms: `3425.14`
- Latency p95 ms: `7632.2`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `4858.61`
- p50 latency ms: `3425.14`
- p95 latency ms: `7632.2`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Tool Use

- Tool call rate: `1`
- Invalid tool call rate: `0`
- Tool error rate: `1`
- Mean tool steps: `1`
- Final answer after tool rate: `1`
- Tool result ignored rate: `n/a`
- See `tool_audit.jsonl` / `tool_audit.md` for the full trace.

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.760578`
- `posterior_max_error`: `0.380289`
- `posterior_tv_error`: `0.380289`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.693668` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.188715` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
