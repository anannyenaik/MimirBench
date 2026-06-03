# Leaderboard report: leaderboard_gemini_flash_rescue_probe_thinking0

- Run ID: `leaderboard_gemini_flash_rescue_probe_thinking0-20260603T054137`
- Timestamp: `2026-06-03T05:41:37Z`
- Agent modes: direct
- Tasks per agent: `6`
- Preliminary tiny run: **yes**
- Real model execution permitted: **yes**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| gemini_3_5_flash_direct_probe_thinking0 | gemini | yes | google-genai installed and GEMINI_API_KEY is set; appears usable. |

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemini_3_5_flash_direct_probe_thinking0 | gemini | direct | 6 | 6 | 0.828754 | n/a/n/a | 0 | 0 | $0.011357 | 1729.17/2640.78 |

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

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_gemini_flash_rescue_probe_thinking0\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_gemini_flash_rescue_probe_thinking0\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_gemini_flash_rescue_probe_thinking0\headline_candidates.md`
