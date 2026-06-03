# Model card: openai_gpt_5_4_mini_bayes_50::tool

## Identity

- Model or agent: `openai_gpt_5_4_mini_bayes_50::tool`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Run ID: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__tool-20260602T233048`
- Run name: `leaderboard_openai_gpt54mini_bayes_direct_tool_50__openai_gpt_5_4_mini_bayes_50__tool`
- Date/time: `2026-06-02T23:30:48Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_direct_tool_50\models\openai_gpt_5_4_mini_bayes_50\agents\tool`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `50`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `model`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.840188`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 3242.5640359995305, "p95_latency_ms": 4409.553530006813}`

## Known Failure Modes

- `bayesian_games/bayesian_games-150` severity=`0.769946` labels=`posterior_miscalculation, tool_result_ignored`: reported posterior differs materially from the deterministic posterior; tool-use trace exists but the final low-scoring answer appears not to use it (score=0.101; violations=none).
- `bayesian_games/bayesian_games-170` severity=`0.760934` labels=`posterior_miscalculation, tool_result_ignored`: reported posterior differs materially from the deterministic posterior; tool-use trace exists but the final low-scoring answer appears not to use it (score=0.191; violations=none).
- `bayesian_games/bayesian_games-141` severity=`0.759106` labels=`posterior_miscalculation, tool_result_ignored`: reported posterior differs materially from the deterministic posterior; tool-use trace exists but the final low-scoring answer appears not to use it (score=0.209; violations=none).
- `bayesian_games/bayesian_games-168` severity=`0.752163` labels=`posterior_miscalculation, tool_result_ignored`: reported posterior differs materially from the deterministic posterior; tool-use trace exists but the final low-scoring answer appears not to use it (score=0.278; violations=none).
- `bayesian_games/bayesian_games-140` severity=`0.750508` labels=`posterior_miscalculation, tool_result_ignored`: reported posterior differs materially from the deterministic posterior; tool-use trace exists but the final low-scoring answer appears not to use it (score=0.295; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
