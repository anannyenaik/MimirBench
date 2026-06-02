# Notebooks

Exploratory and explanatory notebooks. Notebooks are for **exploration and
figures**, not for the source of truth — anything reusable should be promoted into
the `mimirbench` package and covered by tests.

## Conventions

- **Clear outputs before committing** (notebooks are linting-excluded but should stay
  small and diff-friendly). Prefer committing the generating code over heavy outputs.
- **Set seeds** at the top of every notebook so figures are reproducible.
- **Import from the package** (`from mimirbench... import ...`) rather than copying
  code into cells.
- **No secrets** (API keys) in cells; read them from the environment.

## Planned notebooks

- `01_bayesian_intuition.ipynb` — visualise posterior updates and order-invariance.
- `02_hidden_regimes_filtering.ipynb` — forward-filter beliefs vs the true regime path.
- `03_calibration_walkthrough.ipynb` — reliability diagrams from eval outputs.
- `04_belief_probe.ipynb` — probe a trained regime-LM for the Bayes-filtered belief.
