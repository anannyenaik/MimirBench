# Model card: gemini_3_1_flash_lite_direct_smoke::direct

## Identity

- Model or agent: `gemini_3_1_flash_lite_direct_smoke::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.1-flash-lite`
- Run ID: `leaderboard_gemini_flash_lite_smoke__gemini_3_1_flash_lite_direct_smoke__direct-20260603T052802`
- Run name: `leaderboard_gemini_flash_lite_smoke__gemini_3_1_flash_lite_direct_smoke__direct`
- Date/time: `2026-06-03T05:28:02Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_flash_lite_smoke\models\gemini_3_1_flash_lite_direct_smoke\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `6`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.851505`
- Mean regret: `0.171092`
- Calibration summary: `{"brier_score": 0.38166666666666665, "expected_calibration_error": 0.5, "n_confidence_records": 3}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 6 model tasks", "estimated_total_cost_usd": 0.001661, "mean_latency_ms": 796.868416662619, "p95_latency_ms": 914.4363749910553}`

## Known Failure Modes

- `market_making/market_making-123` severity=`0.778113` labels=`overconfidence`: answer is wrong or low-scoring while confidence is high (score=0.719; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
