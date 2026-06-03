# Leaderboard report: leaderboard_openai_all_envs_direct_tiny

- Run ID: `leaderboard_openai_all_envs_direct_tiny-20260602T204109`
- Timestamp: `2026-06-02T20:41:09Z`
- Agent modes: direct
- Tasks per agent: `30`
- Preliminary tiny run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_gpt_4_1_mini_direct_all_envs_tiny | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_4_1_mini_direct_all_envs_tiny | openai | direct | 6 | 30 | 0.60301 | n/a/n/a | 0.0666667 | 0 | $0.00965 | 1748.89/2521.37 |

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

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_openai_all_envs_direct_tiny\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_openai_all_envs_direct_tiny\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_openai_all_envs_direct_tiny\headline_candidates.md`
