# Model card: openai_gpt_4_1_mini_direct_micro::direct

## Identity

- Model or agent: `openai_gpt_4_1_mini_direct_micro::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-4.1-mini`
- Run ID: `leaderboard_openai_bayes_direct_20__openai_gpt_4_1_mini_direct_micro__direct-20260602T200423`
- Run name: `leaderboard_openai_bayes_direct_20__openai_gpt_4_1_mini_direct_micro__direct`
- Date/time: `2026-06-02T20:04:23Z`
- Run directory: `reports/runs/leaderboard/leaderboard_openai_bayes_direct_20/models/openai_gpt_4_1_mini_direct_micro/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `20`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.780615`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 20 model tasks", "estimated_total_cost_usd": 0.005604, "mean_latency_ms": 1467.404370001168, "p95_latency_ms": 2328.1200350116724}`

## Known Failure Modes

- `bayesian_games/bayesian_games-137` severity=`0.575881` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.241; violations=none).
- `bayesian_games/bayesian_games-125` severity=`0.560219` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.398; violations=none).
- `bayesian_games/bayesian_games-128` severity=`0.559529` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.405; violations=none).
- `bayesian_games/bayesian_games-124` severity=`0.545688` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.543; violations=none).
- `bayesian_games/bayesian_games-132` severity=`0.543616` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.564; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
