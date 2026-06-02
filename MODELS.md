# Models

How to run MimirBench against real models — hosted APIs or local Hugging Face
weights — and how to do so **without** accidentally running an expensive
benchmark.

MimirBench's core harness and test suite never import a model SDK. Provider
support is loaded lazily, so `pip install -e ".[dev]"` is enough to develop and
test; you only install model extras when you actually want to run a model.

## Provider matrix

| Backend | `agent.type` | `agent.provider` | Package | Key env var | Cost estimate |
| --- | --- | --- | --- | --- | --- |
| OpenAI-compatible | `api` | `openai` | `openai` (`.[api]`) | `OPENAI_API_KEY` | only if `pricing` configured |
| Anthropic | `api` | `anthropic` | `anthropic` | `ANTHROPIC_API_KEY` | only if `pricing` configured |
| Generic HTTP (OpenAI-shaped) | `api` | `generic_http` | none (stdlib) | `MIMIRBENCH_LLM_API_KEY` (optional) | only if `pricing` configured |
| Local Hugging Face | `local` | — | `torch`+`transformers` (`.[ml]`) | none | never (no provider billing) |

The provider-agnostic contract lives in
[`mimirbench/agents/model_client.py`](mimirbench/agents/model_client.py):
`ModelClient`, `ModelRequest`, `ModelResponseEnvelope`, `ModelUsage`,
`ModelClientError`, `RetryConfig`, and `Pricing`.

## API keys (environment variables only)

Keys are read from environment variables by the client. They are **never** read
from a config file and **never** written to any run record, summary, or log.

```bash
export OPENAI_API_KEY=sk-...        # OpenAI
export ANTHROPIC_API_KEY=sk-ant-... # Anthropic (optional support)
```

To use a non-default variable name, set `api_key_env` in the agent config (the
value still comes from the environment, not the config).

Check availability without making a call (the key value is never printed):

```bash
mimirbench check-provider openai
mimirbench check-provider anthropic
mimirbench check-provider local
```

`check-provider` reports whether the package is installed, whether the key env
var is set, and whether the provider therefore *appears* usable.

## Optional dependencies

```bash
pip install -e ".[api]"   # openai client
pip install anthropic     # optional Anthropic support
pip install -e ".[ml]"    # torch + transformers for local models
```

Missing packages and missing keys raise a clear, actionable `ModelClientError`
(e.g. *"OpenAI support requires the 'api' extra"* or *"No OpenAI API key found.
Set the OPENAI_API_KEY environment variable"*). Nothing is silently skipped.

## Local models

```yaml
agent:
  type: local
  model_name: Qwen/Qwen2.5-0.5B-Instruct
  device: auto            # auto | cpu | cuda | mps
  temperature: 0
  do_sample: false
  max_new_tokens: 512
```

- `device: auto` prefers CUDA, then Apple MPS, then CPU.
- Weights download on first use; pick a small instruct model you have cached.
- Local inference has no provider billing, so cost is always reported as
  **"not estimated"**.

## Running a tiny smoke eval

Always estimate first, then run the smallest possible config:

```bash
mimirbench check-provider openai
mimirbench estimate-run-cost configs/eval_api_openai_bayes_smoke.yaml
mimirbench run-eval         configs/eval_api_openai_bayes_smoke.yaml
mimirbench summarise-run    reports/runs/api_openai_bayes_smoke
mimirbench inspect-failures reports/runs/api_openai_bayes_smoke
```

Stage 5 ships these tiny real-model configs (5–20 tasks, cache on,
`max_workers: 1`, `temperature: 0`):

| Config | Backend | Scope |
| --- | --- | --- |
| `configs/eval_api_openai_bayes_smoke.yaml` | OpenAI | 10 Bayesian tasks |
| `configs/eval_api_openai_all_envs_tiny.yaml` | OpenAI | 5 tasks × 6 families |
| `configs/eval_api_openai_robustness_bayes_tiny.yaml` | OpenAI | robustness probe |
| `configs/eval_local_bayes_smoke.yaml` | local HF | 10 Bayesian tasks |
| `configs/eval_local_all_envs_tiny.yaml` | local HF | 5 tasks × 6 families |
| `configs/eval_tool_api_openai_bayes_smoke.yaml` | OpenAI + tools | tool loop |

## Cost and latency

- `estimate-run-cost` gives a **pre-run** estimate using ~4 characters/token on
  one representative task per environment and an upper-bound output length. It is
  deliberately approximate and never claims an exact cost.
- After a run, `summary.json` and `report.md` include `total_input_tokens`,
  `total_output_tokens`, `total_tokens`, `estimated_total_cost_usd`,
  `mean/p50/p95_latency_ms`, `timeout_rate`, `provider_error_rate`,
  `parse_failure_rate`, and `invalid_response_rate`.
- **Cost is `null` unless pricing is configured.** Add a `pricing` block to the
  agent config to opt in:

  ```yaml
  agent:
    type: api
    provider: openai
    model: gpt-4.1-mini
    pricing:
      input_usd_per_1k: 0.0      # set to your contracted prices
      output_usd_per_1k: 0.0
  ```

  Without it, reports say cost was **"not estimated"** rather than `$0`.

## Avoiding accidental expensive benchmarks

- Tests never call APIs or download models; API/local configs are **validated**,
  never executed, by the suite.
- Keep `num_tasks` small (the shipped configs use 5–20) and `max_workers: 1`.
- `cache: true` deduplicates identical (agent, task) calls so re-runs are free.
- Always run `estimate-run-cost` before a paid run.
- Tool-using model agents make up to `tool_max_steps + 1` calls per task — budget
  accordingly.

## Honesty guarantees

- No hidden chain-of-thought is requested or stored. Anthropic "thinking" output
  is **not** enabled. Prompts ask only for a brief `reasoning_summary`.
- Real-model reports are labelled with provider, model, config, timestamp, token
  usage, and a cost estimate **only if** pricing was configured.
- Reference and mock reports are labelled as non-model baselines and must never be
  reported as model performance.
- Transient failures are retried with bounded backoff; auth/4xx errors are not
  retried. Exhausted retries surface as recorded errors, not crashes.

See [TOOLS.md](TOOLS.md) for the tool-using agent, and [RESULTS.md](RESULTS.md)
for the current (pending) state of real-model results.
