# Failure cases

A curated catalogue of specific, **reproducible** reasoning failures surfaced by
MimirBench. Each entry is reconstructible from its seed, so anyone can inspect the
exact task and the agent's response.

> _Empty until model-agent runs exist. The structure below shows how entries will be
> recorded._

## Entry template

```markdown
### FC-001 — <short title>
- **Failure mode:** <base-rate neglect | over/under-reaction | miscalibration |
  risk-limit violation under pressure | paraphrase brittleness | unfaithful explanation>
- **Environment / seed:** <env> / <seed>   (reproduce: `generate_task(seed)`)
- **Model / agent:** <model@version> / <agent>
- **What optimal looks like:** <closed-form reference answer>
- **What the agent did:** <parsed answer + reasoning summary>
- **Score / metrics:** <score, key error metric, violations>
- **Interpretability follow-up (if any):** <probe / patching observation>
- **Notes:** <hypothesis about the cause>
```

## Failure modes we are cataloguing

1. **Base-rate neglect** — ignoring the prior; over-weighting the latest signal.
2. **Evidence over-/under-reaction** — belief moves too far or too little; order effects.
3. **Miscalibration** — stated probabilities that don't match outcome frequencies.
4. **Expected-value distortion** — risk attitudes inconsistent with the objective.
5. **Risk-limit violation under pressure** — abandoning hard limits when nudged.
6. **Paraphrase brittleness** — answers flipping under meaning-preserving rewrites.
7. **Unfaithful explanation** — rationale that contradicts the action taken.
