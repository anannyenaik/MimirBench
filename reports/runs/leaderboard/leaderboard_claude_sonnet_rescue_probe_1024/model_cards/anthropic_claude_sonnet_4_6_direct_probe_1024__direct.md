# Model card: anthropic_claude_sonnet_4_6_direct_probe_1024::direct

## Identity

- Model or agent: `anthropic_claude_sonnet_4_6_direct_probe_1024::direct`
- Result label: **real API model**
- Provider: `anthropic`
- Model: `claude-sonnet-4-6`
- Run ID: `leaderboard_claude_sonnet_rescue_probe_1024__anthropic_claude_sonnet_4_6_direct_probe_1024__direct-20260603T030735`
- Run name: `leaderboard_claude_sonnet_rescue_probe_1024__anthropic_claude_sonnet_4_6_direct_probe_1024__direct`
- Date/time: `2026-06-03T03:07:35Z`
- Run directory: `reports/runs/leaderboard/leaderboard_claude_sonnet_rescue_probe_1024/models/anthropic_claude_sonnet_4_6_direct_probe_1024/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `30`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 1024, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.816447`
- Mean regret: `0.500142`
- Calibration summary: `{"brier_score": 0.19460000000000002, "expected_calibration_error": 0.21333333333333332, "n_confidence_records": 15}`
- Risk violation rate: `0`
- Parse failure rate: `0.0666667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 30 model tasks", "estimated_total_cost_usd": 0.286554, "mean_latency_ms": 9561.28732666742, "p95_latency_ms": 16032.14778500696}`

## Known Failure Modes

- `hidden_regimes/hidden_regimes-123` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `hidden_regimes/hidden_regimes-124` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `prediction_markets/prediction_markets-127` severity=`0.977122` labels=`wrong_action_despite_correct_belief, overtrading`: belief/estimate appears close but the chosen action is poor; trade size or direction is excessive relative to the reference or limits (score=0.429; violations=none).
- `prediction_markets/prediction_markets-124` severity=`0.975874` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.537; violations=none).
- `prediction_markets/prediction_markets-126` severity=`0.934536` labels=`wrong_action_despite_correct_belief, overconfidence, overtrading`: belief/estimate appears close but the chosen action is poor; answer is wrong or low-scoring while confidence is high; trade size or direction is excessive relative to the reference or limits (score=0.574; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
