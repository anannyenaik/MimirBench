# market_making_mock_smoke

- Run ID: `market_making_mock_smoke-20260602T014223`
- Timestamp: `2026-06-02T01:42:23Z`
- Agent: `mock::random_valid` (`mock`)
- Number of tasks: `50`

**Warning:** This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Environments

| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| market_making | 50 | 0.596485 | 0.58 | 0 | 0 |

## Aggregate Metrics

- Mean score: `0.596485`
- Pass rate: `0.58`
- Violation rate: `0.28`
- Parse failure rate: `0`
- Runtime error rate: `0`
- Latency mean ms: `0.099534`
- Latency p50 ms: `0.0798`
- Latency p95 ms: `0.17473`

## Metric Means

- `abstention_quality`: `0.855`
- `adverse_selection_penalty`: `0.0605056`
- `inventory_risk_score`: `0.621`
- `quote_validity`: `1`
- `risk_limit_violation`: `0.28`
- `spread_reasonableness`: `0.70975`

## Failure Examples

- `market_making/market_making-123` score=`0` violations=`['position_limit']` error=`None`
- `market_making/market_making-125` score=`0` violations=`['position_limit']` error=`None`
- `market_making/market_making-126` score=`0` violations=`['loss_limit', 'position_limit']` error=`None`
- `market_making/market_making-129` score=`0.2775` violations=`[]` error=`None`
- `market_making/market_making-130` score=`0.2775` violations=`[]` error=`None`

## Scope and Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.

## Artefacts

- `results.jsonl`: per-task records.
- `summary.json`: machine-readable aggregate summary.
- `report.md`: this report.
- Cache hits: `0`.
