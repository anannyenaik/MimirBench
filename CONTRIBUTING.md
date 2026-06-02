# Contributing

Thanks for your interest in MimirBench. This is a research-engineering codebase; the
bar is **correctness, clarity, and reproducibility** over cleverness.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## The checks (run before every PR)

```bash
ruff check .         # lint + import sorting
mypy mimirbench      # static types
pytest               # tests
```

CI runs the same three on Python 3.11 and 3.12. PRs must be green.

## Code standards

- **Type hints everywhere.** `mypy` runs with `disallow_untyped_defs`; annotate all
  functions, including tests where practical.
- **Structured data is a model.** Use pydantic models or frozen dataclasses for
  anything crossing a module boundary.
- **Small, readable functions.** Avoid premature abstraction; match the style of the
  surrounding code.
- **Determinism is explicit.** Anything random takes a `seed` and uses
  `numpy.random.default_rng(seed)` (or `torch.manual_seed`). No hidden global RNG.
- **Optional dependencies are lazy.** `torch`, `transformers`, `transformer-lens`,
  `openai`, and `wandb` must be imported *inside* functions, never at module top, so
  the core harness and tests never require them.
- **Line length** is 100; `ruff format` (via pre-commit) handles formatting.

## Project-specific rules

- **Never put ground truth in a `Task`.** Answers belong in `GradingKey`, which agents
  never receive.
- **Graders are pure and deterministic.** No I/O, no randomness, no model calls.
- **No hidden chain-of-thought.** Agents return concise reasoning *summaries*; do not
  add fields or prompts that elicit private step-by-step reasoning, and do not reward
  it in graders.
- **No fabricated results.** Do not add numbers to `RESULTS.md` or `reports/` unless
  they come from a real, reproducible run. The reference baseline is not a result.
- **Honest status.** Mark unfinished environments as scaffolds; prefer a clear
  `NotImplementedError` pointing to the roadmap over a plausible-but-wrong stub.

## Adding an environment

See the checklist at the end of [EVALS.md](EVALS.md). In short: implement
`schemas/generator/solver/grader`, add a `build_spec()`, register it, and add a
determinism test plus a "reference agent is near-perfect" test.

## Commit & PR conventions

- Keep PRs focused; one logical change per PR.
- Describe *what* and *why*; link issues.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Add or update tests and docs alongside code.

## Reporting issues

Open a GitHub issue with a minimal reproduction: the config or code, the seed, and
the observed vs expected behaviour.
