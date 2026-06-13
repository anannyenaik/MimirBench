# Tools

MimirBench's tool-using agents can call a small set of **deterministic, offline**
tools to compute intermediate quantities before answering. This document covers
the allowed tools, the act/observe loop, the audit log, and the safety
boundaries.

## Allowed tools

All tools live in a fixed registry
([`mimirbench/agents/tools_registry.py`](mimirbench/agents/tools_registry.py))
and wrap the same primitives the graders use, so a tool-using agent can, in
principle, compute exactly the answer it is graded against.

| Tool | Computes | Argument shape |
| --- | --- | --- |
| `bayes_calculator` | Exact discrete Bayesian posterior | `{priors, likelihood, observations}` |
| `ev_calculator` | Expected value / variance (optional best action) | `{payoffs, probabilities}` |
| `risk_checker` | Hard position/loss/inventory limit check | `{position, proposed_trade, max_abs_position, max_loss}` |
| `auction_solver` | Second-price IPV surplus/revenue/welfare | `{your_value, n_bidders, v_max}` |
| `market_simulator` | Deterministic synthetic mid-price path | `{n_steps, start, drift, volatility, seed}` |

### Per-environment allow-lists

A tool request is only executed if the tool is allowed for that environment:

| Environment | Allowed tools |
| --- | --- |
| `bayesian_games` | `bayes_calculator`, `ev_calculator` |
| `hidden_regimes` | `bayes_calculator`, `ev_calculator`, `market_simulator` |
| `auctions` | `auction_solver`, `ev_calculator` |
| `market_making` | `risk_checker`, `ev_calculator`, `market_simulator` |
| `prediction_markets` | `bayes_calculator`, `ev_calculator`, `risk_checker` |
| `adversarial_risk` | `risk_checker`, `ev_calculator` |

Override per run with `allowed_tools: [...]` in the agent config.

## The act/observe loop

The loop lives in [`mimirbench/agents/tool_agent.py`](mimirbench/agents/tool_agent.py)
and is bounded by `tool_max_steps` (**default 3**):

1. the policy proposes a JSON action: either `{"tool": name, "arguments": {..}}`
   or `{"final": {..}}`;
2. the harness **validates** the requested tool against the environment
   allow-list;
3. allowed calls are executed deterministically; the output is appended as an
   observation;
4. invalid requests (disallowed or unknown tool) are **recorded and skipped** —
   never executed — and the loop continues safely;
5. when the policy returns a final answer, or the step budget is exhausted, the
   loop stops and returns a structured response.

Two policies ship:

- **`reference`** — a deterministic, non-model baseline that consults an allowed
  tool and answers from the tool output (or the environment's public reference
  solver). Fully reproducible; used to exercise and test the loop. **Not a model
  result.**
- **`model`** — a model-backed policy that asks a `ModelClient` to propose tool
  calls and a final answer in JSON.

```yaml
agent:
  type: tool
  tool_policy: reference      # or: model (+ provider/model for an API backend)
  tool_max_steps: 3
```

## Audit logs

Every step (valid or invalid) is recorded. A tool-agent run writes:

- `reports/runs/<run_name>/tool_audit.jsonl` — one row per step;
- `reports/runs/<run_name>/tool_audit.md` — a human-readable summary.

Each row records: `task_id`, `environment`, `agent`, `step_number`,
`requested_tool`, `tool_arguments`, `validation_status` (`allowed` /
`not_allowed` / `unknown_tool` / `no_tool_requested`), `tool_output`,
`tool_error`, `final_answer_used_tool_result`, and `latency_ms`.

Inspect a run:

```bash
mimirbench run-eval         configs/eval_tool_reference_bayes.yaml
mimirbench inspect-tool-audit reports/runs/tool_reference_bayes
```

### Metrics

The audit aggregates ([`mimirbench/evals/tool_audit.py`](mimirbench/evals/tool_audit.py)):

- `tool_call_rate` — fraction of tasks that requested ≥1 tool;
- `invalid_tool_call_rate` — invalid requests / all tool requests;
- `tool_error_rate` — tool execution errors / executed calls;
- `mean_tool_steps` — average tool requests per task;
- `final_answer_after_tool_rate` — tasks that produced a final answer after a
  tool call;
- `tool_result_ignored_rate` — tasks whose final answer used **none** of the
  available tool outputs, where the heuristic can decide.

`final_answer_used_tool_result` and `tool_result_ignored_rate` are deterministic
**numeric-overlap heuristics**: a tool output counts as "used" when a number it
produced reappears (within tolerance) in the final answer. When there is nothing
numeric to compare, the value is reported as `unknown` (`null`) — never guessed.

## Limitations and safety

- **Deterministic and sandboxed.** Tools are pure functions over their arguments:
  no randomness beyond an explicit `seed`, no global state, no filesystem, and
  **no network**. The same call always yields the same result, which is why a
  tool answer can be graded exactly.
- **No arbitrary code execution.** Tools are a *fixed registry*. There is no
  `eval`, no shell, and no way to register or call code outside the five tools.
  Anything else the model requests is logged as an invalid call and skipped.
- **No ground-truth access.** Tools and policies only ever receive the public
  `Task` (and prior tool observations). The `GradingKey` is never passed to a
  tool or an agent, so the answer cannot leak through a tool.
- **Bounded.** At most `tool_max_steps` tool calls per task keeps cost, latency,
  and audit logs small and predictable.
- **No hidden chain-of-thought.** The tool prompt asks for one JSON action per
  turn and a brief `reasoning_summary`; it never requests private reasoning.

See [MODELS.md](MODELS.md) for model backends and [EVALS.md](EVALS.md) for the
overall harness.
