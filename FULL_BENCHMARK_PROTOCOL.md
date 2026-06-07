# MimirBench full benchmark protocol

This package defines the funded, larger-scale hosted-model evaluation that
MimirBench is ready to run. The protocol, configs, no-execute cost planner, and
statistical planning are implemented. **The full hosted-model protocol has not
been run because external API budget is not available.** Larger hosted-model
results are intentionally not simulated or fabricated.

All MimirBench tasks remain deterministic synthetic benchmark tasks. Neither the
pilot nor a future full run supports a trading claim, a broad provider-superiority
claim, or an automatic statistical-significance claim.

## Scale tracks

| Scale | Tasks/environment/seed | Task seeds | Tasks/model | Status |
| --- | ---: | ---: | ---: | --- |
| Pilot | 20 | 1 (`123`) | 120 | Already run; all hosted-model rows remain labelled pilot |
| Full track A | 100 | 3 (`123`, `1123`, `2123`) | 1,800 | Implemented, costed, not run |
| Full track B | 200 | 5 (`123`, `1123`, `2123`, `3123`, `4123`) | 6,000 | Implemented, costed, not run |

Every model in one track uses the same six environment families and the same
task seeds. Pairing is by `(environment, task_id, seed)`.

## Protocol variants

### Strict-512

The strict-512 variant uses the shared deterministic parser, retry policy, task
IDs, and a 512-token output budget. Provider-required default decoding settings
are recorded in config and must not be changed after the run begins. A model that
cannot emit sufficiently clean answers under this budget becomes
`protocol-limited`; it is not silently moved into a clean capability table.

### Best-valid

The best-valid variant uses each provider/model's documented minimum settings
already shown by the pilot to emit valid JSON, such as a larger output budget or
a thinking setting. It is not identical-decoding across providers. It answers
how a model performs under a practical valid-output configuration, not which
provider is intrinsically superior.

## Full hosted configs and planned volume

| Config | Models | Tasks/model | Scheduled calls | Retry-attempt upper | Configured-price range |
| --- | ---: | ---: | ---: | ---: | ---: |
| `configs/full/leaderboard_strict_100env_3seeds.yaml` | 5 | 1,800 | 9,000 | 27,000 | $4.18-$29.61 |
| `configs/full/leaderboard_best_valid_100env_3seeds.yaml` | 4 | 1,800 | 7,200 | 21,600 | $7.67-$159.74 |
| `configs/full/leaderboard_strict_200env_5seeds.yaml` | 5 | 6,000 | 30,000 | 90,000 | $13.92-$98.71 |
| `configs/full/leaderboard_best_valid_200env_5seeds.yaml` | 4 | 6,000 | 24,000 | 72,000 | $25.56-$532.44 |

Scheduled calls count one direct-model request per task. The retry-attempt upper
assumes every scheduled call consumes all three configured attempts. It is a
capacity-planning bound, not a prediction.
Cost ranges use the pricing fields documented in each config: the lower bound is
estimated input cost only and the upper bound assumes every scheduled call uses
its full output budget. They exclude retries, taxes, cache effects, and future
provider price changes.

## Exact inclusion and exclusion rules

These rules apply to full hosted-model rows. Existing 20/environment rows retain
their published pilot classifications in
[BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md).

### Clean rows included in a headline track

A full row is `strict-track clean` or `best-valid clean` only when all are true:

1. Every planned `(environment, task_id, seed)` exists exactly once.
2. All configured tasks were attempted and saved: 1,800/model for track A or
   6,000/model for track B.
3. There are zero unrecovered provider/runtime errors.
4. Parse-failure rate is at most 1.0% for strict-512 or at most 2.0% for
   best-valid.
5. The config, parser, grader, retry policy, and inclusion rules were frozen
   before scores were inspected; any rerun uses the same task IDs and is disclosed.
6. Mean score, uncertainty, seed variation, pass, parse, risk, cost, and latency
   metrics are present.

Risk violations and low scores remain included as model outcomes. They do not
remove a row from the clean set when the row otherwise satisfies the rules.

### Rows excluded from headline capability comparisons

- **Protocol-limited:** all calls completed, but the row exceeds its track's
  parse-failure threshold because of truncation, empty output, hidden-token
  exhaustion, or another documented protocol constraint.
- **Provider-failed:** one or more unrecovered provider/runtime errors or missing
  planned task records.
- **Rescue probe:** at most 30 deliberately selected tasks used to isolate a
  setting or output-budget failure. Never promoted to a full row.
- **Smoke run:** at most 30 tasks used to exercise plumbing. Never a capability
  result.
- **Diagnostic run:** any forced-tool, robustness-only, provider-load, parser,
  reference, mock, or other run not preregistered as a full direct-agent track
  row.
- **Post-hoc mixed row:** results assembled from incompatible settings, task
  schedules, parser versions, or graders.

Excluded rows remain inspectable and must be labelled with their exclusion
reason. They cannot contribute to model/provider rankings or paired headline
deltas.

## Required full-run reporting

Each clean full row must report:

- mean score and a seeded 95% hierarchical bootstrap CI, resampling task seeds
  and then tasks within environment/seed cells;
- per-seed mean, seed-to-seed standard deviation, and seed range;
- paired mean-score deltas and paired bootstrap CIs only over exactly aligned
  `(environment, task_id, seed)` records;
- pass rate, parse-failure rate, and risk-violation rate, with uncertainty;
- total and per-task cost from observed usage when pricing is configured;
- mean, p50, and p95 latency, timeout rate, and provider-error rate;
- exact task/model counts, config hash, parser/grader version, and exclusions.

Full-run uncertainty may support narrower benchmark-specific statements, but it
does not erase synthetic-task limitations or establish broad provider
superiority. Pilot rows must not be described as statistically significant.

## No-execute planning

The planning command parses config, generates representative synthetic prompts,
and performs arithmetic only:

```bash
python -m mimirbench.cli plan-full-benchmark configs/full/leaderboard_best_valid_100env_3seeds.yaml
python -m mimirbench.cli power-plan-full-benchmark
```

It does not check providers, read credential values, or run inference. Manifests
are written under `reports/plans/`; pilot-variance CI-width planning is written to
`reports/runs/leaderboard/full_benchmark_power_plan.md`.

## Free infrastructure validation

The full-B task volume was exercised with non-paid controls only:

- `reports/runs/full_scale_reference_validation/`
- `reports/runs/full_scale_mock_validation/`

Each run contains 6,000 tasks: 200 tasks/environment, five seeds, all six
environments. These runs validate generation, grading, aggregation, caching, and
artefact writing at the planned scale. They are not hosted-model or model
capability results.
