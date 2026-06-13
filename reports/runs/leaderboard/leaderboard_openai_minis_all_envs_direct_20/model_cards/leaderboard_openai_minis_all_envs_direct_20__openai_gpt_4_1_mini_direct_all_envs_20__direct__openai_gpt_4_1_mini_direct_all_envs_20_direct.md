# Model card: openai_gpt_4_1_mini_direct_all_envs_20::direct

## Identity

- Model or agent: `openai_gpt_4_1_mini_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-4.1-mini`
- Run ID: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_4_1_mini_direct_all_envs_20__direct-20260602T212111`
- Run name: `leaderboard_openai_minis_all_envs_direct_20__openai_gpt_4_1_mini_direct_all_envs_20__direct`
- Date/time: `2026-06-02T21:21:11Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_minis_all_envs_direct_20\models\openai_gpt_4_1_mini_direct_all_envs_20\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.619613`
- Mean regret: `0.780568`
- Calibration summary: `{"brier_score": 0.26154306779661013, "expected_calibration_error": 0.2819152542372882, "n_confidence_records": 59}`
- Risk violation rate: `0.025`
- Parse failure rate: `0.0166667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.038121, "mean_latency_ms": 1520.4990716671698, "p95_latency_ms": 2415.572275005252}`

## Known Failure Modes

- `market_making/market_making-123` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `market_making/market_making-125` severity=`1.5` labels=`overconfidence, ignored_risk_limit, inventory_limit_error`: answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; market-making action breaches or mishandles inventory limits (score=0.000; violations=position_limit).
- `prediction_markets/prediction_markets-131` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-138` severity=`1.06524` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.548; violations=none).
- `bayesian_games/bayesian_games-133` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
