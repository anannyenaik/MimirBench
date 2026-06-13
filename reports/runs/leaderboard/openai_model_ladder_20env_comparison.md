# Pilot OpenAI model-ladder comparison

Generated from saved artefacts on 2026-06-03 local time. This is a synthetic,
direct-agent-only comparison with 20 tasks per environment and six environments.
It is useful for model-ranking diagnostics inside this benchmark only. It is not
statistically conclusive, not a trading result, and not a broad model-superiority
claim.

## Source runs

| Run | Models used here | Config | Artefacts |
| --- | --- | --- | --- |
| `leaderboard_openai_minis_all_envs_direct_20` | `gpt-4.1-mini`, `gpt-5.4-mini` | `configs/leaderboard/leaderboard_openai_minis_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_minis_all_envs_direct_20/` |
| `leaderboard_openai_frontier_all_envs_direct_20` | `gpt-5.4` | `configs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_frontier_all_envs_direct_20/` |
| `leaderboard_openai_gpt55_all_envs_direct_20` | `gpt-5.5` | `configs/leaderboard/leaderboard_openai_gpt55_all_envs_direct_20.yaml` | `reports/runs/leaderboard/leaderboard_openai_gpt55_all_envs_direct_20/` |
| `leaderboard_openai_gpt55_rescue_probe` | `gpt-5.5` diagnostic probe only | `configs/leaderboard/leaderboard_openai_gpt55_rescue_probe.yaml` | `reports/runs/leaderboard/leaderboard_openai_gpt55_rescue_probe/` |

All rows use provider `openai`, agent `direct`, cache enabled, `max_workers=1`,
run seed `123`, environment seed `123`, and no robustness, tools, or reflective
agent. The ordered `(environment, task_id, seed)` keys match across all four
result files. The task set is:

- `bayesian_games`: 20 tasks
- `auctions`: 20 tasks
- `hidden_regimes`: 20 tasks
- `market_making`: 20 tasks
- `prediction_markets`: 20 tasks
- `adversarial_risk`: 20 tasks

## Compatibility note

The original frontier run attempted `gpt-5.5` with `temperature=0`; every call
failed with a 400 response because this model accepts only the default
temperature value. The rerun used the same task IDs/seeds and the same
direct-only benchmark, but the OpenAI client omitted the `temperature` request
field for `gpt-5.5`, so the API default temperature was used.

This completes the four-model ladder without rerunning the completed
`gpt-4.1-mini`, `gpt-5.4-mini`, or `gpt-5.4` cells. The default-temperature
`gpt-5.5` row is not a strictly temperature-paired row against the other three
models, so conclusions involving `gpt-5.5` should be read with that caveat.

The `gpt-5.5` rerun completed provider calls with no provider/runtime errors,
but 89/120 responses ended with `finish_reason="length"` and empty content under
the unchanged `max_tokens: 512` protocol. Those were scored as parse failures;
the row remains a protocol/output-budget failure rather than an interpretable
capability score.

A later six-task rescue probe tested a different API-compatible configuration:
temperature omitted, `max_tokens: 2048`, and Chat Completions
`reasoning_effort: low`. It produced 6/6 non-empty responses, 6/6
`finish_reason="stop"`, zero provider/runtime errors, zero parse failures, mean
score `0.857940`, and observed estimated cost `$0.131810`. This suggests the
empty-output failure is at least partly protocol / output-budget sensitive, but
the probe is not a replacement 120-task ladder row. A full rescued ladder rerun
with the successful settings was estimated at `$7.6568` upper bound and was not
run under the remaining-budget gate.

## Cost

The conservative upper estimate for the `gpt-5.5`-only rerun was `$2.1272`, below
the `$2.50` stop line. The observed estimated cost for that completed rerun was
`$1.878215`.

Observed estimated cost from successful model-call rows:

| Model | Observed estimated cost |
| --- | ---: |
| `gpt-4.1-mini` | `$0.038121` |
| `gpt-5.4-mini` | `$0.091214` |
| `gpt-5.4` | `$0.326270` |
| `gpt-5.5` | `$1.878215` |
| Four-row total | `$2.333820` |

Additional diagnostic spend: the six-task `gpt-5.5` rescue probe cost
`$0.131810` observed estimated. It is excluded from the four-row total because it
uses a different output/reasoning configuration and only six tasks.

## Overall comparison

| Model | Status | Tasks | Provider calls | Valid parsed | Task IDs/seeds match | Mean score | Pass rate | Parse failure | Provider/runtime error | Risk violation | Latency p50/p95 ms | Observed cost | Temperature protocol |
| --- | --- | ---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gpt-4.1-mini` | completed | 120 | 120 | 118 | yes | 0.619613 | 0.341667 | 0.016667 | 0.000000 | 0.025000 | 1451.6 / 2415.6 | `$0.038121` | `temperature=0` |
| `gpt-5.4-mini` | completed | 120 | 120 | 120 | yes | 0.611416 | 0.333333 | 0.000000 | 0.000000 | 0.016667 | 1146.1 / 1821.9 | `$0.091214` | `temperature=0` |
| `gpt-5.4` | completed | 120 | 120 | 120 | yes | 0.662963 | 0.425000 | 0.000000 | 0.000000 | 0.033333 | 2356.8 / 3623.0 | `$0.326270` | `temperature=0` |
| `gpt-5.5` | completed; high parse failure | 120 | 120 | 31 | yes | 0.213157 | 0.225000 | 0.741667 | 0.000000 | 0.000000 | 11993.4 / 14242.2 | `$1.878215` | API default; `temperature` omitted |

For `gpt-5.5`, most low-scoring cells are output-protocol failures rather than
provider failures: 89 responses had empty content with `finish_reason="length"`.

## Per-environment mean scores

| Environment | `gpt-4.1-mini` | `gpt-5.4-mini` | `gpt-5.4` | `gpt-5.5` |
| --- | ---: | ---: | ---: | ---: |
| `adversarial_risk` | 0.816500 | 0.825000 | 0.850000 | 0.850000 |
| `auctions` | 0.224283 | 0.032632 | 0.193458 | 0.200000 |
| `bayesian_games` | 0.740130 | 0.807899 | 0.883559 | 0.049994 |
| `hidden_regimes` | 0.754242 | 0.801071 | 0.848995 | 0.000000 |
| `market_making` | 0.646789 | 0.719257 | 0.772774 | 0.130000 |
| `prediction_markets` | 0.535734 | 0.482639 | 0.428989 | 0.048950 |

## gpt-5.5 parse-failure breakdown

| Environment | Parse failure | Empty `length` responses | Valid parsed |
| --- | ---: | ---: | ---: |
| `adversarial_risk` | 0.000000 | 0 | 20 |
| `auctions` | 0.800000 | 16 | 4 |
| `bayesian_games` | 0.950000 | 19 | 1 |
| `hidden_regimes` | 1.000000 | 20 | 0 |
| `market_making` | 0.750000 | 15 | 5 |
| `prediction_markets` | 0.950000 | 19 | 1 |

## Per-environment deltas

Candidate minus baseline. Deltas against `gpt-5.5` are shown as scored artefact
differences, but the row is not strict-temperature-paired and is dominated by
parse failures.

| Environment | `gpt-5.4-mini` vs `gpt-4.1-mini` | `gpt-5.4` vs `gpt-4.1-mini` | `gpt-5.4` vs `gpt-5.4-mini` | `gpt-5.5` vs `gpt-5.4` |
| --- | ---: | ---: | ---: | ---: |
| `adversarial_risk` | +0.008500 | +0.033500 | +0.025000 | +0.000000 |
| `auctions` | -0.191651 | -0.030825 | +0.160826 | +0.006542 |
| `bayesian_games` | +0.067768 | +0.143429 | +0.075661 | -0.833565 |
| `hidden_regimes` | +0.046829 | +0.094753 | +0.047924 | -0.848995 |
| `market_making` | +0.072468 | +0.125985 | +0.053517 | -0.642774 |
| `prediction_markets` | -0.053095 | -0.106745 | -0.053650 | -0.380039 |

## Non-monotonic patterns

- `gpt-5.4` remains the strongest completed row overall in this run, with mean
  score `0.662963` versus `0.619613` for `gpt-4.1-mini`, `0.611416` for
  `gpt-5.4-mini`, and `0.213157` for default-temperature `gpt-5.5`.
- Bigger was not uniformly better across environments. `gpt-5.4` improved
  `bayesian_games`, `hidden_regimes`, `market_making`, and `adversarial_risk`
  versus both mini models, but it remained below `gpt-4.1-mini` on `auctions`
  and was worse than both mini models on `prediction_markets`.
- The default-temperature `gpt-5.5` row tied `gpt-5.4` on `adversarial_risk` and
  narrowly exceeded `gpt-5.4` on `auctions`, but severe parse failures made it
  much weaker overall.
- `gpt-5.4-mini` was also non-monotonic versus `gpt-4.1-mini`: it improved
  Bayesian, hidden-regime, market-making, and adversarial-risk scores, but was
  worse on auctions and prediction markets.

## Reading

This is now a four-model OpenAI direct-agent ladder, but it is still
pilot: synthetic tasks, 20 tasks per environment, one agent mode, no
robustness, no tools, and one row (`gpt-5.5`) that used API-default temperature
because the model rejected `temperature=0`. It supports the same high-level
reading as before: `gpt-5.4` is the strongest OpenAI direct row in this benchmark
snapshot, and improvements are non-uniform. The `gpt-5.5` rerun does not overturn
that conclusion; instead, it adds a protocol caveat around default temperature
and empty length-limited responses under the existing 512-token output cap. The
rescue probe shows those empty responses can be avoided on a tiny slice with a
larger budget and lower reasoning effort, but the budget-gated full rerun was
skipped, so `gpt-5.5` remains unresolved under a strictly comparable full-ladder
protocol.
