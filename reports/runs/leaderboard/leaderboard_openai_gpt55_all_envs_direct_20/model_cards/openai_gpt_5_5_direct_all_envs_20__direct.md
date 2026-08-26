# Model card: openai_gpt_5_5_direct_all_envs_20::direct

## Identity

- Model or agent: `openai_gpt_5_5_direct_all_envs_20::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.5`
- Run ID: `leaderboard_openai_gpt55_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct-20260603T001730`
- Run name: `leaderboard_openai_gpt55_all_envs_direct_20__openai_gpt_5_5_direct_all_envs_20__direct`
- Date/time: `2026-06-03T00:17:30Z`
- Run directory: `reports/runs/leaderboard/leaderboard_openai_gpt55_all_envs_direct_20/models/openai_gpt_5_5_direct_all_envs_20/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games, auctions, hidden_regimes, market_making, prediction_markets, adversarial_risk
- Number of tasks: `120`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- API temperature note: the OpenAI request omitted `temperature` for `gpt-5.5`; the API default temperature was used.
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.213157`
- Mean regret: `0`
- Calibration summary: `{"brier_score": 0.0958894230769231, "expected_calibration_error": 0.13673076923076932, "n_confidence_records": 26}`
- Risk violation rate: `0`
- Parse failure rate: `0.741667`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 120 model tasks", "estimated_total_cost_usd": 1.878215, "mean_latency_ms": 10784.705446666692, "p95_latency_ms": 14242.159400002129}`

## Known Failure Modes

- `bayesian_games/bayesian_games-123` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-124` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-125` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-127` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).
- `bayesian_games/bayesian_games-128` severity=`1` labels=`missing_required_field`: parsed response is missing a required field or has malformed fields (score=0.000; violations=no_valid_answer).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- The `gpt-5.5` row used API-default temperature and is not strictly temperature-paired with `temperature=0` rows.
- 89/120 responses ended with `finish_reason="length"` and empty content under `max_tokens=512`.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
