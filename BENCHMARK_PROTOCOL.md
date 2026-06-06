# MimirBench benchmark protocol

This document defines the **official evaluation tracks** for MimirBench real-model
rows and the rules for labelling every saved run. It exists so that protocol
artefacts (output-budget truncation, provider load) are never confused with
capability results, and so that "which rows are comparable?" has one answer.

All rows below are **synthetic, pilot, 20-tasks-per-environment, single-seed**
results. Nothing here is a trading claim, a broad provider-superiority claim, or a
statistical-significance claim. See [STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md)
for bootstrap CIs over these same saved artefacts.

## Two official tracks

### A. Strict-512 track

A controlled, identical-decoding comparison. Every row in this track shares:

- the **same output budget** where applicable (`max_tokens=512`);
- the **same deterministic parser** (JSON extraction/repair, no LLM judge);
- the **same retry policy**;
- the **same task IDs and seeds** (20 tasks/environment across the six
  environments, identical across rows).

Truncation or empty-output rows under this track are **protocol findings**, not
capability failures — unless a row is explicitly scoped as strict-track behaviour
(i.e. "this model cannot emit valid JSON within 512 tokens" *is* the finding).

Strict-512 clean rows currently: OpenAI `gpt-4.1-mini`, `gpt-5.4-mini`, `gpt-5.4`;
Claude Haiku 4.5; Gemini Flash-Lite.

### B. Best-valid track

A practical "usable model under its documented protocol" comparison. Each provider
gets the **minimum documented settings needed to emit valid JSON** (for example a
larger output budget, or a thinking/decoding switch). This track is explicitly
**not identical-decoding**: rows use different output budgets or thinking settings,
so cross-row differences mix capability with protocol. It answers "how well does
each model do when configured to actually return parseable answers?".

Best-valid clean rows currently: Claude Sonnet 4.6 (`max_tokens=1536`); Gemini
Flash (`thinking_budget=0`); Gemini Pro Preview (`thinking_level=low`, cache-backed
retry, provider-load caveat). `gpt-5.4` is clean in both tracks (already clean at
512).

## Row classification rules

Every saved run is exactly one of the following. The curated mapping is emitted
into [reports/INDEX.md](reports/INDEX.md) (section "Real-model row classification")
so it survives index regeneration.

| Label | Meaning | Counts as a headline comparison? |
| --- | --- | --- |
| **strict-track clean** | Completed all tasks under the strict-512 protocol with an acceptable parse-failure rate. | Yes (within strict-512 track) |
| **best-valid clean** | Completed all tasks under the provider's documented minimum-valid settings. | Yes (within best-valid track) |
| **protocol-limited** | Completed provider calls but a large share produced truncated/empty output under the row's budget/settings. Retained as a documented protocol finding. | No (protocol finding) |
| **provider-failed** | One or more tasks failed with provider/runtime errors (e.g. 503/504) and the row was not cleanly completed. | No (diagnostic) |
| **rescue probe** | A small (≤30-task) run that changes settings to test whether a failure is protocol-driven. | No (diagnostic) |
| **smoke run** | A tiny run (≤30 tasks, often single-environment) that exercises plumbing. | No |
| **diagnostic forced-tool run** | A run where a tool call is forced to study tool-use, not to rank models. | No (separate experiment) |
| **reference / mock / non-model diagnostic** | Deterministic reference solver, random-valid mock, or deterministic tool-reference baseline. | No (control) |

### Definitions in detail

- A **completed clean row** has `models_run ≥ 1`, all configured tasks attempted,
  zero provider/runtime errors, and a parse-failure rate consistent with its track
  (≈0 for strict-512 clean; small and documented for best-valid clean).
- A **protocol-limited row** completed its provider calls but its score is depressed
  by output-budget/decoding behaviour (truncation, hidden-thinking-token exhaustion,
  empty content), not by reasoning. It is kept for completeness and never reported
  as capability.
- A **provider-failed row** has unrecovered provider errors; its clean replacement
  (e.g. a cache-backed retry) is the row that may be reported, with the failure
  noted as a caveat.
- A **rescue probe** is a deliberately small run that isolates whether a failure is
  protocol-driven. It is diagnostic and never replaces a full ladder score.
- A **diagnostic tool run** forces a tool call; forced-tool use is not natural tool
  use and is reported separately from direct rankings.
- **Reference / mock / non-model** rows validate generation, grading, and tool
  plumbing. They are controls and must never be reported as model performance.

## Current track assignments (the rows that matter)

| Row | Track / label |
| --- | --- |
| OpenAI `gpt-4.1-mini`, `gpt-5.4-mini` | strict-track clean |
| OpenAI `gpt-5.4` | strict-track clean (strongest comparable OpenAI direct row) |
| OpenAI `gpt-5.5` | protocol-limited (default temp, 512 budget; 89/120 empty-at-length) |
| Claude Haiku 4.5 | strict-track clean |
| Claude Sonnet 4.6 (512) | protocol-limited (70/120 truncated before JSON) |
| Claude Sonnet 4.6 (1536) | best-valid clean |
| Gemini Flash-Lite | strict-track clean |
| Gemini Flash (default thinking, 512) | protocol-limited (118/120 stopped at MAX_TOKENS) |
| Gemini Flash (`thinking_budget=0`) | best-valid clean |
| Gemini Pro Preview (`thinking_level=low`, retry) | best-valid clean (provider-load caveat) |

## Reproducing the classification and statistics

```bash
mimirbench build-report-index                 # regenerates the classification table
mimirbench statistical-validity               # bootstrap CIs + paired deltas (no model runs)
```

Both commands read saved artefacts only; neither makes any API call.

## Caveats (apply to every row)

- Synthetic, deterministic evaluation tasks; not live-market or trading results.
- 20 tasks/environment, single seed/schedule; pilot CIs only.
- Cross-track comparisons are not identical-decoding.
- No broad provider- or model-superiority claim; no trading-usefulness claim.
- No hidden chain-of-thought is collected; all grading is deterministic.
