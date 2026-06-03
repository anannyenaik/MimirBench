# Leaderboard report: leaderboard_openai_gpt54mini_bayes_direct_tool_50

- Run ID: `leaderboard_openai_gpt54mini_bayes_direct_tool_50-20260602T232918`
- Timestamp: `2026-06-02T23:29:18Z`
- Agent modes: direct, tool
- Tasks per agent: `50`
- Preliminary tiny run: **no**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_gpt_5_4_mini_bayes_50 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_4_mini_bayes_50 | openai | direct | 1 | 50 | 0.837207 | n/a/n/a | 0 | 0 | $0.036419 | 1363.23/2312.57 |
| openai_gpt_5_4_mini_bayes_50 | openai | tool | 1 | 50 | 0.840188 | n/a/n/a | 0 | 0 | not estimated | 3050.21/4409.55 |

## Paired deltas (candidate minus baseline, identical task IDs)


### openai_gpt_5_4_mini_bayes_50

| Pair | Pairs | Score | Posterior error | Risk viol. | Parse fail | Latency ms | Cost USD | Robustness drop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tool_vs_direct` | 50 | 0.00298041 | -0.00298041 | 0 | 0 | 1516.75 | n/a | n/a |

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

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_direct_tool_50\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_direct_tool_50\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_openai_gpt54mini_bayes_direct_tool_50\headline_candidates.md`
