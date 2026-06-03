# Model card: openai_gpt_4_1_mini_direct_micro::direct

## Identity

- Model or agent: `openai_gpt_4_1_mini_direct_micro::direct`
- Result label: **real API model**
- Provider: `openai`
- Model: `gpt-4.1-mini`
- Run ID: `leaderboard_openai_bayes_direct_micro__openai_gpt_4_1_mini_direct_micro__direct-20260602T194212`
- Run name: `leaderboard_openai_bayes_direct_micro__openai_gpt_4_1_mini_direct_micro__direct`
- Date/time: `2026-06-02T19:42:12Z`
- Run directory: `reports\runs\leaderboard\leaderboard_openai_bayes_direct_micro\models\openai_gpt_4_1_mini_direct_micro\agents\direct`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `5`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 512, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `0.718651`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "estimated over 5 model tasks", "estimated_total_cost_usd": 0.00141, "mean_latency_ms": 5503.779380000196, "p95_latency_ms": 11484.703119992628}`

## Known Failure Modes

- `bayesian_games/bayesian_games-125` severity=`0.559519` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.405; violations=none).
- `bayesian_games/bayesian_games-124` severity=`0.551188` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.488; violations=none).
- `bayesian_games/bayesian_games-127` severity=`0.51574` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.843; violations=none).
- `bayesian_games/bayesian_games-126` severity=`0.511078` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.889; violations=none).

## Limitations

- Scores are meaningful only for the environments and graders actually run.
- No hidden chain-of-thought is collected; model output stores concise summaries only.
- Results apply only to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
