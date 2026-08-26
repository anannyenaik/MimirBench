# Comparison report: tool_reference_bayes

- Run ID: `tool_reference_bayes-20260602T061002`
- Timestamp: `2026-06-02T06:10:02Z`
- Baseline agent key: `reference`
- Baseline kind: **reference sanity check**

## Agents

| Agent key | Agent name | Type | Result label | Tasks | Mean score | Parse failure |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `reference` | `reference` | `reference` | reference sanity check | 20 | 1 | 0 |
| `tool_reference` | `tool_reference` | `tool` | deterministic non-model tool baseline | 20 | 1 | 0 |

## Paired Deltas

Deltas are candidate minus baseline on matched `(environment, task_id)` rows.

| Candidate | Pairs | Score diff | Regret diff | Posterior error diff | Risk violation diff | Parse failure diff | Latency diff ms | Cost diff USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tool_reference` | 20 | 0 | n/a | 0 | 0 | 0 | -0.047565 | n/a |

## Figures

- `reports/runs/comparisons/tool_reference_bayes/figures/score_by_environment.png`
- `reports/runs/comparisons/tool_reference_bayes/figures/posterior_error_distribution.png`
- `reports/runs/comparisons/tool_reference_bayes/figures/risk_violation_rate_by_environment.png`
- `reports/runs/comparisons/tool_reference_bayes/figures/latency_distribution.png`
- `reports/runs/comparisons/tool_reference_bayes/figures/parse_failure_rate_by_agent.png`

## Scope and Limitations

- All paired deltas are candidate minus baseline on identical task IDs.
- Lower regret, posterior error, risk violations, parse failures, latency, and cost are better; higher score is better.
- No hidden chain-of-thought is collected or reported.
- No LLM judges are used; graders and labels are deterministic.
- These results are benchmark diagnostics, not evidence of trading usefulness or profitability.
- Reference, mock, and reference-tool rows are non-model baselines and must not be described as model performance.

## Artefacts

- `paired_results.jsonl`: `reports/runs/comparisons/tool_reference_bayes/paired_results.jsonl`
- Agent run directories: `reports/runs/comparisons/tool_reference_bayes/agent_runs`
- Machine-readable summary: `reports/runs/comparisons/tool_reference_bayes/comparison_summary.json`
