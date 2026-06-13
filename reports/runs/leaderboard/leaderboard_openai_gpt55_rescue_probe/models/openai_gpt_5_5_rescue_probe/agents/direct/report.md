# leaderboard_openai_gpt55_rescue_probe__openai_gpt_5_5_rescue_probe__direct

- Run ID: `leaderboard_openai_gpt55_rescue_probe__openai_gpt_5_5_rescue_probe__direct-20260603T005912`
- Timestamp: `2026-06-03T00:59:12Z`
- Agent: `openai_gpt_5_5_rescue_probe::direct` (`direct`)
- Number of tasks: `6`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 2 | 0.99963 | 1 | 0 | 0 |
| hidden_regimes | 2 | 0.999614 | 1 | 0 | 0 |
| market_making | 2 | 0.574576 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.85794`
- Pass rate: `0.666667`
- Violation rate: `0.166667`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `17042.6`
- Latency p50 ms: `16756.2`
- Latency p95 ms: `26872.3`

## Cost and Latency

- Total input tokens: `3082`
- Total output tokens: `3880`
- Total tokens: `6962`
- Estimated total cost (USD): `0.13181` (estimated over 6 model tasks)
- Mean latency ms: `17042.6`
- p50 latency ms: `16756.2`
- p95 latency ms: `26872.3`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `1`
- `adverse_selection_penalty`: `0.589192`
- `answer_sum`: `1`
- `inventory_risk_score`: `0.75`
- `posterior_l1_error`: `0.000756253`
- `posterior_max_error`: `0.000306769`
- `posterior_tv_error`: `0.000378126`
- `quote_validity`: `0.5`
- `risk_limit_violation`: `0`
- `spread_reasonableness`: `0.252274`

## Failure Examples

- `market_making/market_making-123` score=`0.4` violations=`['missing_quote']` error=`None`
- `market_making/market_making-124` score=`0.749152` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
