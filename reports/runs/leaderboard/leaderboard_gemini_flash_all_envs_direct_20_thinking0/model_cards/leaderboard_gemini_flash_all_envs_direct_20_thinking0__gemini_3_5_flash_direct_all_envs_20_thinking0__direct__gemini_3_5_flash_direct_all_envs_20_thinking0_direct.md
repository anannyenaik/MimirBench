# Model card: gemini_3_5_flash_direct_all_envs_20_thinking0::direct

## Identity

- Model or agent: `gemini_3_5_flash_direct_all_envs_20_thinking0::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.5-flash`
- Run ID: `leaderboard_gemini_flash_all_envs_direct_20_thinking0__gemini_3_5_flash_direct_all_envs_20_thinking0__direct-20260603T054317`
- Run name: `leaderboard_gemini_flash_all_envs_direct_20_thinking0__gemini_3_5_flash_direct_all_envs_20_thinking0__direct`
- Date/time: `2026-06-03T05:43:17Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_flash_all_envs_direct_20_thinking0\models\gemini_3_5_flash_direct_all_envs_20_thinking0\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.745386`
- Mean regret: `1.83572`
- Calibration summary: `{"brier_score": 0.21925041666666667, "expected_calibration_error": 0.2262499999999999, "n_confidence_records": 60}`
- Risk violation rate: `0.00833333`
- Parse failure rate: `0.00833333`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.228205, "mean_latency_ms": 1651.7986974999076, "p95_latency_ms": 1985.3860050046933}`

## Known Failure Modes

- `prediction_markets/prediction_markets-128` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-140` severity=`1.08841` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.316; violations=none).
- `prediction_markets/prediction_markets-126` severity=`1.07683` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.432; violations=none).
- `prediction_markets/prediction_markets-124` severity=`1.07504` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.450; violations=none).
- `prediction_markets/prediction_markets-138` severity=`1.07379` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.462; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
