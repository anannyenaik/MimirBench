# Model card: gemini_3_1_pro_preview_direct_probe_low_thinking::direct

## Identity

- Model or agent: `gemini_3_1_pro_preview_direct_probe_low_thinking::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.1-pro-preview`
- Run ID: `leaderboard_gemini_pro_rescue_probe_low_thinking__gemini_3_1_pro_preview_direct_probe_low_thinking__direct-20260603T063601`
- Run name: `leaderboard_gemini_pro_rescue_probe_low_thinking__gemini_3_1_pro_preview_direct_probe_low_thinking__direct`
- Date/time: `2026-06-03T06:36:01Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_pro_rescue_probe_low_thinking\models\gemini_3_1_pro_preview_direct_probe_low_thinking\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `6`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 4096, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.814298`
- Mean regret: `1.04853`
- Calibration summary: `{"brier_score": 0.24416666666666664, "expected_calibration_error": 0.3166666666666667, "n_confidence_records": 3}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 6 model tasks", "estimated_total_cost_usd": 0.048754, "mean_latency_ms": 7671.457833331563, "p95_latency_ms": 11471.918400002323}`

## Known Failure Modes

- `prediction_markets/prediction_markets-123` severity=`1.07068` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.493; violations=none).
- `hidden_regimes/hidden_regimes-123` severity=`0.51759` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.824; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
