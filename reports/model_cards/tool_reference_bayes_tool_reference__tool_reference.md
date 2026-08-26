# Model card: tool_reference

## Identity

- Model or agent: `tool_reference`
- Result label: **deterministic non-model tool baseline**
- Provider: `n/a`
- Model: `n/a`
- Run ID: `tool_reference_bayes_tool_reference-20260602T061002`
- Run name: `tool_reference_bayes_tool_reference`
- Date/time: `2026-06-02T06:10:02Z`
- Run directory: `reports/runs/comparisons/tool_reference_bayes/agent_runs/tool_reference`

## Evaluation

- Environments evaluated: bayesian_games
- Number of tasks: `20`
- Decoding settings: `{'temperature': 0.0, 'max_tokens': 1024, 'max_new_tokens': 512, 'seed': 0}`
- Tool policy: `reference`
- Prompt version: MimirBench default prompt templates (no explicit prompt-version tag)
- Parse/repair policy: deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored

## Metrics

- Mean score: `1`
- Mean regret: `n/a`
- Calibration summary: `{"brier_score": null, "expected_calibration_error": null, "n_confidence_records": 0}`
- Risk violation rate: `0`
- Parse failure rate: `0`
- Robustness summary: `null`
- Cost/latency summary: `{"cost_note": "not estimated (no per-task cost available; configure 'pricing' to estimate)", "estimated_total_cost_usd": null, "mean_latency_ms": 0.40380999998888, "p95_latency_ms": 0.6708550001349068}`

## Known Failure Modes

No deterministic failure cases were extracted from this run.

## Limitations

- Results apply to the evaluated environments and deterministic graders.
- Model outputs contain structured answers and concise reasoning summaries; hidden chain-of-thought is not collected.
- Results are scoped to the saved task set, prompt, parser, and decoding settings.
- No LLM judges are used; all grading and failure labels are deterministic.
- These benchmark diagnostics are not evidence of trading usefulness or profitability.
- This card describes a non-model baseline, not model capability.
