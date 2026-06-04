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

### Added — real-model provider phase
- Direct-agent leaderboard artefacts for OpenAI, Claude, and Gemini on the
  synthetic 20-tasks-per-environment protocol, plus targeted robustness probes.
  Strongest clean rows: OpenAI `gpt-5.4`, Claude Sonnet 4.6 (`max_tokens=1536`),
  Gemini `gemini-3.1-pro-preview` (`thinking_level=low`), and Gemini
  `gemini-3.5-flash` (`thinking_budget=0`) for the non-Pro tier.
- A forced Bayesian tool-use run was kept as a diagnostic only; it showed
  negligible gain over direct answering at higher latency. Results are
  preliminary, synthetic, and not statistically conclusive.

### Added — Stage 6/7/8 (reporting, synthetic transformer, interpretability)
- Comparison runner, plots, model cards, report index, and failure taxonomy.
- Synthetic Bayesian trace generation, a compact transformer, held-out
  evaluation, and a medium model organism (321,455 params; 12,000 / 2,000 /
  2,000 traces) reaching ~0.990 held-out posterior-bucket accuracy with 1.000
  action/risk accuracy.
- Mechanistic interpretability (activation capture, linear probes,
  clean/corrupted activation patching, attention analysis). On the medium
  checkpoint, layer-0 attention patching restored the clean action on 118/122
  flipped pairs while layer-0 MLP restored 0/122 — a narrow causal
  model-organism result specific to that synthetic checkpoint, with no
  frontier-model transfer claim.

### Planned
- Stage 9: a paper-style report consolidating evals, robustness, training, and
  interpretability with polished figures, tables, and limitations.
- Natural-language task generators for `market_making`, `prediction_markets`, and
  `adversarial_risk`.

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

[Unreleased]: https://github.com/anannyenaik/MimirBench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/anannyenaik/MimirBench/releases/tag/v0.1.0
