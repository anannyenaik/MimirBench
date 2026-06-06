# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Stage 9: a paper-style report consolidating evals, robustness, training, and
  interpretability with polished figures, tables, and limitations.
- Natural-language task generators for `market_making`, `prediction_markets`, and
  `adversarial_risk`.

## [0.2.0] — 2026-06-06

The alpha-stage stable review target for the public repository. Adds real-model provider artefacts,
robustness probes, the medium transformer model organism and its interpretability
result, and — new in this release — an official benchmark protocol, statistical
validity over saved artefacts, deepened (position-resolved) interpretability, and
release/artifact hygiene. **No paid API calls are made by any of this; all
real-model statistics are computed from saved artefacts.**

### Added — benchmark protocol and statistical validity
- **`BENCHMARK_PROTOCOL.md`** — two official tracks (strict-512 and best-valid) and
  explicit row-classification rules (clean / protocol-limited / provider-failed /
  rescue probe / smoke / diagnostic / non-model).
- **`STATISTICAL_VALIDITY.md`** and `mimirbench statistical-validity` — seeded
  bootstrap 95% CIs (mean score, pass, parse-fail, risk-violation), paired
  task-aligned deltas, per-row n and latency, generated to
  `reports/runs/leaderboard/statistical_validity_existing_artifacts.md` from saved
  `results.jsonl` only (no model is run).
- **Row reclassification** — curated track labels emitted into `reports/INDEX.md`
  so protocol/probe artefacts are never confused with capability rows.

### Added — deepened interpretability (local-only, no API calls)
- **Position-resolved (token-group) activation patching** plus a
  **mismatched-donor negative control** and a **label-shuffle probe control**
  (`mimirbench run-extended-interpretability`). On the medium checkpoint: a matched
  whole-site patch recovers the action on 0.967 of flipped pairs vs 0.533 for an
  unrelated donor; single token-group patches recover ≤2%, showing the
  evidence→decision signal is distributed across positions; the action probe scores
  1.000 on real vs 0.484 on shuffled labels.
- **Six-seed replication (seeds 123–128).** Layer-0 MLP action recovery is 0.000
  on every seed while layer-0/1 attention recovery is 0.964/0.989 (mean);
  matched/mismatched donor action recovery is 0.964/0.496; the real/shuffled
  action probe is 1.000/0.471.
- **Per-head and individual-token analysis.** Projected per-head outputs are now
  patchable and ablatable. Across six seeds, no head dominates consistently; the
  best mean single-head action recovery is 0.141, the largest mean zero-ablation
  degradation is 0.051 action accuracy / 0.314 posterior accuracy, and
  individual-position action recovery is effectively zero.
- Artefacts: `reports/interpretability/interp_bayes_medium_extended/`,
  `reports/interpretability/interp_bayes_multiseed_summary.md`, and
  `reports/interpretability/interp_bayes_head_token_summary.md` (plus JSON).

### Added — artifact inspectability and release hygiene
- **`ARTIFACTS.md`** and curated **`MODEL_CARD_medium.md`** — what is committed vs
  gitignored, SHA256 checksums for the medium checkpoint, and exact reproduce
  commands.
- **`RELEASE_NOTES_v0.2.0.md`** and this `[0.2.0]` entry.
- Package metadata bumped to `0.2.0` with Alpha development status.
- The medium `best.pt` checkpoint and `vocab.json` are attached to the v0.2.0
  GitHub release as convenience assets while `.pt` files remain gitignored.

### Fixed
- pytest no longer rewrites tracked `reports/model_cards/` files with
  machine-specific temp paths: `train()` / `evaluate_checkpoint()` (and the
  matching CLI commands) take a `model_card_dir`, tests isolate it, and four
  test-artefact cards were removed from the tree.

### From the real-model provider phase (carried into 0.2.0)
- Direct-agent leaderboard artefacts for OpenAI, Claude, and Gemini on the
  synthetic 20-tasks-per-environment protocol, plus targeted robustness probes.
  Strongest clean rows: OpenAI `gpt-5.4` (strict-512), Claude Sonnet 4.6
  (`max_tokens=1536`, best-valid), Gemini `gemini-3.1-pro-preview`
  (`thinking_level=low`, best-valid), and Gemini `gemini-3.5-flash`
  (`thinking_budget=0`, best-valid). A forced Bayesian tool-use run was kept as a
  diagnostic only.

### From Stage 5/6/7/8 (carried into 0.2.0)
- Provider-agnostic `ModelClient` (OpenAI/Anthropic/Gemini/generic-HTTP/local HF),
  deterministic parsing/repair (no LLM judge), a sandboxed audited tool agent, and
  cost/latency reporting.
- Comparison runner, plots, model cards, report index, and failure taxonomy.
- Synthetic Bayesian trace generation, a compact transformer, held-out evaluation,
  and the medium model organism (321,455 params; 12,000 / 2,000 / 2,000 traces)
  reaching ~0.990 held-out posterior-bucket accuracy with 1.000 action/risk
  accuracy.
- Mechanistic interpretability (activation capture, linear probes,
  clean/corrupted activation patching, attention analysis). On the medium
  checkpoint, layer-0 attention patching restored the clean action on 118/122
  flipped pairs while layer-0 MLP restored 0/122 — a narrow causal model-organism
  result specific to that synthetic checkpoint, with no frontier-model transfer
  claim.

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

[Unreleased]: https://github.com/anannyenaik/MimirBench/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/anannyenaik/MimirBench/releases/tag/v0.2.0
[0.1.0]: https://github.com/anannyenaik/MimirBench/releases/tag/v0.1.0
