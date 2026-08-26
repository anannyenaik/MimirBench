# Model card: anthropic_claude_sonnet_4_6_direct_all_envs_20::direct

## Identity

- Model or agent: `anthropic_claude_sonnet_4_6_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `anthropic`
- Model: `claude-sonnet-4-6`
- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20__anthropic_claude_sonnet_4_6_direct_all_envs_20__direct-20260603T024516`
- Run name: `leaderboard_claude_sonnet_all_envs_direct_20__anthropic_claude_sonnet_4_6_direct_all_envs_20__direct`
- Date/time: `2026-06-03T02:45:16Z`
- Run directory: `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20/models/anthropic_claude_sonnet_4_6_direct_all_envs_20/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.368856`
- Mean regret: `0`
- Calibration summary: `{"brier_score": 0.0717529411764706, "expected_calibration_error": 0.08176470588235321, "n_confidence_records": 34}`
- Risk violation rate: `0`
- Parse failure rate: `0.591667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 0.906528, "mean_latency_ms": 7705.265229167344, "p95_latency_ms": 11452.0831750051}`

## Known Failure Modes

- `bayesian_games/bayesian_games-125` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-127` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-128` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-132` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-136` severity=`1.03` labels=`invalid_json, missing_required_field`: response could not be parsed as valid JSON; parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
