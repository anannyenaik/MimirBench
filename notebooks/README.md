# Notebooks

Exploratory and explanatory notebooks. Notebooks are for **exploration and
figures**, not for the source of truth; anything reusable should be promoted into
the `mimirbench` package and covered by tests.

## Conventions

- **Clear outputs before committing** (notebooks are linting-excluded but should stay
  small and diff-friendly). Prefer committing the generating code over heavy outputs.
- **Set seeds** at the top of every notebook so figures are reproducible.
- **Import from the package** (`from mimirbench... import ...`) rather than copying
  code into cells.
- **No secrets** (API keys) in cells; read them from the environment.

## Candidate Analyses

- Bayesian posterior updates and order invariance.
- Hidden-regime filtering against the generated regime path.
- Reliability diagrams from evaluation outputs.
- Belief probes for trained synthetic model organisms.
