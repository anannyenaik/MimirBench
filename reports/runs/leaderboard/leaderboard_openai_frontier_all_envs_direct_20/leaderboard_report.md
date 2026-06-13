# Leaderboard report: leaderboard_openai_frontier_all_envs_direct_20

- Run ID: `leaderboard_openai_frontier_all_envs_direct_20-20260602T235148`
- Timestamp: `2026-06-02T23:51:48Z`
- Agent modes: direct
- Tasks per agent: `120`
- Pilot-scale run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_gpt_5_4_direct_all_envs_20 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |
| openai_gpt_5_5_direct_all_envs_20 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_5_4_direct_all_envs_20 | openai | direct | 6 | 120 | 0.662963 | n/a/n/a | 0.0333333 | 0 | $0.32627 | 2356.81/3622.97 |
| openai_gpt_5_5_direct_all_envs_20 | openai | direct | 6 | 120 | 0 | n/a/n/a | 0 | 1 | not estimated | 161.3/869.693 |

## Paired deltas (candidate minus baseline, identical task IDs)

No paired deltas (need at least two agent modes per model).

## Headline candidates

No headline candidates: available metrics did not meet the evidence threshold.

## Scope and Limitations

- All paired deltas are candidate minus baseline on identical task IDs (and identical variant IDs for robustness).
- Higher mean score is better; lower posterior error, risk violations, parse failures, latency, cost, and robustness score drop are better.
- Cost is reported only when pricing was configured; otherwise it is 'not estimated'.
- No hidden chain-of-thought is collected or reported; graders and labels are deterministic.
- These are benchmark diagnostics, not evidence of trading usefulness or profitability.
- These are synthetic deterministic evaluation tasks, not live-market or deployment outcomes.
- Each leaderboard row is scoped to the configured model, agent mode, environments, and task set.
- This is a pilot hosted-model evaluation (<= a handful of tasks per environment); full-scale confirmation is required for broader conclusions.

## Artefacts

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_openai_frontier_all_envs_direct_20\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_openai_frontier_all_envs_direct_20\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_openai_frontier_all_envs_direct_20\headline_candidates.md`
