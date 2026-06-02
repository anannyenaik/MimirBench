# Reports

Curated, human-readable outputs of MimirBench runs. Unlike the git-ignored raw
artifacts under `runs/`/`artifacts/`, everything here is **intentionally committed**
and **reproducible from a config + seed + model version**.

## Contents

- [`model_cards/`](model_cards/) — one card per evaluated model/agent: setup,
  headline metrics (with confidence intervals), known limitations.
- [`failure_cases.md`](failure_cases.md) — curated, seeded examples of specific
  reasoning failures.

## Rules

- **No fabricated numbers.** A report is added only when it is backed by a real run.
- **Always reproducible.** Every report names the environment, seed(s), `n_tasks`,
  agent, and model version so it can be regenerated.
- **Honest framing.** Report confidence intervals and limitations, not just point
  estimates.

_There are no reports yet — the harness is at the foundation stage._
