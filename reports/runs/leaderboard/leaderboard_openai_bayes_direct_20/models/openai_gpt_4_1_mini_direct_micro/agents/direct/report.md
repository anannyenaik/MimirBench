# leaderboard_openai_bayes_direct_20__openai_gpt_4_1_mini_direct_micro__direct

- Run ID: `leaderboard_openai_bayes_direct_20__openai_gpt_4_1_mini_direct_micro__direct-20260602T200423`
- Timestamp: `2026-06-02T20:04:23Z`
- Agent: `openai_gpt_4_1_mini_direct_micro::direct` (`direct`)
- Number of tasks: `20`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 20 | 0.780615 | 0.2 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.780615`
- Pass rate: `0.2`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1467.4`
- Latency p50 ms: `1221.67`
- Latency p95 ms: `2328.12`

## Cost and Latency

- Total input tokens: `9637`
- Total output tokens: `1093`
- Total tokens: `10730`
- Estimated total cost (USD): `0.005604` (estimated over 20 model tasks)
- Mean latency ms: `1467.4`
- p50 latency ms: `1221.67`
- p95 latency ms: `2328.12`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.438769`
- `posterior_max_error`: `0.217506`
- `posterior_tv_error`: `0.219385`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.543122` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.397806` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.889223` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.808596` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.40471` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
