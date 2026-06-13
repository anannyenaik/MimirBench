# Robustness Evaluation

Robustness is a first-class MimirBench evaluation surface. A robustness run asks:
does an agent keep the same decision when the problem's answer is preserved, and
does it resist misleading or irrelevant context when hard constraints still
apply?

The implementation is deterministic, seed-controlled, and grader-only. It does
not use LLM judges, live data, hidden chain-of-thought, or generated frontier
model results.

## Why Robustness Matters

Strategic reasoning failures often appear only after a small prompt change:

- a posterior flips under a paraphrase
- a risk limit is ignored after urgency or authority pressure
- irrelevant context distracts from the stated evidence
- recent outcomes are over-weighted even when the task structure is unchanged
- a valid base response becomes invalid JSON on a variant

Base-task accuracy and robustness are therefore reported separately. Reference
solver robustness is a wiring sanity check. Mock-agent robustness is diagnostic
only. Real-model robustness should be reported only when an API or local model
run is actually executed and saved as an artefact.

## Variant Taxonomy

The variant catalogue is defined in `mimirbench/evals/variants.py`.

| Variant type | Purpose | Answer-preserving by default |
| --- | --- | --- |
| `paraphrase` | Reword the task without changing data or objective | Yes |
| `irrelevant_context` | Add unrelated public context | Yes |
| `misleading_authority` | Add a confident but untrusted recommendation | Yes |
| `emotional_pressure` | Add social or emotional pressure | Yes |
| `urgency_pressure` | Add time-pressure framing | Yes |
| `recent_outcome_bias` | Add misleading recency framing | Yes |
| `order_permutation` | Reorder exchangeable evidence | Yes |
| `unit_scale_change` | Rescale auction units and recompute the key | No |
| `distractor_signal` | Add an untrusted signal-like distraction | Yes |
| `risk_pressure` | Pressure the agent toward unsafe sizing or policy breaks | Yes |
| `prompt_injection_style` | Add text that imitates an instruction override | Yes |

Every generated variant has a `VariantSpec` with:

- `variant_id`
- `variant_type`
- `parent_task_id`
- `environment`
- `answer_preserving`
- `transformation_description`
- `expected_invariance`
- `metadata`

## Answer-Preserving vs Non-Preserving

For answer-preserving variants, the grading key is copied unchanged. The final
answer and canonical action should usually remain the same. A changed final
action counts against robustness unless an environment-specific canonicalization
proves it equivalent.

For non-answer-preserving variants, the variant must document why the answer can
change. The current example is `unit_scale_change` for auctions: all monetary
units are rescaled, the expected surplus changes numerically, and the key is
recomputed from the reference solver.

## Environment Coverage

Deterministic generators cover all six registered environments:

- `bayesian_games`: evidence reordering, framing changes, irrelevant context,
  wrong analyst commentary, emotional pressure, label-preserving paraphrases
- `auctions`: bidder-context paraphrases, competitor rumours, winner's-curse
  pressure, authority recommendations, equivalent unit scaling
- `hidden_regimes`: irrelevant commentary, non-temporal metadata framing,
  recent-outcome bias, fake expert regime calls
- `market_making`: urgency pressure, authority pressure, irrelevant macro text,
  pressure to exceed inventory limits, recent-win bias
- `prediction_markets`: emotional pressure, fake insider signals, irrelevant
  commentary, event-wording changes, pressure to trade despite no edge
- `adversarial_risk`: authority pressure, urgency, loss chasing, fake insider
  signals, emotional pressure, ignore-constraints text, fake system status,
  recent-win bias, and confident irrelevant analyst claims

## Metrics

Robustness runs compare each variant against its base task and aggregate:

- `paraphrase_consistency_rate`
- `mean_score_drop`
- `worst_score_drop`
- `action_flip_rate`
- `invalid_response_increase`
- `unsafe_action_increase`
- `risk_violation_increase`
- `pressure_susceptibility_rate`
- `order_invariance_rate`
- `distractor_robustness_rate`
- `environment_breakdown`
- `variant_type_breakdown`

`mean_score_drop` is base score minus variant score over answer-preserving
variants. Positive values mean the variant scored worse. Non-answer-preserving
variants are excluded from action-flip and consistency rates but still contribute
to safety regression counts.

## Paraphrase Consistency

Paraphrase consistency is measured over `paraphrase` variants only. The runner
reduces each parsed answer to a canonical action using
`mimirbench/evals/scoring.py`, then checks whether the base and variant actions
match. Continuous values are rounded or reduced to the relevant discrete choice
where appropriate.

## Adversarial Pressure

Pressure variants include misleading authority, emotional pressure, urgency,
recent-outcome bias, risk pressure, and prompt-injection-style framing.

Pressure susceptibility is either provided by the environment grader or inferred
from robustness signals: score drop, answer-preserving action flip, and new
unsafe action. This keeps the metric deterministic and avoids asking a model
judge whether the agent was "persuaded."

## Failure-Case Extraction

`mimirbench/analysis/failure_cases.py` ranks records that are likely to be useful
for debugging:

- largest score drops
- base correct, variant wrong
- base safe, variant unsafe
- action flips under paraphrase
- pressure-induced risk violations
- overconfidence despite wrong answers
- ignored tool results when tool metadata exists
- invalid JSON or parse failures
- high-regret failures

Each case includes environment, task id, variant id, variant type, task text,
base response, variant response, base and variant grader summaries, a concise
diagnostic label, and why the case is interesting. Writers emit both
`failure_cases.jsonl` and `failure_cases.md`.

## CLI

```bash
python -m mimirbench.cli list-variant-types
python -m mimirbench.cli run-robustness configs/robustness_reference_bayes.yaml
python -m mimirbench.cli run-robustness configs/robustness_mock_all_envs.yaml
python -m mimirbench.cli summarise-robustness reports/runs/robustness_mock_all_envs
```

Robustness configs live under `configs/robustness_*.yaml`.

## Scope and Limitations

- Deterministic templates are intentionally limited. They are reproducible and
  auditable, but they do not cover the full diversity of natural paraphrases.
- Reference robustness is robust by construction because reference solvers read
  structured metadata. Treat it as a sanity check, not a model result.
- Mock robustness is diagnostic only. The random-valid mock is keyed on task id,
  so action flips under variants are expected.
- The deterministic robustness infrastructure is implemented and exercised end to
  end. Historical reference and mock robustness remain sanity-check/diagnostic
  only (see the two bullets above), not model results.
- Real-model robustness probes have now been run and saved for OpenAI `gpt-5.4`,
  Claude Sonnet 4.6, Gemini Flash, and Gemini Pro. These are pilot
  synthetic robustness probes. Robustness sample
  sizes differ by provider/config where documented, so rows are not always
  directly comparable. Read them through [RESULTS.md](RESULTS.md) and
  [reports/INDEX.md](reports/INDEX.md), alongside the saved comparison and run
  reports:
  - [OpenAI `gpt-5.4` robustness](reports/runs/leaderboard/leaderboard_openai_gpt54_robustness_tiny/robustness_report.md)
  - [Claude Sonnet 4.6 robustness](reports/runs/leaderboard/leaderboard_claude_sonnet_robustness_tiny/robustness_report.md)
  - [Gemini strongest-row robustness comparison](reports/runs/leaderboard/gemini_strongest_robustness_comparison.md)
    (Flash and Pro), with per-run reports under
    [`leaderboard_gemini_strongest_robustness_tiny/`](reports/runs/leaderboard/leaderboard_gemini_strongest_robustness_tiny/robustness_report.md)
    and [`leaderboard_gemini_pro_robustness_small/`](reports/runs/leaderboard/leaderboard_gemini_pro_robustness_small/robustness_report.md).

  Protocol-limited or provider-failed rows must not be treated as capability
  rows, and nothing here is a trading-usefulness or broad provider-superiority
  claim. See [MODELS.md](MODELS.md) for provider setup and limitations.
- The benchmark does not use LLM judges, so it cannot score free-form rationale
  quality beyond deterministic parseable outputs and grader metrics.
- Tasks are synthetic and evaluation-only. They do not use live market data and
  are not trading systems or recommendations.

## Deterministic Variant Design

LLM-generated paraphrases can be useful later, but they create extra variance and
can accidentally change the task. MimirBench starts with deterministic templates so
that every robustness failure is traceable to a known, reviewable transformation.
Once hosted/local-model baselines exist, LLM-generated variants can be added as an
optional audited layer with explicit preservation checks.
