# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Full hosted-model benchmark protocol package:** strict-512 and best-valid
  configs for 100 tasks/environment x 3 seeds and 200 tasks/environment x 5
  seeds, plus exact inclusion/exclusion rules in `FULL_BENCHMARK_PROTOCOL.md`.
- **No-execute full benchmark planner:** `mimirbench plan-full-benchmark` writes
  call, token, configured-pricing cost, artefact-path, and exact-run-command
  manifests under `reports/plans/` without checking or calling providers.
- **Pilot-variance power planning:** `mimirbench power-plan-full-benchmark`
  estimates approximate CI widths from saved pilot artefacts only.
- **Free full-scale infrastructure validation:** reference and deterministic mock
  controls each completed 6,000 tasks (200/environment x 5 seeds x 6
  environments) with no hosted/API calls. These are not capability results.

### Changed
- Public docs now state explicitly that all hosted-model results remain
  pilot-scale and that funded full hosted-model runs are implemented but unrun;
  larger hosted-model rows are not simulated or fabricated.
- Documentation, docstrings, comments, and CLI help reworked for consistent
  research-engineering prose. Internal "Stage N" development labels were replaced
  with descriptive names throughout, including the affected test modules and the
  exported `TAXONOMY_FAILURE_LABELS` (previously `STAGE6_FAILURE_LABELS`).

### Fixed
- `mimirbench --version` reported `0.1.0` while the package declared `0.2.0`.
  `mimirbench.__version__` is now the single source of truth, checked against
  `pyproject.toml` by a test. The response cache's fallback version matches it,
  so running from an uninstalled checkout no longer silently misses every cached
  response.
- Artefacts recorded paths using the host's separator, so runs on Windows wrote
  `reports\runs\...` into committed JSON and Markdown. Paths now go through
  `mimirbench.artefacts.artefact_path`, and the committed artefacts were
  normalised to POSIX form.
- Artefact writers now emit LF endings explicitly, so regenerating a report on
  Windows produces a byte-identical file rather than a whitespace-only diff.
- Leaderboard model cards no longer repeat the leaderboard and model names in
  their filename. The longest tracked path drops from 284 to 181 characters, so
  the repository can be cloned on Windows without `core.longpaths`.
- Removed the changelog link to a `v0.1.0` release that was never tagged.

## [0.2.0] - 2026-06-06

The stable review target for the public repository. Adds hosted-model provider
artefacts, robustness probes, the medium transformer model organism and its
interpretability result, an official benchmark protocol, uncertainty analysis
over saved artefacts, position-resolved interpretability, and a documented
artefact policy.

### Added: benchmark protocol and statistical validity
- **`BENCHMARK_PROTOCOL.md`**: two official tracks (strict-512 and best-valid) and
  explicit row-classification rules (clean / protocol-limited / provider-failed /
  rescue probe / smoke / diagnostic / non-model).
- **`STATISTICAL_VALIDITY.md`** and `mimirbench statistical-validity`: seeded
  bootstrap 95% CIs (mean score, pass, parse-fail, risk-violation), paired
  task-aligned deltas, per-row n and latency, generated to
  `reports/runs/leaderboard/statistical_validity_existing_artifacts.md` from saved
  `results.jsonl` only (no model is run).
- **Row reclassification**: curated track labels emitted into `reports/INDEX.md`
  so protocol/probe artefacts are never confused with capability rows.

### Added: deepened interpretability (local-only, no API calls)
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

### Added: artefact inspectability and release hygiene
- **`ARTIFACTS.md`** and curated **`MODEL_CARD_medium.md`**: what is committed vs
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

### Carried into 0.2.0 from earlier development
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
  flipped pairs while layer-0 MLP restored 0/122, a narrow causal model-organism
  result specific to that synthetic checkpoint, with no frontier-model transfer
  claim.

## 0.1.0 - 2026-06-02

Initial repository foundation, never tagged as a release. No benchmark results
are claimed.

### Added
- **Shared contracts**: pydantic schemas for `Task`, `GradingKey`, `TaskInstance`,
  `ModelResponse`, `GraderResult`, `EvalConfig`, `EvalReport`.
- **Deterministic tools**: Bayesian posterior calculator, risk checker, sealed-bid
  auction surplus helper, expected-value helper, and a synthetic price-path simulator.
- **Environments**: fully implemented and registered `bayesian_games`, `auctions`,
  and `hidden_regimes`; scaffolds with real primitives for `market_making`,
  `prediction_markets`, and `adversarial_risk`.
- **Eval harness**: environment registry, runner, scoring/aggregation, seeded
  bootstrap, and paraphrase / adversarial variant generators.
- **Agents**: `BaseAgent`, `ReferenceAgent`, `DirectAgent`, `ToolAgent`,
  `ReflectiveAgent`, and lazy-loading `LocalModelAgent` / `APIModelAgent`.
- **Analysis**: calibration (ECE, Brier, reliability curve), regret, robustness, and
  matplotlib plotting helpers.
- **Training**: symbol tokenizer, synthetic regime dataset, Bayes-optimal NLL
  baseline, and guarded small-transformer train/eval scaffolds.
- **Interpretability**: ridge linear probe, attention summaries, activation-patching
  data structures, SAE config, and the experiment plan-as-data.
- **CLI**: `mimirbench` with `list-envs`, `validate-config`, and `run-eval`.
- **Tooling**: `pyproject.toml` (hatchling), ruff, mypy, pytest, pre-commit, and a
  GitHub Actions CI workflow (ruff + mypy + pytest).
- **Docs**: README, DESIGN, EVALS, INTERPRETABILITY, RESULTS, CONTRIBUTING.

[Unreleased]: https://github.com/anannyenaik/MimirBench/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/anannyenaik/MimirBench/releases/tag/v0.2.0
