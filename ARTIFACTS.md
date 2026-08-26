# Artefacts

This document defines what is committed, what is regenerated, and how to verify
it. The repository policy is:
**curated reports and metrics are committed; large binary weights and raw caches
are regenerated from configs + seeds**, because they are deterministic.

## Committed Artefacts

- **Curated reports** under `reports/`: `INDEX.md`, leaderboard reports and
  comparison notes, robustness reports, interpretability reports, and the
  generated statistical-validity table
  (`reports/runs/leaderboard/statistical_validity_existing_artifacts.md`).
- **Per-task results**: `results.jsonl` and `summary.json` for the saved
  hosted-model leaderboard rows (the inputs to
  [STATISTICAL_VALIDITY.md](STATISTICAL_VALIDITY.md)).
- **Response caches**: `responses_cache.jsonl` next to each committed run. These
  hold the verbatim provider responses, so a saved hosted-model row can be
  re-scored and re-analysed offline without paying for the calls again.
- **Training/eval summaries and figures** for the tiny and medium model organisms
  (`reports/training/...`, `reports/runs/small_transformer_bayes_*_eval/`).
- **Interpretability artefacts**: probe/patching/attention JSON, the
  reports, the extended report
  (`reports/interpretability/interp_bayes_medium_extended/`), and the **multi-seed
  replication** (seeds 123–128): per-seed summaries/figures under
  `reports/interpretability/interp_bayes_all_medium_seed_*/` and `..._extended_seed_*/`,
  the aggregate
  [`interp_bayes_multiseed_summary.md`](reports/interpretability/interp_bayes_multiseed_summary.md)
  (+ `.json`), the per-head/individual-token aggregate
  [`interp_bayes_head_token_summary.md`](reports/interpretability/interp_bayes_head_token_summary.md)
  (+ `.json`), and per-seed checkpoint SHA256s
  (`reports/interpretability/interp_bayes_multiseed/checkpoints_sha256.txt`).
- **Model cards** under `reports/model_cards/` (auto-generated for real runs) and
  the curated [MODEL_CARD_medium.md](MODEL_CARD_medium.md).

## Regenerated Artefacts

Per [.gitignore](.gitignore):

- model weights: `*.pt`, `*.ckpt`, `*.safetensors` (so all `checkpoints/` are
  **not** committed);
- raw run scratch (`*.log`) and scratch output directories (`/runs/`, `/outputs/`,
  `/artifacts/`, `results/`);
- `.env` and `.env.*`, so a local key file can never be committed by accident;
- virtualenvs, tool caches, build artefacts;
- **multi-seed replication bulk** (seeds 124+): per-seed synthetic traces,
  activation dumps, per-row patching logs, and held-out eval rows are regenerable
  and gitignored; the per-seed summaries, patching summaries, reports, and figures
  are kept.

This means the medium checkpoint exists locally but is **not in git**. The training
is deterministic (fixed seed, dropout 0, CPU), so anyone can regenerate a
bit-identical checkpoint from the committed config.

## Convenience release assets

The [v0.2.0 GitHub release](https://github.com/anannyenaik/MimirBench/releases/tag/v0.2.0)
includes the medium `best.pt` checkpoint and `vocab.json` as downloadable
convenience assets. The release asset does not change repository policy:
checkpoints remain gitignored and the checkpoint is reproducible from the
committed config.

Download and verify them:

```powershell
gh release download v0.2.0 --pattern best.pt --pattern vocab.json --dir release-assets\v0.2.0
Get-FileHash release-assets\v0.2.0\best.pt -Algorithm SHA256
Get-FileHash release-assets\v0.2.0\vocab.json -Algorithm SHA256
```

```bash
gh release download v0.2.0 --pattern best.pt --pattern vocab.json --dir release-assets/v0.2.0
sha256sum release-assets/v0.2.0/best.pt release-assets/v0.2.0/vocab.json
```

Expected SHA256 values:

- `best.pt`: `3f273cfe70d94e42c0f1b0440b9a907203c6260e6e03e02eff6ad5f4eaa1c546`
- `vocab.json`: `d7a994c5a616d4326250483528ff0cd06f933b05c41cf7d735f428d64ba2ecfa`

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

> PyTorch may serialise identical weights with minor container differences
> across versions/platforms. If the byte-level hash differs, confirm equivalence
> via the held-out metrics in [MODEL_CARD_medium.md](MODEL_CARD_medium.md) (action
> accuracy 1.000, posterior-bucket accuracy 0.990, mean posterior error ≈ 0.0162)
> rather than the raw hash alone.

## Running medium interpretability

```bash
mimirbench run-interpretability            configs/interp_bayes_all_medium.yaml
mimirbench run-extended-interpretability   configs/interp_bayes_medium_extended.yaml
# Multi-seed replication across seeds 123-128 (trains missing checkpoints, reruns
# the whole-site + extended pipeline and a held-out eval per seed, writes the
# aggregate interp_bayes_multiseed_summary.json):
mimirbench run-multiseed-interpretability  configs/interp_bayes_medium_multiseed.yaml
mimirbench run-head-token-interpretability configs/interp_bayes_medium_multiseed.yaml
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
