# Model cards

One card per evaluated model or agent. Each card records the evaluated artefact,
configuration, metrics, and limitations required to reproduce and interpret the
result.

Curated and generated cards in this directory cover the deterministic controls
and the tiny and medium synthetic transformers. Hosted-model cards are stored
alongside their leaderboard runs under `reports/runs/leaderboard/`.

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

## Scope and limitations
- …

## Reproduction
```bash
mimirbench run-eval <config> --seed <seed> --n-tasks <n>
```
```
