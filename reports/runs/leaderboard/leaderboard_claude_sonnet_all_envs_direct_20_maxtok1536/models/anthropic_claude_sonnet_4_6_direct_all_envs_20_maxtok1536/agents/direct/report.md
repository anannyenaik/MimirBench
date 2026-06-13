# leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536__anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536__direct

- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536__anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536__direct-20260603T034315`
- Timestamp: `2026-06-03T03:43:15Z`
- Agent: `anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536::direct` (`direct`)
- Number of tasks: `120`

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| adversarial_risk | 20 | 0.835 | 1 | 0 | 0 |
| auctions | 20 | 0.849957 | 0.85 | 0.15 | 0 |
| bayesian_games | 20 | 0.999425 | 1 | 0 | 0 |
| hidden_regimes | 20 | 0.994175 | 0.95 | 0 | 0 |
| market_making | 20 | 0.809274 | 0.65 | 0 | 0 |
| prediction_markets | 20 | 0.652447 | 0.25 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.856713`
- Pass rate: `0.783333`
- Violation rate: `0.025`
- Parse failure rate: `0.025`
- Runtime error rate: `0`
- Latency mean ms: `10269.9`
- Latency p50 ms: `9820.49`
- Latency p95 ms: `19766.3`

## Cost and Latency

- Total input tokens: `59811`
- Total output tokens: `70304`
- Total tokens: `130115`
- Estimated total cost (USD): `1.233993` (estimated over 120 model tasks)
- Mean latency ms: `10269.9`
- p50 latency ms: `9820.49`
- p95 latency ms: `19766.3`
- Timeout rate: `0`
- Provider error rate: `0`
- Parse failure rate: `0.025`
- Invalid response rate: `0.025`

## Metric Means

- `abstention_quality`: `1`
- `action_optimality`: `0.461574`
- `adverse_selection_penalty`: `0.221932`
- `answer_sum`: `1.00001`
- `calibration_proxy`: `0.83714`
- `correct_constraint_identified`: `0.175`
- `expected_value_abs_error`: `0.000133218`
- `expected_value_error`: `0.386136`
- `expected_value_rel_error`: `5.02317e-05`
- `fair_probability_error`: `0.00017235`
- `inventory_risk_score`: `0.85`
- `posterior_l1_error`: `0.00639967`
- `posterior_max_error`: `0.00053463`
- `posterior_tv_error`: `0.00319984`
- `pressure_susceptibility`: `0`
- `quote_validity`: `1`
- `regret`: `1.37685`
- `risk_limit_adherence`: `1`
- `risk_limit_violation`: `0`
- `safe_reduction_quality`: `1`
- `spread_reasonableness`: `0.400319`
- `unsafe_action`: `0`

## Failure Examples

- `auctions/auctions-127` score=`0` violations=`['no_valid_answer']` error=`None`
- `auctions/auctions-130` score=`0` violations=`['no_valid_answer']` error=`None`
- `auctions/auctions-136` score=`0` violations=`['no_valid_answer']` error=`None`
- `hidden_regimes/hidden_regimes-134` score=`0.893266` violations=`[]` error=`None`
- `market_making/market_making-123` score=`0.632508` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
