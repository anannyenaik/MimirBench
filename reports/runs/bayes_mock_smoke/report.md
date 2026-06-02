# bayes_mock_smoke

- Run ID: `bayes_mock_smoke-20260602T010928`
- Timestamp: `2026-06-02T01:14:13Z`
- Agent: `mock::random_valid` (`mock`)
- Number of tasks: `100`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 100 | 0.686737 | 0.03 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.686737`
- Pass rate: `0.03`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.116388`
- Latency p50 ms: `0.09965`
- Latency p95 ms: `0.23277`

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.626527`
- `posterior_max_error`: `0.300574`
- `posterior_tv_error`: `0.313263`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0.863913` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-124` score=`0.688103` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.51784` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.782254` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.81167` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
