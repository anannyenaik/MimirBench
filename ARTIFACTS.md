# Artifacts

What is committed, what is regenerated, and how to verify it. The guiding rule:
**curated reports and metrics are committed; large binary weights and raw caches
are regenerated from configs + seeds**, because they are deterministic.

## What is committed

- **Curated reports** under `reports/` — `INDEX.md`, leaderboard reports and
  comparison notes, robustness reports, interpretability reports, and the
  generated statistical-validity table
  (`reports/runs/leaderboard/statistical_validity_existing_artifacts.md`).
- **Per-task results** — `results.jsonl` and `summary.json` for the saved
  real-model leaderboard rows (the inputs to
  [STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md)).
- **Training/eval summaries and figures** for the tiny and medium model organisms
  (`reports/training/...`, `reports/runs/small_transformer_bayes_*_eval/`).
- **Interpretability artefacts** — probe/patching/attention JSON, the Stage 8
  reports, and the extended report
  (`reports/interpretability/interp_bayes_medium_extended/`).
- **Model cards** under `reports/model_cards/` (auto-generated for real runs) and
  the curated [MODEL_CARD_medium.md](MODEL_CARD_medium.md).

## What is gitignored (regenerated, not committed)

Per [.gitignore](.gitignore):

- model weights — `*.pt`, `*.ckpt`, `*.safetensors` (so all `checkpoints/` are
  **not** committed);
- response caches and raw run scratch (`*.log`, large `responses_cache.jsonl` are
  byproducts);
- `.env` and `.env.*` (secrets) — only `.env.example` is tracked;
- virtualenvs, tool caches, build artefacts.

This means the medium checkpoint exists locally but is **not in git**. The training
is deterministic (fixed seed, dropout 0, CPU), so anyone can regenerate a
bit-identical checkpoint from the committed config.

## Regenerating the medium checkpoint

```bash
pip install -e ".[ml]"
mimirbench train-small-transformer configs/train_small_transformer_bayes_medium.yaml
mimirbench eval-small-transformer  configs/eval_small_transformer_bayes_medium.yaml
```

This writes `reports/training/small_transformer_bayes_medium/checkpoints/best.pt`
(and `final.pt`) plus `vocab.json`, metrics, and figures.

## Verifying checksums

Recorded SHA256 checksums for the locally generated medium checkpoint (see
[MODEL_CARD_medium.md](MODEL_CARD_medium.md) for the canonical copy):

| File | SHA256 | Bytes |
| --- | --- | ---: |
| `checkpoints/best.pt` | `3f273cfe70d94e42c0f1b0440b9a907203c6260e6e03e02eff6ad5f4eaa1c546` | 1,301,217 |
| `checkpoints/final.pt` | `137ec5d15241557ebc25d7f33a56ec45736c043b9780afe28b9eb43f98d96d89` | 1,301,263 |
| `vocab.json` | `d7a994c5a616d4326250483528ff0cd06f933b05c41cf7d735f428d64ba2ecfa` | 2,025 |

To verify a regenerated checkpoint:

```bash
# PowerShell
Get-FileHash reports\training\small_transformer_bayes_medium\checkpoints\best.pt -Algorithm SHA256
# bash
sha256sum reports/training/small_transformer_bayes_medium/checkpoints/best.pt
```

> Note: PyTorch may serialise identical weights with minor container differences
> across versions/platforms. If the byte-level hash differs, confirm equivalence
> via the held-out metrics in [MODEL_CARD_medium.md](MODEL_CARD_medium.md) (action
> accuracy 1.000, posterior-bucket accuracy 0.990, mean posterior error ≈ 0.0162)
> rather than the raw hash alone.

## Running medium interpretability

```bash
mimirbench run-interpretability          configs/interp_bayes_all_medium.yaml
mimirbench run-extended-interpretability configs/interp_bayes_medium_extended.yaml
```

The extended command runs position-resolved patching and negative controls; it is
local-only and makes no API calls. If the checkpoint or torch is missing, both
commands write a `status="pending"` report rather than failing.

## Why checkpoints are not committed

- They are deterministic byproducts of committed configs + seeds, so committing
  them duplicates information and bloats the repository.
- Binary weights do not diff or review well.
- The curated metrics, figures, and model card capture everything a reader needs;
  the weights can be regenerated on demand.

## Attaching a checkpoint as a release asset (optional, later)

If a fixed binary is wanted for convenience, attach it to a GitHub release rather
than committing it to the tree:

```bash
# After creating the v0.2.0 release (see RELEASE_NOTES_v0.2.0.md):
gh release upload v0.2.0 \
  reports/training/small_transformer_bayes_medium/checkpoints/best.pt \
  reports/training/small_transformer_bayes_medium/vocab.json
```

No release URLs are invented here; create the release first, then upload. Record the
asset's SHA256 alongside the ones above when you do.
