# Model card: openai_gpt_5_5_direct_all_envs_20::direct

## Identity

- Model or agent: `openai_gpt_5_5_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.5`
- Run ID: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct-20260602T235703`
- Run name: `leaderboard_openai_frontier_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct`
- Date/time: `2026-06-02T23:57:03Z`
- Run directory: `reports/runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20/models/openai_gpt_5_5_direct_all_envs_20/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `1`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 238.76384333319342, "p95_latency_ms": 869.6929699952307}`

## Known Failure Modes

- `bayesian_games/bayesian_games-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-124` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-125` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-126` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-127` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
