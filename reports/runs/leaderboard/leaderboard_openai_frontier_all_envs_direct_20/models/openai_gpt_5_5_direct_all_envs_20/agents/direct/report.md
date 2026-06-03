# leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct

- Run ID: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct-20260602T235703`
- Timestamp: `2026-06-02T23:57:03Z`
- Agent: `openai_gpt_5_5_direct_all_envs_20::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0 | 0 | 1 | 1 |
| auctions | 20 | 0 | 0 | 1 | 1 |
| bayesian_games | 20 | 0 | 0 | 1 | 1 |
| hidden_regimes | 20 | 0 | 0 | 1 | 1 |
| market_making | 20 | 0 | 0 | 1 | 1 |
| prediction_markets | 20 | 0 | 0 | 1 | 1 |

## Aggregate Metrics

- Mean score: `0`
- Pass rate: `0`
- Violation rate: `1`
- Parse failure rate: `1`
- Runtime error rate: `1`
- Latency mean ms: `238.764`
- Latency p50 ms: `161.3`
- Latency p95 ms: `869.693`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `238.764`
- p50 latency ms: `161.3`
- p95 latency ms: `869.693`
- Timeout rate: `0`
- Provider error rate: `1`
- Parse failure rate: `1`
- Invalid response rate: `1`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): BadRequestError: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}`
- `bayesian_games/bayesian_games-124` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): BadRequestError: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}`
- `bayesian_games/bayesian_games-125` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): BadRequestError: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}`
- `bayesian_games/bayesian_games-126` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): BadRequestError: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}`
- `bayesian_games/bayesian_games-127` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): BadRequestError: Error code: 400 - {'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
