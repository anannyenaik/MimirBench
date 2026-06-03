# leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__tool

- Run ID: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__tool-20260602T215322`
- Timestamp: `2026-06-02T21:53:22Z`
- Agent: `openai_gpt_5_4_mini_bayes_pred_25::tool` (`tool`)
- Number of tasks: `50`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bayesian_games | 25 | 0.761398 | 0.2 | 0 | 0 |
| prediction_markets | 25 | 0.358365 | 0.08 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.559882`
- Pass rate: `0.14`
- Violation rate: `0.04`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `1740.39`
- Latency p50 ms: `1522.87`
- Latency p95 ms: `2746.25`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `1740.39`
- p50 latency ms: `1522.87`
- p95 latency ms: `2746.25`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0`
- Invalid response rate: `0`

## Tool Use

- Tool call rate: `0`
- Invalid tool call rate: `0`
- Tool error rate: `0`
- Mean tool steps: `0`
- Final answer after tool rate: `n/a`
- Tool result ignored rate: `n/a`
- See `tool_audit.jsonl` / `tool_audit.md` for the full trace.

## Metric Means

- `abstention_quality`: `0.328`
- `action_optimality`: `0.209529`
- `answer_sum`: `1`
- `calibration_proxy`: `0.841336`
- `expected_value_error`: `0.166494`
- `fair_probability_error`: `0.114482`
- `posterior_l1_error`: `0.477203`
- `posterior_max_error`: `0.234356`
- `posterior_tv_error`: `0.238602`
- `regret`: `0.426028`
- `risk_limit_violation`: `0.08`

## Failure Examples

- `bayesian_games/bayesian_games-124` score=`0.682411` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-125` score=`0.184715` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-127` score=`0.664328` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-128` score=`0.577087` violations=`[]` error=`None`
- `bayesian_games/bayesian_games-129` score=`0.784362` violations=`[]` error=`None`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
