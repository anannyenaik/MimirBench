# Model card: openai_gpt_5_4_mini_direct_all_envs_20::direct

## Identity

- Model or agent: `openai_gpt_5_4_mini_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_5_4_mini_direct_all_envs_20__direct-20260602T212421`
- Run name: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_5_4_mini_direct_all_envs_20__direct`
- Date/time: `2026-06-02T21:24:21Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_minis_all_envs_direct_20\models\openai_gpt_5_4_mini_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.611416`
- Mean regret: `0.917249`
- Calibration summary: `{"brier_score": 0.2434416666666667, "expected_calibration_error": 0.26349999999999996, "n_confidence_records": 60}`
- Risk violation rate: `0.0166667`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.091214, "mean_latency_ms": 1308.3695499988, "p95_latency_ms": 1821.87749499426}`

## Known Failure Modes

- `market_making/market_making-123` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `prediction_markets/prediction_markets-139` severity=`1.5` labels=`overconfidence, ignored_risk_limit`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit (score=0.000; violations=empty_trade).
- `prediction_markets/prediction_markets-127` severity=`1.10031` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading, market_price_vs_belief_confusion`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.197; violations=none).
- `prediction_markets/prediction_markets-126` severity=`1.09389` labels=`overconfidence, overtrading, market_price_vs_belief_confusion`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.261; violations=none).
- `prediction_markets/prediction_markets-132` severity=`1.00891` labels=`overconfidence, overtrading`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.467; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
