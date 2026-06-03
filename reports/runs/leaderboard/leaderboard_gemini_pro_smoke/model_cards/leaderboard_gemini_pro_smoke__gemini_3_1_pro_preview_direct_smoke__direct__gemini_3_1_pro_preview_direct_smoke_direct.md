# Model card: gemini_3_1_pro_preview_direct_smoke::direct

## Identity

- Model or agent: `gemini_3_1_pro_preview_direct_smoke::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.1-pro-preview`
- Run ID: `leaderboard_gemini_pro_smoke__gemini_3_1_pro_preview_direct_smoke__direct-20260603T063353`
- Run name: `leaderboard_gemini_pro_smoke__gemini_3_1_pro_preview_direct_smoke__direct`
- Date/time: `2026-06-03T06:33:53Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_pro_smoke\models\gemini_3_1_pro_preview_direct_smoke\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `6`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 1024, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `1`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 2329.2418333318587, "p95_latency_ms": 2826.2990250004805}`

## Known Failure Modes

- `bayesian_games/bayesian_games-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `auctions/auctions-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `hidden_regimes/hidden_regimes-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `market_making/market_making-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `prediction_markets/prediction_markets-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
