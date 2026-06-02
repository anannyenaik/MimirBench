# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Stage 5 (real model integration and tool-agent infrastructure)
- **Model client** — provider-agnostic `ModelClient`, `ModelRequest`,
  `ModelResponseEnvelope`, `ModelUsage`, `ModelClientError`, `RetryConfig`, and
  `Pricing`, with bounded retries, timeouts, and honest (pricing-gated) cost.
- **Providers** — lazy `OpenAIClient`, `AnthropicClient`, `GenericHTTPClient`, and
  `HFLocalClient` (device auto/cpu/cuda/mps); `APIModelAgent` / `LocalModelAgent`
  rebuilt on top of them.
- **Prompts & parsing** — environment-aware prompt builders (no hidden CoT) and
  deterministic JSON extraction / repair / validation (no LLM judge).
- **Tool agent** — fixed sandboxed tool registry with per-environment allow-lists,
  a bounded act/observe loop, and `ReferenceToolAgent` / `ModelToolAgent` policies.
- **Tool-use audit** — `tool_audit.jsonl` / `tool_audit.md` plus tool-use metrics.
- **Cost/latency reporting** — token totals, latency percentiles, and
  timeout/provider-error/parse-failure/invalid-response rates in summaries.
- **CLI** — `check-provider`, `estimate-run-cost`, `inspect-failures`,
  `inspect-tool-audit`.
- **Configs** — tiny API/local/tool smoke configs and a tiny API robustness probe.
- **Docs** — `MODELS.md`, `TOOLS.md`; README/EVALS/RESULTS/ROBUSTNESS updated.

### Planned
- First artefact-backed tiny real-model baselines (Stage 6) when keys/weights exist.
- Natural-language task generators for `market_making`, `prediction_markets`, and
  `adversarial_risk`.
- Small-transformer checkpoints and the belief-probe / activation-patching
  experiments.

## [0.1.0] — 2026-06-02

Initial repository foundation. No benchmark results are claimed.

### Added
- **Shared contracts** — pydantic schemas for `Task`, `GradingKey`, `TaskInstance`,
  `ModelResponse`, `GraderResult`, `EvalConfig`, `EvalReport`.
- **Deterministic tools** — Bayesian posterior calculator, risk checker, sealed-bid
  auction surplus helper, expected-value helper, and a toy price-path simulator.
- **Environments** — fully implemented and registered `bayesian_games`, `auctions`,
  and `hidden_regimes`; scaffolds with real primitives for `market_making`,
  `prediction_markets`, and `adversarial_risk`.
- **Eval harness** — environment registry, runner, scoring/aggregation, seeded
  bootstrap, and paraphrase / adversarial variant generators.
- **Agents** — `BaseAgent`, `ReferenceAgent`, `DirectAgent`, `ToolAgent`,
  `ReflectiveAgent`, and lazy-loading `LocalModelAgent` / `APIModelAgent`.
- **Analysis** — calibration (ECE, Brier, reliability curve), regret, robustness, and
  matplotlib plotting helpers.
- **Training** — symbol tokenizer, synthetic regime dataset, Bayes-optimal NLL
  baseline, and guarded small-transformer train/eval scaffolds.
- **Interpretability** — ridge linear probe, attention summaries, activation-patching
  data structures, SAE config, and the experiment plan-as-data.
- **CLI** — `mimirbench` with `list-envs`, `validate-config`, and `run-eval`.
- **Tooling** — `pyproject.toml` (hatchling), ruff, mypy, pytest, pre-commit, and a
  GitHub Actions CI workflow (ruff + mypy + pytest).
- **Docs** — README, DESIGN, EVALS, INTERPRETABILITY, RESULTS, CONTRIBUTING.

[Unreleased]: https://github.com/your-org/mimirbench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/mimirbench/releases/tag/v0.1.0
