# mock_bayes_mock_random_valid

- Run ID: `mock_bayes_mock_random_valid-20260602T060945`
- Timestamp: `2026-06-02T06:09:45Z`
- Agent: `mock_random_valid` (`mock`)
- Number of tasks: `20`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 20 | 0.727657 | 0 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.727657`
- Pass rate: `0`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.13691`
- Latency p50 ms: `0.09165`
- Latency p95 ms: `0.31592`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `0.13691`
- p50 latency ms: `0.09165`
- p95 latency ms: `0.31592`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `answer_sum`: `1`
- `posterior_l1_error`: `0.544686`
- `posterior_max_error`: `0.26216`
- `posterior_tv_error`: `0.272343`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0.863913` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-124` score=`0.688103` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.51784` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-126` score=`0.782254` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.81167` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
