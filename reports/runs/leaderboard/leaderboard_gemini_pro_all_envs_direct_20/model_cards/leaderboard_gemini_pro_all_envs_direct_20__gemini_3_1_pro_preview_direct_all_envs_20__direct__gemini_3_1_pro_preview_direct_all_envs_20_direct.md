# Model card: gemini_3_1_pro_preview_direct_all_envs_20::direct

## Identity

- Model or agent: `gemini_3_1_pro_preview_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.1-pro-preview`
- Run ID: `leaderboard_gemini_pro_all_envs_direct_20__gemini_3_1_pro_preview_direct_all_envs_20__direct-20260603T063843`
- Run name: `leaderboard_gemini_pro_all_envs_direct_20__gemini_3_1_pro_preview_direct_all_envs_20__direct`
- Date/time: `2026-06-03T06:38:43Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_pro_all_envs_direct_20\models\gemini_3_1_pro_preview_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 4096, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.751072`
- Mean regret: `2.15516`
- Calibration summary: `{"brier_score": 0.2863679245283019, "expected_calibration_error": 0.3009433962264151, "n_confidence_records": 53}`
- Risk violation rate: `0`
- Parse failure rate: `0.116667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 106 model tasks", "estimated_total_cost_usd": 1.130186, "mean_latency_ms": 26976.296759999488, "p95_latency_ms": 118734.83315500052}`

## Known Failure Modes

- `prediction_markets/prediction_markets-137` severity=`1.07834` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.417; violations=none).
- `prediction_markets/prediction_markets-138` severity=`1.07825` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.418; violations=none).
- `prediction_markets/prediction_markets-132` severity=`1.07652` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.435; violations=none).
- `prediction_markets/prediction_markets-129` severity=`1.07624` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.438; violations=none).
- `prediction_markets/prediction_markets-142` severity=`1.0759` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.441; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
