# Model cards

One card per evaluated model or agent. A model card records *exactly how* a model was
evaluated and *what was found*, so a reader can trust and reproduce the numbers.

Add a card only when it is backed by a real, reproducible run.

## Template

```markdown
# <model / agent name>

- **Model version:** <provider/model@version or checkpoint hash>
- **Agent:** <direct | tool | reflective | ...>
- **Harness version:** mimirbench <x.y.z>
- **Date:** <YYYY-MM-DD>
- **Configs / seeds:** <configs used, base seeds, n_tasks>

## Headline metrics (mean ± 95% CI)

| Environment | Score | Key metric | Violation rate |
| --- | --- | --- | --- |
| bayesian_games | … | posterior TV error … | … |
| auctions | … | EV rel. error … | … |
| hidden_regimes | … | posterior TV error … | … |

## Robustness
- Paraphrase consistency: …
- Adversarial score drop: …

## Known limitations & caveats
- …

## Reproduction
```bash
mimirbench run-eval <config> --seed <seed> --n-tasks <n>
```
```

_No model cards yet._
