# Model card: openai_gpt_5_4_direct_all_envs_20::direct

## Identity

- Model or agent: `openai_gpt_5_4_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4`
- Run ID: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_4_direct_all_envs_20__direct-20260602T235149`
- Run name: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_4_direct_all_envs_20__direct`
- Date/time: `2026-06-02T23:51:49Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_frontier_all_envs_direct_20\models\openai_gpt_5_4_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.662963`
- Mean regret: `2.85095`
- Calibration summary: `{"brier_score": 0.23303208333333333, "expected_calibration_error": 0.21841666666666665, "n_confidence_records": 60}`
- Risk violation rate: `0.0333333`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.32627, "mean_latency_ms": 2565.998784165519, "p95_latency_ms": 3622.97148999205}`

## Known Failure Modes

- `prediction_markets/prediction_markets-128` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-131` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-138` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-141` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-140` severity=`1.09809` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.219; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
