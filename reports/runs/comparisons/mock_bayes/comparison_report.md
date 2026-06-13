# Comparison report: mock_bayes

- Run ID: `mock_bayes-20260602T060943`
- Timestamp: `2026-06-02T06:09:43Z`
- Baseline agent key: `reference`
- Baseline kind: **reference sanity check**

## Agents

| Agent key | Agent name | Type | Result label | Tasks | Mean score | Parse failure |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `reference` | `reference` | `reference` | reference sanity check | 20 | 1 | 0 |
| `mock_random_valid` | `mock_random_valid` | `mock` | mock diagnostic baseline | 20 | 0.727657 | 0 |

## Paired Deltas

Deltas are candidate minus baseline on matched `(environment, task_id)` rows.

| Candidate | Pairs | Score diff | Regret diff | Posterior error diff | Risk violation diff | Parse failure diff | Latency diff ms | Cost diff USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `mock_random_valid` | 20 | -0.272343 | n/a | 0.272343 | 0 | 0 | -8.12584 | n/a |

## Figures

- `reports\runs\comparisons\mock_bayes\figures\score_by_environment.png`
- `reports\runs\comparisons\mock_bayes\figures\posterior_error_distribution.png`
- `reports\runs\comparisons\mock_bayes\figures\risk_violation_rate_by_environment.png`
- `reports\runs\comparisons\mock_bayes\figures\latency_distribution.png`
- `reports\runs\comparisons\mock_bayes\figures\parse_failure_rate_by_agent.png`

## Scope and Limitations

- All paired deltas are candidate minus baseline on identical task IDs.
- Lower regret, posterior error, risk violations, parse failures, latency, and cost are better; higher score is better.
- No hidden chain-of-thought is collected or reported.
- No LLM judges are used; graders and labels are deterministic.
- These results are benchmark diagnostics, not evidence of trading usefulness or profitability.
- Reference, mock, and reference-tool rows are non-model baselines and must not be described as model performance.

## Artefacts

- `paired_results.jsonl`: `reports\runs\comparisons\mock_bayes\paired_results.jsonl`
- Agent run directories: `reports\runs\comparisons\mock_bayes\agent_runs`
- Machine-readable summary: `reports\runs\comparisons\mock_bayes\comparison_summary.json`
