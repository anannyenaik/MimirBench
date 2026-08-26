# Model card: openai_gpt_5_4_mini_bayes_50::direct

## Identity

- Model or agent: `openai_gpt_5_4_mini_bayes_50::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__direct-20260602T232920`
- Run name: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__direct`
- Date/time: `2026-06-02T23:29:20Z`
- Run directory: `reports/runs/leaderboard/leaderboard_openai_gpt54mini_bayes_direct_tool_50/models/openai_gpt_5_4_mini_bayes_50/agents/direct`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `50`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.837207`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 50 model tasks", "estimated_total_cost_usd": 0.036419, "mean_latency_ms": 1725.8093760014162, "p95_latency_ms": 2312.5692250032434}`

## Known Failure Modes

- `bayesian_games/bayesian_games-125` severity=`0.580075` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.199; violations=none).
- `bayesian_games/bayesian_games-166` severity=`0.576768` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.232; violations=none).
- `bayesian_games/bayesian_games-137` severity=`0.563721` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.363; violations=none).
- `bayesian_games/bayesian_games-163` severity=`0.548178` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.518; violations=none).
- `bayesian_games/bayesian_games-145` severity=`0.538212` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.618; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
