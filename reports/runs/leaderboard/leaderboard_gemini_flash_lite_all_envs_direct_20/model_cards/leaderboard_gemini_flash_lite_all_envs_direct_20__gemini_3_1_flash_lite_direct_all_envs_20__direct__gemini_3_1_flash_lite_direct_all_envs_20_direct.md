# Model card: gemini_3_1_flash_lite_direct_all_envs_20::direct

## Identity

- Model or agent: `gemini_3_1_flash_lite_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.1-flash-lite`
- Run ID: `leaderboard_gemini_flash_lite_all_envs_direct_20__gemini_3_1_flash_lite_direct_all_envs_20__direct-20260603T052929`
- Run name: `leaderboard_gemini_flash_lite_all_envs_direct_20__gemini_3_1_flash_lite_direct_all_envs_20__direct`
- Date/time: `2026-06-03T05:29:29Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_flash_lite_all_envs_direct_20\models\gemini_3_1_flash_lite_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.65352`
- Mean regret: `0.264899`
- Calibration summary: `{"brier_score": 0.2555849333333333, "expected_calibration_error": 0.2624, "n_confidence_records": 60}`
- Risk violation rate: `0.0416667`
- Parse failure rate: `0.0166667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.036121, "mean_latency_ms": 1115.1179241666493, "p95_latency_ms": 904.6354799895197}`

## Known Failure Modes

- `market_making/market_making-124` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `market_making/market_making-129` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `market_making/market_making-131` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `market_making/market_making-139` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `market_making/market_making-141` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
