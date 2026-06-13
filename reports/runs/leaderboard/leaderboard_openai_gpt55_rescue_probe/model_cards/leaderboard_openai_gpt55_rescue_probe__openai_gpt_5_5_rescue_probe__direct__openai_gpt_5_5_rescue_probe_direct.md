# Model card: openai_gpt_5_5_rescue_probe::direct

## Identity

- Model or agent: `openai_gpt_5_5_rescue_probe::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.5`
- Run ID: `leaderboard_openai_gpt55_rescue_probe__openai_gpt_5_5_rescue_probe__direct-20260603T005912`
- Run name: `leaderboard_openai_gpt55_rescue_probe__openai_gpt_5_5_rescue_probe__direct`
- Date/time: `2026-06-03T00:59:12Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_gpt55_rescue_probe\models\openai_gpt_5_5_rescue_probe\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, hidden_regimes, market_making
- Number of tasks: `6`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 2048, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.85794`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": 0.5634, "expected_calibration_error": 0.75, "n_confidence_records": 2}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 6 model tasks", "estimated_total_cost_usd": 0.13181, "mean_latency_ms": 17042.60026666695, "p95_latency_ms": 26872.332574999746}`

## Known Failure Modes

- `market_making/market_making-123` severity=`0.81` labels=`overconfidence`: answer is wrong or low-scoring while confidence is high (score=0.400; violations=missing_quote).
- `market_making/market_making-124` severity=`0.775085` labels=`overconfidence`: answer is wrong or low-scoring while confidence is high (score=0.749; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
