# leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__direct

- Run ID: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__direct-20260602T215152`
- Timestamp: `2026-06-02T21:51:52Z`
- Agent: `openai_gpt_5_4_mini_bayes_pred_25::direct` (`direct`)
- Number of tasks: `50`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 25 | 0.817789 | 0.28 | 0 | 0 |
| prediction_markets | 25 | 0.490949 | 0.16 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.654369`
- Pass rate: `0.22`
- Violation rate: `0`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1760.22`
- Latency p50 ms: `1422.6`
- Latency p95 ms: `3577.19`

## Cost and Latency

- Total input tokens: `22590`
- Total output tokens: `4377`
- Total tokens: `26967`
- Estimated total cost (USD): `0.036635` (estimated over 50 model tasks)
- Mean latency ms: `1760.22`
- p50 latency ms: `1422.6`
- p95 latency ms: `3577.19`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Metric Means

- `abstention_quality`: `0.832`
- `action_optimality`: `0.370648`
- `answer_sum`: `1`
- `calibration_proxy`: `0.822696`
- `expected_value_error`: `0.191854`
- `fair_probability_error`: `0.100381`
- `posterior_l1_error`: `0.364422`
- `posterior_max_error`: `0.177618`
- `posterior_tv_error`: `0.182211`
- `regret`: `1.47158`
- `risk_limit_violation`: `0`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.707207` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.199345` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.84102` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.735867` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-130` score=`0.792911` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
