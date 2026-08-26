# Evaluation Guide

MimirBench turns seeded synthetic tasks into graded, aggregate reports. Six
runnable environment families share the same config-driven runner, with
agent resolution, response caching, optional concurrency, structured per-task
records, and report writers.

## Runner Flow

```text
EvalRunConfig
  -> registry.get(environment)
  -> resolver.resolve_agent(agent config)
  -> generator(seed + i) -> TaskInstance(task, key)
  -> cache lookup by agent config, task payload, environment, package version
  -> agent.act(task) or diagnostic_mock.act_with_key(task, key)
  -> grader(task, response, key)
  -> EvalTaskRecord
  -> results.jsonl, summary.json, report.md
```

The legacy Python API still accepts `EvalConfig` and returns `EvalReport` for one
environment. New YAML configs use `EvalRunConfig` with `run`, `agent`,
`environments`, and `reporting` sections.

## Robustness Runner Flow

Base-vs-variant evaluations use `RobustnessRunConfig`:

```text
RobustnessRunConfig
  -> registry.get(environment)
  -> resolver.resolve_agent(agent config)
  -> generator(seed + i) -> base TaskInstance
  -> VariantGenerator(base task) -> deterministic variants
  -> run agent on base and each variant
  -> grade base and each variant with deterministic graders
  -> RobustnessRecord(base score/action vs variant score/action)
  -> robustness metrics, failure cases, and artefacts
```

Each robustness record contains the parent task id, variant id, variant type,
environment, answer-preserving flag, base and variant scores, score delta,
canonical actions, action-change flag, invalid/unsafe transitions, pressure
susceptibility, violations, notes, and prompt/response metadata for triage.

## Config Format

```yaml
run:
  name: bayes_reference_smoke
  seed: 123
  output_dir: reports/runs/bayes_reference_smoke
  cache: true
  cache_bypass: false
  max_workers: 1

agent:
  type: reference

environments:
  - name: bayesian_games
    num_tasks: 100
    seed: 123

reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
```

`max_workers` controls task-level concurrency. Results are sorted back into
deterministic task order before writing.

## Agents

All agents implement `BaseAgent.act(task: Task) -> ModelResponse`.

- `ReferenceAgent` calls an environment reference solver on public task metadata.
  It is a sanity check, not a model.
- `AlwaysAbstainAgent`, `RandomValidAgent`, and `NoisyReferenceAgent` are
  deterministic mock/diagnostic baselines.
- `APIModelAgent` is a `DirectAgent` over a provider-agnostic `ModelClient`
  (OpenAI, Anthropic, or a generic OpenAI-compatible HTTP endpoint), importing the
  provider SDK lazily.
- `LocalModelAgent` is a `DirectAgent` over an `HFLocalClient` and imports
  `transformers`/`torch` lazily.
- `ReflectiveAgent` wraps a direct backend with draft, critique, and revision.
- `tool` resolves to a concrete tool-using agent: a deterministic `reference`
  policy or a model-backed `model` policy. Both run a bounded, audited act/observe
  loop over sandboxed tools. See [TOOLS.md](TOOLS.md).

Real agents receive only `Task`. Prompts are environment-aware
([`mimirbench/agents/prompts.py`](mimirbench/agents/prompts.py)) and responses are
parsed/repaired deterministically
([`mimirbench/agents/parsing.py`](mimirbench/agents/parsing.py)); no second LLM
is used to judge or repair. The noisy reference mock is explicitly diagnostic and
uses `GradingKey` through a separate `act_with_key` path; no real or tool agent
ever receives the `GradingKey`. See [MODELS.md](MODELS.md) for backends.

## Records

Each evaluated task writes an `EvalTaskRecord` with:

- `run_id`, `timestamp`, `environment`, `task_id`, `seed`
- `agent_type`, `agent_name`
- `raw_prompt`
- `model_response`
- `parsed_response`
- `grader_result`
- `latency_ms`
- `error`

Records do not include hidden chain-of-thought. Agents are instructed to return
concise reasoning summaries and machine-readable JSON answers.

## Caching

`mimirbench/evals/cache.py` implements an append-only JSONL response cache.

The cache key depends on:

- agent config
- environment name
- task id and public task payload
- package version

Cache bypass is available with `run.cache_bypass: true`. Cache read failures
raise clear runtime errors rather than silently hiding corrupt rows. Responses
with agent errors are not cached.

## Scoring

`mimirbench/evals/scoring.py` aggregates:

- mean score and pass rate
- posterior error metrics where graders provide them
- regret where environments provide it
- expected-value error where graders provide it
- risk, budget, quote, and pressure metrics where graders provide them
- calibration statistics where graders provide them
- invalid response rate
- parse failure rate
- runtime error rate
- latency mean, p50, and p95

Metrics are averaged only over tasks that report them, so mixed-environment runs
remain well defined.

For hosted/local-model runs, `aggregate_cost_latency` adds a `cost_latency` block to the
summary: `total_input_tokens`, `total_output_tokens`, `total_tokens`,
`estimated_total_cost_usd` (only when `pricing` is configured; otherwise `null`
with a `cost_note`), `mean/p50/p95_latency_ms`, `timeout_rate`,
`provider_error_rate`, `parse_failure_rate`, and `invalid_response_rate`. Token
usage and cost are read from each record's
`metadata.response_metadata.usage`. Tool-agent runs additionally emit a
`tool_audit` block and `tool_audit.jsonl` / `tool_audit.md` (see
[TOOLS.md](TOOLS.md)).

## Robustness Config Format

```yaml
run:
  name: robustness_mock_all_envs
  seed: 123
  output_dir: reports/runs/robustness_mock_all_envs
  cache: true
  max_workers: 1

agent:
  type: mock
  behaviour: random_valid
  seed: 123

environments:
  - name: bayesian_games
    num_tasks: 15
    seed: 123
    variants_per_task: 5
    variant_types:
      - paraphrase
      - irrelevant_context
      - misleading_authority
      - emotional_pressure
      - order_permutation

robustness:
  answer_preserving_only: false
  max_variants_per_task: 5
  include_base_records: true
  extract_failure_cases: true
  max_failure_cases: 30

reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
  write_failure_cases: true
```

Available variant types are listed by:

```bash
mimirbench list-variant-types
```

Robustness metrics include paraphrase consistency, mean and worst score drop,
action flip rate, invalid response increase, unsafe action increase, risk
violation increase, pressure susceptibility, order invariance, distractor
robustness, and environment/variant-type breakdowns. Base records are written
only when `include_base_records` is true and are ignored by aggregate metrics.

Failure-case extraction ranks diagnostic cases such as largest score drops, base
correct to variant wrong, base safe to variant unsafe, paraphrase action flips,
pressure-induced risk violations, overconfident wrong answers, ignored tool
results, invalid JSON or parse failures, and high-regret failures.

## Environment Metrics

`bayesian_games` and `hidden_regimes` grade posterior distributions with total
variation, L1, and max-error metrics. `auctions` grades expected surplus with
absolute and relative expected-value error.

`market_making` generates one-shot synthetic quote decisions with mid price,
inventory, position limits, daily loss state, volatility, displayed spread,
adverse-selection risk, arrival intensity, and risk aversion. Agent responses
include bid/ask prices, bid/ask sizes, `reduce_inventory`, `abstain`,
confidence, and a concise reasoning summary. The grader reports
`quote_validity`, `spread_reasonableness`, `inventory_risk_score`,
`risk_limit_violation`, `adverse_selection_penalty`, and `abstention_quality`.
Hard loss or position-limit violations are constraint-gated.

`prediction_markets` generates binary event tasks with a current YES price,
prior probability, private signal, signal reliability, market-impact parameter,
transaction cost, position limit, budget limit, and optional public evidence.
The reference solver computes a posterior probability, compares fair probability
to price after synthetic cost/impact, and sizes conservatively. The grader reports
`fair_probability_error`, `expected_value_error`, `action_optimality`, `regret`,
`calibration_proxy`, `risk_limit_violation`, and `abstention_quality`.

`adversarial_risk` generates risk-control decisions with current exposure,
current loss, proposed trade, maximum exposure, maximum daily loss, explicit
risk policy, and adversarial pressure text. Pressure types include authority,
urgency, loss chasing, fake insider signal, emotional pressure, ignore-constraints
framing, fake system status, recent-win bias, and confident irrelevant analyst
claims. The grader reports `risk_limit_adherence`, `unsafe_action`,
`pressure_susceptibility`, `correct_constraint_identified`, and
`safe_reduction_quality`. Unsafe approvals receive severe penalties.

## Writers

`mimirbench/evals/writers.py` writes:

- `results.jsonl` - per-task records
- `summary.json` - aggregate machine-readable metrics
- `report.md` - a human-readable report

For robustness runs it also writes:

- `robustness_results.jsonl` - base-vs-variant records
- `robustness_summary.json` - aggregate robustness metrics
- `robustness_report.md` - a human-readable robustness report
- `failure_cases.jsonl` and `failure_cases.md` - ranked diagnostic failures

Markdown reports include the run name, timestamp, agent, environments, task
counts, aggregate metrics, failure examples, scope and limitations, and a warning
when the agent is reference or mock rather than a hosted/local model.

## CLI

```bash
mimirbench list-envs
mimirbench validate-config configs/eval_mock_bayes.yaml
mimirbench run-eval configs/eval_mock_bayes.yaml
mimirbench summarise-run reports/runs/bayes_mock_smoke
mimirbench list-variant-types
mimirbench run-robustness configs/robustness_mock_all_envs.yaml
mimirbench summarise-robustness reports/runs/robustness_mock_all_envs
# Hosted-model and tool commands:
mimirbench check-provider openai
mimirbench estimate-run-cost configs/eval_api_openai_bayes_smoke.yaml
mimirbench inspect-failures reports/runs/<run_name>
mimirbench inspect-tool-audit reports/runs/<run_name>
```

Validation checks the pydantic schema, registered environments, and agent
resolver. It does not call remote APIs or load local model weights.
`check-provider` confirms package/key availability without printing the key;
`estimate-run-cost` gives a rough pre-run token estimate (and cost only if pricing
is configured).

## Adding an Environment

1. Create `environments/<name>/{schemas,generator,solver,grader}.py`.
2. `generator.generate_task(seed)` returns `TaskInstance`.
3. `solver.reference_solver(task)` returns the structured reference answer.
4. `grader.grade(task, response, key)` returns `GraderResult`.
5. Add `build_spec()` and register it in `evals/registry.load_builtin_environments`.
6. Add determinism and reference-solver tests.
