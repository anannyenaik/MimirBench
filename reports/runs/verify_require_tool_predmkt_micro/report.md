# verify_require_tool_predmkt_micro

- Run ID: `verify_require_tool_predmkt_micro-20260602T231854`
- Timestamp: `2026-06-02T23:18:54Z`
- Agent: `tool::openai::gpt-5.4-mini` (`tool`)
- Number of tasks: `3`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| prediction_markets | 3 | 0.237347 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.237347`
- Pass rate: `0`
- Violation rate: `0.666667`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `4224.64`
- Latency p50 ms: `3111.91`
- Latency p95 ms: `6389.4`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `4224.64`
- p50 latency ms: `3111.91`
- p95 latency ms: `6389.4`
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
- Tool result ignored rate: `0.333333`
- See `tool_audit.jsonl` / `tool_audit.md` for the full trace.

## Metric Means

- `abstention_quality`: `0.75`
- `action_optimality`: `0.20264`
- `calibration_proxy`: `0.763267`
- `expected_value_error`: `0.103731`
- `fair_probability_error`: `0.0334627`
- `regret`: `2.71357`
- `risk_limit_violation`: `0.666667`

## Failure Examples

- `prediction_markets/prediction_markets-123` score=`0.712041` violations=`[]` error=`None`
- `prediction_markets/prediction_markets-124` score=`0` violations=`['empty_trade']` error=`None`
- `prediction_markets/prediction_markets-125` score=`0` violations=`['budget_limit']` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
