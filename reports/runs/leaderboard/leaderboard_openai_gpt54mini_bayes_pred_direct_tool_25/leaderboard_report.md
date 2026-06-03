# Leaderboard report: leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25

- Run ID: `leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25-20260602T215150`
- Timestamp: `2026-06-02T21:51:50Z`
- Agent modes: direct, tool
- Tasks per agent: `50`
- Preliminary tiny run: **no**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_gpt_5_4_mini_bayes_pred_25 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_4_mini_bayes_pred_25 | openai | direct | 2 | 50 | 0.654369 | n/a/n/a | 0 | 0 | $0.036635 | 1422.6/3577.19 |
| openai_gpt_5_4_mini_bayes_pred_25 | openai | tool | 2 | 50 | 0.559882 | n/a/n/a | 0.04 | 0 | not estimated | 1522.87/2746.25 |

## Paired deltas (candidate minus baseline, identical task IDs)


### openai_gpt_5_4_mini_bayes_pred_25

| Pair | Pairs | Score | Posterior error | Risk viol. | Parse fail | Latency ms | Cost USD | Robustness drop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tool_vs_direct` | 50 | -0.0944876 | 0.0563906 | 0.04 | 0 | -19.8335 | n/a | n/a |

## Headline candidates

No headline candidates: available metrics did not meet the evidence threshold.

## Caveats

- All paired deltas are candidate minus baseline on identical task IDs (and identical variant IDs for robustness).
- Higher mean score is better; lower posterior error, risk violations, parse failures, latency, cost, and robustness score drop are better.
- Cost is reported only when pricing was configured; otherwise it is 'not estimated'.
- No hidden chain-of-thought is collected or reported; graders and labels are deterministic.
- These are benchmark diagnostics, not evidence of trading usefulness or profitability.
- These are synthetic deterministic evaluation tasks, not live-market or deployment outcomes.
- Leaderboard rows describe only the configured model, agent mode, environments, and task set; they are not frontier-model claims.

## Artefacts

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25\headline_candidates.md`
