# Model card: gemini_3_5_flash_direct_all_envs_20::direct

## Identity

- Model or agent: `gemini_3_5_flash_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `gemini`
- Model: `gemini-3.5-flash`
- Run ID: `leaderboard_gemini_flash_all_envs_direct_20__gemini_3_5_flash_direct_all_envs_20__direct-20260603T053310`
- Run name: `leaderboard_gemini_flash_all_envs_direct_20__gemini_3_5_flash_direct_all_envs_20__direct`
- Date/time: `2026-06-03T05:33:10Z`
- Run directory: `reports\runs\leaderboard\leaderboard_gemini_flash_all_envs_direct_20\models\gemini_3_5_flash_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 1.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.015`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": 0.0, "expected_calibration_error": 0.0, "n_confidence_records": 2}`
- Risk violation rate: `0`
- Parse failure rate: `0.983333`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.636148, "mean_latency_ms": 3290.1110599998597, "p95_latency_ms": 3730.9540349946465}`

## Known Failure Modes

- `bayesian_games/bayesian_games-123` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-124` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-125` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-126` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-127` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
