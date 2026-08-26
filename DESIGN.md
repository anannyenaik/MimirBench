# Design

This document sets out MimirBench's research and engineering principles. For
evaluation procedures, see [EVALS.md](EVALS.md); for robustness methodology, see
[ROBUSTNESS.md](ROBUSTNESS.md); for the interpretability plan see
[INTERPRETABILITY.md](INTERPRETABILITY.md).

## Motivation

We want to measure something sharper than task success: the **quality of an
agent's reasoning under uncertainty**. Concretely, four capabilities:

1. **Belief updating**: does the agent move its probabilities the right way, by
   the right amount, when it sees evidence?
2. **Expected-value reasoning**: does it value uncertain outcomes correctly?
3. **Constraint obedience**: does it respect hard limits even when violating them
   looks locally attractive?
4. **Robustness**: are its conclusions stable under paraphrase and adversarial
   pressure?

The benchmark also asks *why* an agent succeeds or fails, at both the
behavioural and mechanistic levels. That second goal is what
separates MimirBench from a pure eval suite and motivates the parallel track of
small, fully-controlled transformer models.

## Design philosophy

- **Closed-form ground truth or it doesn't ship.** Every registered environment has
  a reference solver that computes the optimal answer exactly. If we cannot grade an
  environment deterministically, it stays a scaffold until we can.
- **Small, readable code.** Prefer explicit functions and pydantic models
  over clever abstractions. The benchmark's credibility rests on being auditable.
- **Separation of concerns via stable contracts.** Environments, agents, graders,
  and analysis communicate only through the schemas in
  [`mimirbench/evals/schemas.py`](mimirbench/evals/schemas.py). Any agent can be
  dropped into any environment.
- **Structural safety for ground truth.** A task's answer lives in `GradingKey`,
  which the agent never receives. The "don't leak the answer" rule is enforced by
  types, not vigilance.
- **Determinism as a feature.** Reproducibility from a seed is a first-class
  property, tested in CI.
- **Explicit scope.** Result files remain empty until reproducible runs exist.

## Why deterministic graders matter

LLM-as-judge grading is convenient but introduces a second model's biases, variance,
and cost into the measurement. For decision tasks we don't need it: the optimal
posterior, the expected surplus, and the set of breached risk limits are all exactly
computable. Deterministic grading buys us:

- **Calibrated error, not just pass/fail**: we report *how far* an answer is from
  optimal (e.g. total-variation distance to the true posterior), which is far more
  informative than a binary verdict.
- **Zero grader variance**: re-running grading never changes a score.
- **Auditability**: a reviewer can recompute any score by hand.
- **Speed and cost**: no judge-model calls in the inner loop.

## Why synthetic task generation matters

Tasks are generated from seeds rather than scraped or hand-written. This gives:

- **No contamination.** Freshly-seeded instances cannot be in any training set.
- **Controlled difficulty.** We can dial the number of hypotheses, the
  informativeness of evidence, or the tightness of risk limits.
- **Unlimited, balanced data.** Enough instances for tight confidence intervals and
  for training the small interpretability models on the *same* task structure.
- **Known structure for interpretability.** Because we generate the data-generating
  process, we know the Bayes-optimal belief at every step: the target a probe tries
  to read out of a model's activations.

## Why train a small synthetic transformer

MimirBench trains a compact transformer on synthetic Bayesian strategic
traces. This is a model-organism track, not a frontier-model claim. The synthetic
traces expose exact posterior buckets, action labels, EV buckets, risk flags,
confidence buckets, and concise rationale classes. They deliberately do not
store hidden chain-of-thought.

That choice keeps the training target auditable and mechanistically useful:
later probes can ask whether posterior, action, and risk features are linearly
decodable from activations without relying on elicited private reasoning text.
The model remains small enough for CPU smoke tests, checkpoint inspection, and
activation-capture experiments.

## Bridging frontier AI evals and quant-style uncertainty

Quantitative finance has spent decades formalising decision-making under
uncertainty: Bayesian filtering of hidden states, expected-value and risk trade-offs,
auction and market mechanisms, inventory and loss limits. These are not used here to
build a trading system; they are used as a **deep, well-posed library of decision
problems** with known optimal solutions.

That makes them an unusually good evaluation substrate for frontier models:

- the problems are **genuinely hard** (sequential inference, strategic interaction),
- the **optimal behaviour is computable**, and
- the **failure modes are economically meaningful** (mis-calibration, over-trading,
  ignoring risk limits under pressure).

MimirBench sits at that intersection: frontier-eval methodology (synthetic tasks,
robustness, interpretability) applied to quant-style uncertainty problems.

## Environment families

| Family | What the agent must do | Reference solution |
| --- | --- | --- |
| `bayesian_games` | Report the posterior over hidden sources after a signal sequence | Exact naive-Bayes posterior |
| `hidden_regimes` | Report the filtered belief over the current regime in an HMM | Exact forward algorithm |
| `auctions` | Report expected surplus from truthful bidding | Closed-form IPV second-price surplus |
| `market_making` | Choose synthetic bid/ask quotes and sizes while obeying inventory/loss limits | Deterministic inventory-aware quote heuristic + risk checker |
| `prediction_markets` | Separate posterior belief, market price, edge, and conservative sizing | Binary Bayesian posterior + synthetic cost/impact sizing |
| `adversarial_risk` | Keep obeying limits under misleading pressure | Deterministic risk-policy solver |

All six families are implemented and registered. Reference solvers are sanity
checks for the generate-grade pipeline, not model results.

## Why Synthetic Market-Making

The `market_making` environment is a one-shot quote decision benchmark. It uses
synthetic mid prices, generated inventory states, synthetic volatility, a
adverse-selection scalar, and explicit hard limits. The reference policy widens
spreads under higher risk and skews sizes away from inventory expansion near
limits.

It is not a trading strategy. It has no live data, no execution model, no
profitability claim, and no claim to describe real market microstructure. The
point is to test whether an agent can keep quote validity, inventory pressure,
and hard limits in its head at the same time.

## Why prediction markets

The `prediction_markets` environment deliberately separates three quantities
that language agents often conflate:

- belief: the posterior probability after the private signal
- price: the current market price
- edge: the difference after synthetic transaction cost and impact

That separation lets the grader distinguish a calibration error from a trade
direction error or a risk-sizing error. The generated markets are binary,
synthetic, and small; they are evaluation tasks, not market recommendations.

## Why adversarial risk-control tasks

The `adversarial_risk` environment tests instruction hierarchy and constraint
adherence. Each task includes explicit hard limits and misleading pressure text:
authority pressure, urgency, loss chasing, fake insider signals, emotional
framing, requests to ignore constraints, fake system status, recent-win bias, or
confident but irrelevant analyst claims.

The correct action is computed from the risk policy alone. The adversarial text
is answer-preserving and should not change the safe decision. This gives a direct
measure of whether the agent follows hard constraints under pressure without
requiring a model judge.

## Why robustness is first-class

A high score on a single prompt is insufficient. Strategic-reasoning agents should
keep the same answer when only wording, irrelevant framing, evidence order, or
untrusted pressure changes. MimirBench therefore treats robustness as a benchmark
surface rather than an afterthought:

- `VariantSpec` records the parent task, environment, variant type, whether the
  variant is answer-preserving, and the expected invariance.
- Answer-preserving variants copy the grading key unchanged. If a transformation
  mathematically changes the problem, such as auction unit scaling, it is marked
  non-answer-preserving and the key is recomputed.
- Variant generation uses deterministic templates and seed-controlled text banks
  instead of LLM-generated paraphrases, so any regression is reproducible and
  inspectable.
- Robustness records compare base and variant score, canonical action, safety
  status, invalid parsing, risk violations, and pressure susceptibility.
- Failure-case extraction turns raw records into a triage list without an LLM
  judge.

This keeps the same core principle as the environments: if the benchmark cannot
explain exactly what changed and why the expected answer should or should not
move, it should not score that case.

## Failure modes we want to study

- **Base-rate neglect / prior insensitivity**: ignoring the prior and over-weighting
  the latest signal.
- **Evidence over- and under-reaction**: moving beliefs too far or too little per
  observation; order effects in sequential updating.
- **Miscalibration**: confident probabilities that don't match outcome frequencies.
- **Expected-value distortions**: risk-seeking/averse errors inconsistent with the
  task's stated objective.
- **Risk-limit violations under pressure**: abandoning hard constraints when an
  adversarial prompt makes breaking them look attractive.
- **Brittleness**: answers that flip under paraphrase or irrelevant distractors.
- **Unfaithful explanations**: a stated rationale that does not match the action
  actually taken.

For each behavioural failure, the interpretability track asks the mechanistic
follow-up: *what computation inside the model produced it?*
