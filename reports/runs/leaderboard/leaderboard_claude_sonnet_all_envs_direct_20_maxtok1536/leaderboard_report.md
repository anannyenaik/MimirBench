# Leaderboard report: leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536

- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536-20260603T034312`
- Timestamp: `2026-06-03T03:43:12Z`
- Agent modes: direct
- Tasks per agent: `120`
- Pilot-scale run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536 | anthropic | yes | anthropic installed and ANTHROPIC_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_claude_sonnet_4_6_direct_all_envs_20_maxtok1536 | anthropic | direct | 6 | 120 | 0.856713 | n/a/n/a | 0 | 0.025 | $1.233993 | 9820.49/19766.3 |

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

- `leaderboard_summary.json`: `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/paired_deltas.jsonl`
- `headline_candidates.md`: `reports/runs/leaderboard/leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536/headline_candidates.md`
