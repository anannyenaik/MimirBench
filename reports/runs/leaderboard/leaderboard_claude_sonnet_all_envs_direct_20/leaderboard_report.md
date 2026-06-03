# Leaderboard report: leaderboard_claude_sonnet_all_envs_direct_20

- Run ID: `leaderboard_claude_sonnet_all_envs_direct_20-20260603T024514`
- Timestamp: `2026-06-03T02:45:14Z`
- Agent modes: direct
- Tasks per agent: `120`
- Preliminary tiny run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| anthropic_claude_sonnet_4_6_direct_all_envs_20 | anthropic | yes | anthropic installed and ANTHROPIC_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_claude_sonnet_4_6_direct_all_envs_20 | anthropic | direct | 6 | 120 | 0.368856 | n/a/n/a | 0 | 0.591667 | $0.906528 | 8270.36/11452.1 |

## Paired deltas (candidate minus baseline, identical task IDs)

No paired deltas (need at least two agent modes per model).

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
- This is a PRELIMINARY tiny real-model run (<= a handful of tasks per environment); expand the evaluation before drawing strong conclusions.

## Artefacts

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_claude_sonnet_all_envs_direct_20\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_claude_sonnet_all_envs_direct_20\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_claude_sonnet_all_envs_direct_20\headline_candidates.md`
