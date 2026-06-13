# Leaderboard report: leaderboard_claude_sonnet_rescue_probe_1024

- Run ID: `leaderboard_claude_sonnet_rescue_probe_1024-20260603T030733`
- Timestamp: `2026-06-03T03:07:33Z`
- Agent modes: direct
- Tasks per agent: `30`
- Pilot-scale run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| anthropic_claude_sonnet_4_6_direct_probe_1024 | anthropic | yes | anthropic installed and ANTHROPIC_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic_claude_sonnet_4_6_direct_probe_1024 | anthropic | direct | 6 | 30 | 0.816447 | n/a/n/a | 0 | 0.0666667 | $0.286554 | 9017.8/16032.1 |

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

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_claude_sonnet_rescue_probe_1024\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_claude_sonnet_rescue_probe_1024\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_claude_sonnet_rescue_probe_1024\headline_candidates.md`
