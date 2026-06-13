# Model card: openai_gpt_5_4_mini_direct_all_envs_tiny::direct

## Identity

- Model or agent: `openai_gpt_5_4_mini_direct_all_envs_tiny::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_modern_mini_all_envs_direct_tiny__openai_gpt_5_4_mini_direct_all_envs_tiny__direct-20260602T210801`
- Run name: `leaderboard_openai_modern_mini_all_envs_direct_tiny__openai_gpt_5_4_mini_direct_all_envs_tiny__direct`
- Date/time: `2026-06-02T21:08:01Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_modern_mini_all_envs_direct_tiny\models\openai_gpt_5_4_mini_direct_all_envs_tiny\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `30`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.543625`
- Mean regret: `3.29007`
- Calibration summary: `{"brier_score": 0.25819333333333344, "expected_calibration_error": 0.35266666666666663, "n_confidence_records": 15}`
- Risk violation rate: `0.0333333`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 30 model tasks", "estimated_total_cost_usd": 0.022646, "mean_latency_ms": 1433.9567466663236, "p95_latency_ms": 2751.5557350001473}`

## Known Failure Modes

- `market_making/market_making-125` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `prediction_markets/prediction_markets-126` severity=`1.09389` labels=`overconfidence, overtrading, market_price_vs_belief_confusion`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.261; violations=none).
- `prediction_markets/prediction_markets-127` severity=`1.00211` labels=`wrong_action_despite_correct_belief, overtrading, market_price_vs_belief_confusion`: belief/estimate appears close but the chosen action is poor; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.179; violations=none).
- `market_making/market_making-123` severity=`0.997526` labels=`overconfidence, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; market-making action breaches or mishandles inventory limits (score=0.525; violations=none).
- `prediction_markets/prediction_markets-125` severity=`0.8583` labels=`wrong_action_despite_correct_belief, overtrading, market_price_vs_belief_confusion`: belief/estimate appears close but the chosen action is poor; trade size or direction is excessive relative to the reference or limits; prediction-market belief/edge is confused with market price or direction (score=0.184; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
