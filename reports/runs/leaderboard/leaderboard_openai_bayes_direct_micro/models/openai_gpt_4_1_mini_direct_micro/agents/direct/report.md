# leaderboard_openai_bayes_direct_micro__openai_gpt_4_1_mini_direct_micro__direct

- Run ID: `leaderboard_openai_bayes_direct_micro__openai_gpt_4_1_mini_direct_micro__direct-20260602T194212`
- Timestamp: `2026-06-02T19:42:12Z`
- Agent: `openai_gpt_4_1_mini_direct_micro::direct` (`direct`)
- Number of tasks: `5`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 5 | 0.718651 | 0.2 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.718651`
- Pass rate: `0.2`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `5503.78`
- Latency p50 ms: `2018.07`
- Latency p95 ms: `11484.7`

## Cost and Latency

- Total input tokens: `2361`
- Total output tokens: `291`
- Total tokens: `2652`
- Estimated total cost (USD): `0.00141` (estimated over 5 model tasks)
- Mean latency ms: `5503.78`
- p50 latency ms: `2018.07`
- p95 latency ms: `11484.7`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.562698`
- `posterior_max_error`: `0.281349`
- `posterior_tv_error`: `0.281349`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.488122` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.404806` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.889223` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.842596` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
