# Model card: anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536::direct

## Identity

- Model or agent: `anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536::direct`
- Result label: **real API model**
- Provider: `anthropic`
- Model: `claude-sonnet-4-6`
- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536__anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536__direct-20260603T034315`
- Run name: `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536__anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536__direct`
- Date/time: `2026-06-03T03:43:15Z`
- Run directory: `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/models/anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 1536, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.856713`
- Mean regret: `1.37685`
- Calibration summary: `{"brier_score": 0.22151666666666667, "expected_calibration_error": 0.23133333333333347, "n_confidence_records": 60}`
- Risk violation rate: `0`
- Parse failure rate: `0.025`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 1.233993, "mean_latency_ms": 10269.948213332222, "p95_latency_ms": 19766.326504990135}`

## Known Failure Modes

- `prediction_markets/prediction_markets-132` severity=`1.0759` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.441; violations=none).
- `prediction_markets/prediction_markets-124` severity=`1.07586` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.441; violations=none).
- `prediction_markets/prediction_markets-142` severity=`1.07546` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.445; violations=none).
- `prediction_markets/prediction_markets-134` severity=`1.07519` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.448; violations=none).
- `auctions/auctions-127` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
