# Model card: mock_random_valid

## Identity

- Model or agent: `mock_random_valid`
- Result label: **mock diagnostic baseline**
- Provider: `n/a`
- Model: `n/a`
- Run ID: `mock_bayes_mock_random_valid-20260602T060945`
- Run name: `mock_bayes_mock_random_valid`
- Date/time: `2026-06-02T06:09:45Z`
- Run directory: `reports\runs\comparisons\mock_bayes\agent_runs\mock_random_valid`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `20`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 1024, 'max_new_tokens': 512, 'seed': 123}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic structured baseline output; parser repair is not model-facing

## Metrics

- Mean score: `0.727657`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 0.13691000058315694, "p95_latency_ms": 0.3159200055961265}`

## Known Failure Modes

- `bayesian_games/bayesian_games-139` severity=`0.578636` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.214; violations=none).
- `bayesian_games/bayesian_games-131` severity=`0.548327` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.517; violations=none).
- `bayesian_games/bayesian_games-125` severity=`0.548216` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.518; violations=none).
- `bayesian_games/bayesian_games-128` severity=`0.543592` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.564; violations=none).
- `bayesian_games/bayesian_games-129` severity=`0.543285` labels=`posterior_miscalculation`: reported posterior differs materially from the deterministic posterior (score=0.567; violations=none).

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a deterministic mock or diagnostic baseline, not a real model benchmark.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
- This card describes a non-model baseline, not model capability.
