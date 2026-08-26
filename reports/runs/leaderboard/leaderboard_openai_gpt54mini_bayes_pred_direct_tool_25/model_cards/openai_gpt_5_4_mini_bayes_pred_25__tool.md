# Model card: openai_gpt_5_4_mini_bayes_pred_25::tool

## Identity

- Model or agent: `openai_gpt_5_4_mini_bayes_pred_25::tool`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__tool-20260602T215322`
- Run name: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25__openai_gpt_5_4_mini_bayes_pred_25__tool`
- Date/time: `2026-06-02T21:53:22Z`
- Run directory: `reports/runs/leaderboard/leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25/models/openai_gpt_5_4_mini_bayes_pred_25/agents/tool`

## Evaluation

- Environments evaluated: bayesian_games, prediction_markets
- Number of tasks: `50`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `model`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.559882`
- Mean regret: `0.426028`
- Calibration summary: `{"brier_score": 0.48315199999999997, "expected_calibration_error": 0.6168, "n_confidence_records": 25}`
- Risk violation rate: `0.04`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 1740.3886340005556, "p95_latency_ms": 2746.253345003788}`

## Known Failure Modes

- `prediction_markets/prediction_markets-125` severity=`1.5` labels=`wrong_action_despite_correct_belief, overconfidence, ignored_risk_limit, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; response violates or ignores an explicit risk limit; trade size or direction is excessive relative to the reference or limits (score=0.000; violations=budget_limit).
- `prediction_markets/prediction_markets-130` severity=`1.5` labels=`wrong_action_despite_correct_belief, ignored_risk_limit`: belief/estimate appears close but the chosen action is poor; response violates or ignores an explicit risk limit (score=0.000; violations=empty_trade).
- `prediction_markets/prediction_markets-126` severity=`1.08509` labels=`overconfidence, overtrading`: answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.349; violations=none).
- `prediction_markets/prediction_markets-131` severity=`1.03203` labels=`wrong_action_despite_correct_belief, overconfidence, excessive_abstention, market_price_vs_belief_confusion`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; agent abstained when the deterministic reference did not; prediction-market belief/edge is confused with market price or direction (score=0.180; violations=none).
- `prediction_markets/prediction_markets-139` severity=`1.01802` labels=`wrong_action_despite_correct_belief, overconfidence, excessive_abstention`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; agent abstained when the deterministic reference did not (score=0.320; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
