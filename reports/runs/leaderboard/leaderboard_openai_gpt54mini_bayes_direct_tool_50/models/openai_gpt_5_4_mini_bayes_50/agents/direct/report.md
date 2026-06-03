# leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__direct

- Run ID: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__direct-20260602T232920`
- Timestamp: `2026-06-02T23:29:20Z`
- Agent: `openai_gpt_5_4_mini_bayes_50::direct` (`direct`)
- Number of tasks: `50`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 50 | 0.837207 | 0.32 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.837207`
- Pass rate: `0.32`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1725.81`
- Latency p50 ms: `1363.23`
- Latency p95 ms: `2312.57`

## Cost and Latency

- Total input tokens: `23886`
- Total output tokens: `4112`
- Total tokens: `27998`
- Estimated total cost (USD): `0.036419` (estimated over 50 model tasks)
- Mean latency ms: `1725.81`
- p50 latency ms: `1363.23`
- p95 latency ms: `2312.57`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.325586`
- `posterior_max_error`: `0.158373`
- `posterior_tv_error`: `0.162793`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.707207` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.199245` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.781212` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.735867` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-130` score=`0.864339` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
