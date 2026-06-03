# leaderboard_gemini_pro_smoke__gemini_3_1_pro_preview_direct_smoke__direct

- Run ID: `leaderboard_gemini_pro_smoke__gemini_3_1_pro_preview_direct_smoke__direct-20260603T063353`
- Timestamp: `2026-06-03T06:33:53Z`
- Agent: `gemini_3_1_pro_preview_direct_smoke::direct` (`direct`)
- Number of tasks: `6`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 1 | 0 | 0 | 1 | 1 |
| auctions | 1 | 0 | 0 | 1 | 1 |
| bayesian_games | 1 | 0 | 0 | 1 | 1 |
| hidden_regimes | 1 | 0 | 0 | 1 | 1 |
| market_making | 1 | 0 | 0 | 1 | 1 |
| prediction_markets | 1 | 0 | 0 | 1 | 1 |

## Aggregate Metrics

- Mean score: `0`
- Pass rate: `0`
- Violation rate: `1`
- Parse failure rate: `1`
- Runtime error rate: `1`
- Latency mean ms: `2329.24`
- Latency p50 ms: `2494.03`
- Latency p95 ms: `2826.3`

## Cost and Latency

- Total input tokens: `not estimated`
- Total output tokens: `not estimated`
- Total tokens: `not estimated`
- Estimated total cost (USD): **not estimated (no per-task cost available; configure 'pricing' to estimate)**
- Mean latency ms: `2329.24`
- p50 latency ms: `2494.03`
- p95 latency ms: `2826.3`
- Timeout rate: `0`
- Provider error rate: `1`
- Parse failure rate: `1`
- Invalid response rate: `1`

## Failure Examples

- `bayesian_games/bayesian_games-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Budget 0 is invalid. This model only works in thinking mode.', 'status': 'INVALID_ARGUMENT'}}`
- `auctions/auctions-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Budget 0 is invalid. This model only works in thinking mode.', 'status': 'INVALID_ARGUMENT'}}`
- `hidden_regimes/hidden_regimes-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Budget 0 is invalid. This model only works in thinking mode.', 'status': 'INVALID_ARGUMENT'}}`
- `market_making/market_making-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Budget 0 is invalid. This model only works in thinking mode.', 'status': 'INVALID_ARGUMENT'}}`
- `prediction_markets/prediction_markets-123` score=`0` violations=`['no_valid_answer']` error=`model call failed after 3 attempt(s): ClientError: 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Budget 0 is invalid. This model only works in thinking mode.', 'status': 'INVALID_ARGUMENT'}}`

## Known Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
