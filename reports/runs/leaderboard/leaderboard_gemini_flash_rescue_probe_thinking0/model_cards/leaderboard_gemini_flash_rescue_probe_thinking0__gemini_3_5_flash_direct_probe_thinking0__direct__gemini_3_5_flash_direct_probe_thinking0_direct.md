# Model card: gemini_3_5_flash_direct_probe_thinking0::direct

## Identity

- Model or agent: `gemini_3_5_flash_direct_probe_thinking0::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.5-flash`
- Run ID: `leaderboard_gemini_flash_rescue_probe_thinking0__gemini_3_5_flash_direct_probe_thinking0__direct-20260603T054140`
- Run name: `leaderboard_gemini_flash_rescue_probe_thinking0__gemini_3_5_flash_direct_probe_thinking0__direct`
- Date/time: `2026-06-03T05:41:40Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_flash_rescue_probe_thinking0\models\gemini_3_5_flash_direct_probe_thinking0\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `6`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.828754`
- Mean regret: `0.109166`
- Calibration summary: `{"brier_score": 0.4575, "expected_calibration_error": 0.5499999999999999, "n_confidence_records": 3}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 6 model tasks", "estimated_total_cost_usd": 0.011357, "mean_latency_ms": 1829.8137500023586, "p95_latency_ms": 2640.784025006724}`

## Known Failure Modes

- `prediction_markets/prediction_markets-123` severity=`0.87957` labels=`overconfidence`: answer is wrong or low-scoring while confidence is high (score=0.796; violations=none).
- `market_making/market_making-123` severity=`0.785731` labels=`overconfidence`: answer is wrong or low-scoring while confidence is high (score=0.643; violations=none).
- `hidden_regimes/hidden_regimes-123` severity=`0.51431` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.857; violations=none).
- `bayesian_games/bayesian_games-123` severity=`0.512302` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.877; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
