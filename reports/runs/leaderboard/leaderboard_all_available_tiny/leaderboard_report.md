# Leaderboard report: leaderboard_all_available_tiny

- Run ID: `leaderboard_all_available_tiny-20260602T184848`
- Timestamp: `2026-06-02T18:48:48Z`
- Agent modes: direct, tool, reflective
- Tasks per agent: `60`
- Pilot-scale run: **yes**
- Real model execution permitted: **no**

## Provider availability

| Model | Provider | Usable | Detail |
| --- | --- | :---: | --- |
| openai_configured_tiny | openai | no | openai package not installed (pip install -e ".[api]"). |
| anthropic_configured_tiny | anthropic | no | anthropic package not installed (pip install anthropic). |
| local_configured_tiny | hf_local | no | torch/transformers not installed (pip install -e ".[ml]"). |

## Models pending (not run)

- `openai_configured_tiny` (openai): openai package not installed (pip install -e ".[api]").
- `anthropic_configured_tiny` (anthropic): anthropic package not installed (pip install anthropic).
- `local_configured_tiny` (hf_local): torch/transformers not installed (pip install -e ".[ml]").

## Leaderboard

| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | Risk violation | Parse failure | Cost | Latency p50/p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| _no models were run (see provider availability above)_ |  |  |  |  |  |  |  |  |  |  |

## Paired deltas (candidate minus baseline, identical task IDs)

No paired deltas (need at least two agent modes per model).

## Headline candidates

No headline candidates: no run produced metrics that meet the evidence threshold. Real model runs are pending.

## Scope and Limitations

- All paired deltas are candidate minus baseline on identical task IDs (and identical variant IDs for robustness).
- Higher mean score is better; lower posterior error, risk violations, parse failures, latency, cost, and robustness score drop are better.
- Cost is reported only when pricing was configured; otherwise it is 'not estimated'.
- No hidden chain-of-thought is collected or reported; graders and labels are deterministic.
- These are benchmark diagnostics, not evidence of trading usefulness or profitability.
- This is a pilot-scale infrastructure run (<= a handful of tasks per environment); interpret it as a smoke test.
- No model-performance rows were produced in this run; provider checks and pending artefacts are infrastructure status, not benchmark results.

## Artefacts

- `leaderboard_summary.json`: `reports\runs\leaderboard\leaderboard_all_available_tiny\leaderboard_summary.json`
- `paired_deltas.jsonl`: `reports\runs\leaderboard\leaderboard_all_available_tiny\paired_deltas.jsonl`
- `headline_candidates.md`: `reports\runs\leaderboard\leaderboard_all_available_tiny\headline_candidates.md`
