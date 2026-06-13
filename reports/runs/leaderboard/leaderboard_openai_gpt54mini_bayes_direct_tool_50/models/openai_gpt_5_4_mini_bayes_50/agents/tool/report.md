# leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__tool

- Run ID: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__tool-20260602T233048`
- Timestamp: `2026-06-02T23:30:48Z`
- Agent: `openai_gpt_5_4_mini_bayes_50::tool` (`tool`)
- Number of tasks: `50`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 50 | 0.840188 | 0.64 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.840188`
- Pass rate: `0.64`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `3242.56`
- Latency p50 ms: `3050.21`
- Latency p95 ms: `4409.55`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `3242.56`
- p50 latency ms: `3050.21`
- p95 latency ms: `4409.55`
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
- `posterior_l1_error`: `0.319625`
- `posterior_max_error`: `0.158194`
- `posterior_tv_error`: `0.159812`

## Failure Examples

- `bayesian_games/bayesian_games-126` score=`0.85436` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-130` score=`0.584016` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-134` score=`0.729299` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-138` score=`0.913488` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-140` score=`0.294915` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
