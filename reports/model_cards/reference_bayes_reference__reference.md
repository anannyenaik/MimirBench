# Model card: reference

## Identity

- Model or agent: `reference`
- Result label: **reference sanity check**
- Provider: `n/a`
- Model: `n/a`
- Run ID: `reference_bayes_reference-20260602T060923`
- Run name: `reference_bayes_reference`
- Date/time: `2026-06-02T06:09:23Z`
- Run directory: `reports/runs/comparisons/reference_bayes/agent_runs/reference`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `20`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 1024, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic structured baseline output; parser repair is not model-facing

## Metrics

- Mean score: `1`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 0.48723500040068757, "p95_latency_ms": 0.7415299958665857}`

## Known Failure Modes

No deterministic failure cases were extracted from this run.

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- This is a reference solver sanity check, not a real model benchmark.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
- This card describes a non-model baseline, not model capability.
