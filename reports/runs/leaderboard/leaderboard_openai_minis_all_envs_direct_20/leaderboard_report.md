# Leaderboard report: leaderboard_openai_minis_all_envs_direct_20

- Run ID: `leaderboard_openai_minis_all_envs_direct_20-20260602T212110`
- Timestamp: `2026-06-02T21:21:10Z`
- Agent modes: direct
- Tasks per agent: `120`
- Preliminary tiny run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_gpt_4_1_mini_direct_all_envs_20 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |
| openai_gpt_5_4_mini_direct_all_envs_20 | openai | yes | openai installed and OPENAI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai_gpt_4_1_mini_direct_all_envs_20 | openai | direct | 6 | 120 | 0.619613 | n/a/n/a | 0.025 | 0.0166667 | $0.038121 | 1451.59/2415.57 |
| openai_gpt_5_4_mini_direct_all_envs_20 | openai | direct | 6 | 120 | 0.611416 | n/a/n/a | 0.0166667 | 0 | $0.091214 | 1146.07/1821.88 |

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

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_openai_minis_all_envs_direct_20\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_openai_minis_all_envs_direct_20\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_openai_minis_all_envs_direct_20\headline_candidates.md`
