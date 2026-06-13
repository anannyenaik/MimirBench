# Model card: openai_gpt_5_4_mini_bayes_pred_25::direct

## Identity

- Model or agent: `openai_gpt_5_4_mini_bayes_pred_25::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__direct-20260602T215152`
- Run name: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__direct`
- Date/time: `2026-06-02T21:51:52Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25\models\openai_gpt_5_4_mini_bayes_pred_25\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, prediction_markets
- Number of tasks: `50`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.654369`
- Mean regret: `1.47158`
- Calibration summary: `{"brier_score": 0.43390799999999996, "expected_calibration_error": 0.622, "n_confidence_records": 25}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 50 model tasks", "estimated_total_cost_usd": 0.036635, "mean_latency_ms": 1760.2220999979181, "p95_latency_ms": 3577.190864997826}`

## Known Failure Modes

- `prediction_markets/prediction_markets-127` severity=`1.10011` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading, market_price_vs_belief_confusion`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.199; violations=none).
- `prediction_markets/prediction_markets-126` severity=`1.09177` labels=`overconfidence, overtrading, market_price_vs_belief_confusion`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.282; violations=none).
- `prediction_markets/prediction_markets-132` severity=`1.07407` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.459; violations=none).
- `prediction_markets/prediction_markets-133` severity=`1.06475` labels=`overconfidence, overtrading`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.553; violations=none).
- `prediction_markets/prediction_markets-131` severity=`1.00899` labels=`wrong_action_despite_correct_belief, overconfidence`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high (score=0.410; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
