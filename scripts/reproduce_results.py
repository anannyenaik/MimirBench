"""Recompute and verify the committed benchmark summaries without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ROOT / "experiments" / "selected_results"
BENCHMARK = SELECTED / "benchmark"
SUMMARY_PATH = BENCHMARK / "summary.json"
MANIFEST_PATH = SELECTED / "manifest.json"
CHECKSUMS_PATH = SELECTED / "SHA256SUMS"

BOOTSTRAP_SEED = 20_260_606
N_RESAMPLES = 2_000
CONFIDENCE = 0.95

MODEL_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "openai_gpt_4_1_mini",
        "display": "OpenAI gpt-4.1-mini",
        "provider": "OpenAI",
        "track": "strict-512",
        "protocol": {"temperature": 0, "max_tokens": 512},
    },
    {
        "key": "openai_gpt_5_4_mini",
        "display": "OpenAI gpt-5.4-mini",
        "provider": "OpenAI",
        "track": "strict-512",
        "protocol": {"temperature": 0, "max_tokens": 512},
    },
    {
        "key": "openai_gpt_5_4",
        "display": "OpenAI gpt-5.4",
        "provider": "OpenAI",
        "track": "strict-512",
        "protocol": {"temperature": 0, "max_tokens": 512},
    },
    {
        "key": "claude_haiku_4_5",
        "display": "Claude Haiku 4.5",
        "provider": "Anthropic",
        "track": "strict-512",
        "protocol": {"temperature": 0, "max_tokens": 512},
    },
    {
        "key": "claude_sonnet_4_6",
        "display": "Claude Sonnet 4.6",
        "provider": "Anthropic",
        "track": "best-valid",
        "protocol": {"temperature": 0, "max_tokens": 1536},
    },
    {
        "key": "gemini_flash_lite",
        "display": "Gemini Flash-Lite",
        "provider": "Google",
        "track": "strict-512",
        "protocol": {"temperature": "provider default", "max_tokens": 512},
    },
    {
        "key": "gemini_flash",
        "display": "Gemini Flash",
        "provider": "Google",
        "track": "best-valid",
        "protocol": {
            "temperature": "provider default",
            "max_tokens": 512,
            "thinking_budget": 0,
        },
    },
    {
        "key": "gemini_pro_preview",
        "display": "Gemini Pro Preview",
        "provider": "Google",
        "track": "best-valid",
        "protocol": {
            "temperature": "provider default",
            "max_tokens": 4096,
            "thinking_level": "low",
        },
    },
)

PAIRED_COMPARISONS: tuple[tuple[str, str], ...] = (
    ("openai_gpt_4_1_mini", "openai_gpt_5_4_mini"),
    ("openai_gpt_5_4_mini", "openai_gpt_5_4"),
    ("openai_gpt_4_1_mini", "openai_gpt_5_4"),
    ("openai_gpt_5_4", "claude_haiku_4_5"),
    ("openai_gpt_5_4", "claude_sonnet_4_6"),
    ("openai_gpt_5_4", "gemini_flash"),
    ("openai_gpt_5_4", "gemini_pro_preview"),
    ("gemini_flash", "gemini_pro_preview"),
    ("claude_sonnet_4_6", "gemini_pro_preview"),
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not records:
        raise ValueError(f"no records in {path.relative_to(ROOT)}")
    forbidden = {"prompt", "raw_prompt", "response", "raw_response", "model_response"}
    for index, record in enumerate(records):
        present = forbidden.intersection(record)
        if present:
            raise ValueError(
                f"{path.relative_to(ROOT)}:{index + 1} contains excluded fields: "
                f"{', '.join(sorted(present))}"
            )
    return records


def bootstrap(values: Sequence[float], *, seed: int) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise ValueError("cannot bootstrap an empty sample")
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, array.size, size=(N_RESAMPLES, array.size))
    means = array[indices].mean(axis=1)
    alpha = 1.0 - CONFIDENCE
    low, high = np.quantile(means, [alpha / 2, 1.0 - alpha / 2])
    return {
        "mean": float(array.mean()),
        "low": float(low),
        "high": float(high),
        "confidence": CONFIDENCE,
        "n_resamples": N_RESAMPLES,
    }


def summarise_model(spec: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    key = str(spec["key"])
    if len(records) != 120:
        raise ValueError(f"{key}: expected 120 records, found {len(records)}")
    if any(record.get("model") != key for record in records):
        raise ValueError(f"{key}: record contains the wrong model key")

    identities = [
        (str(record["environment"]), str(record["task_id"]), int(record["seed"]))
        for record in records
    ]
    if len(identities) != len(set(identities)):
        raise ValueError(f"{key}: duplicate task identities")

    environments: dict[str, dict[str, float | int]] = {}
    for environment in sorted({identity[0] for identity in identities}):
        subset = [record for record in records if record["environment"] == environment]
        environments[environment] = {
            "n": len(subset),
            "mean_score": _mean(float(record["score"]) for record in subset),
            "pass_rate": _mean(float(bool(record["passed"])) for record in subset),
            "risk_violation_rate": _mean(
                float(bool(record["risk_violation"])) for record in subset
            ),
        }

    return {
        **spec,
        "results_file": f"benchmark/{key}.jsonl",
        "n": len(records),
        "mean_score": bootstrap([float(record["score"]) for record in records], seed=BOOTSTRAP_SEED),
        "pass_rate": bootstrap(
            [float(bool(record["passed"])) for record in records], seed=BOOTSTRAP_SEED + 1
        ),
        "parse_failure_rate": bootstrap(
            [float(bool(record["parse_failed"])) for record in records],
            seed=BOOTSTRAP_SEED + 2,
        ),
        "risk_violation_rate": bootstrap(
            [float(bool(record["risk_violation"])) for record in records],
            seed=BOOTSTRAP_SEED + 3,
        ),
        "runtime_error_rate": bootstrap(
            [float(bool(record["runtime_error"])) for record in records],
            seed=BOOTSTRAP_SEED + 4,
        ),
        "environment_metrics": environments,
    }


def paired_difference(
    baseline: str,
    candidate: str,
    records: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    def keyed(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int], float]:
        return {
            (str(row["environment"]), str(row["task_id"]), int(row["seed"])): float(
                row["score"]
            )
            for row in rows
        }

    baseline_scores = keyed(records[baseline])
    candidate_scores = keyed(records[candidate])
    identities = sorted(set(baseline_scores) & set(candidate_scores))
    if len(identities) != 120:
        raise ValueError(f"{baseline} vs {candidate}: expected 120 aligned tasks")
    deltas = [candidate_scores[identity] - baseline_scores[identity] for identity in identities]
    return {
        "baseline": baseline,
        "candidate": candidate,
        "n_aligned": len(deltas),
        "mean_difference": bootstrap(deltas, seed=BOOTSTRAP_SEED),
    }


def build_summary() -> dict[str, Any]:
    records = {
        str(spec["key"]): load_jsonl(BENCHMARK / f"{spec['key']}.jsonl")
        for spec in MODEL_SPECS
    }
    identity_sets = [
        {
            (str(row["environment"]), str(row["task_id"]), int(row["seed"]))
            for row in model_records
        }
        for model_records in records.values()
    ]
    if any(identities != identity_sets[0] for identities in identity_sets[1:]):
        raise ValueError("the eight hosted-model rows do not share one task schedule")

    return {
        "schema_version": 1,
        "experiment": {
            "agent": "direct",
            "task_seed": 123,
            "tasks_per_environment": 20,
            "environments": [
                "bayesian_games",
                "auctions",
                "hidden_regimes",
                "market_making",
                "prediction_markets",
                "adversarial_risk",
            ],
            "model_rows": len(records),
            "task_records": sum(len(model_records) for model_records in records.values()),
        },
        "bootstrap": {
            "unit": "task",
            "seed": BOOTSTRAP_SEED,
            "confidence": CONFIDENCE,
            "n_resamples": N_RESAMPLES,
        },
        "models": [summarise_model(spec, records[str(spec["key"])]) for spec in MODEL_SPECS],
        "paired_differences": [
            paired_difference(baseline, candidate, records)
            for baseline, candidate in PAIRED_COMPARISONS
        ],
    }


def verify_interpretability() -> None:
    summary = load_json(SELECTED / "interpretability" / "six_seed_summary.json")
    seeds = summary["seeds"]
    if [seed["seed"] for seed in seeds] != [123, 124, 125, 126, 127, 128]:
        raise ValueError("interpretability summary does not contain seeds 123 to 128")

    metrics = {
        "heldout_action_accuracy": [
            seed["metrics"]["heldout_test"]["action_accuracy"] for seed in seeds
        ],
        "heldout_posterior_bucket_accuracy": [
            seed["metrics"]["heldout_test"]["posterior_bucket_accuracy"] for seed in seeds
        ],
        "heldout_risk_flag_accuracy": [
            seed["metrics"]["heldout_test"]["risk_flag_accuracy"] for seed in seeds
        ],
        "layer0_attn_action_recovery": [
            seed["metrics"]["whole_site_action_recovery"]["blocks.0.attn_out"]
            for seed in seeds
        ],
        "layer0_attn_posterior_recovery": [
            seed["metrics"]["whole_site_posterior_recovery"]["blocks.0.attn_out"]
            for seed in seeds
        ],
        "layer0_mlp_action_recovery": [
            seed["metrics"]["whole_site_action_recovery"]["blocks.0.mlp_out"]
            for seed in seeds
        ],
        "layer1_attn_action_recovery": [
            seed["metrics"]["whole_site_action_recovery"]["blocks.1.attn_out"]
            for seed in seeds
        ],
        "mismatched_action_matched_recovery": [
            seed["metrics"]["mismatched_donor"]["action"]["matched_recovery_rate"]
            for seed in seeds
        ],
        "mismatched_action_mismatched_recovery": [
            seed["metrics"]["mismatched_donor"]["action"]["mismatched_recovery_rate"]
            for seed in seeds
        ],
        "mismatched_posterior_matched_recovery": [
            seed["metrics"]["mismatched_donor"]["posterior_bucket"][
                "matched_recovery_rate"
            ]
            for seed in seeds
        ],
        "mismatched_posterior_mismatched_recovery": [
            seed["metrics"]["mismatched_donor"]["posterior_bucket"][
                "mismatched_recovery_rate"
            ]
            for seed in seeds
        ],
        "label_shuffle_real_accuracy": [
            seed["metrics"]["label_shuffle"]["real_test_accuracy"] for seed in seeds
        ],
        "label_shuffle_shuffled_accuracy": [
            seed["metrics"]["label_shuffle"]["shuffled_test_accuracy"] for seed in seeds
        ],
        "token_group_max_action_recovery": [
            seed["metrics"]["token_group"]["max_action_recovery"] for seed in seeds
        ],
        "validation_action_accuracy": [
            seed["metrics"]["validation"]["action_accuracy"] for seed in seeds
        ],
        "validation_posterior_bucket_accuracy": [
            seed["metrics"]["validation"]["posterior_bucket_accuracy"] for seed in seeds
        ],
        "validation_risk_flag_accuracy": [
            seed["metrics"]["validation"]["risk_flag_accuracy"] for seed in seeds
        ],
    }
    for key, values in metrics.items():
        committed = summary["aggregate_metrics"][key]
        calculated = {"mean": _mean(values), "min": min(values), "max": max(values), "n": 6}
        _assert_close(committed, calculated, context=key)

    checkpoint_data = load_json(SELECTED / "interpretability" / "checkpoint_hashes.json")
    expected_hashes = {int(row["seed"]): row["sha256"] for row in checkpoint_data["checkpoints"]}
    actual_hashes = {int(seed["seed"]): seed["checkpoint_sha256"] for seed in seeds}
    if expected_hashes != actual_hashes:
        raise ValueError("checkpoint hashes disagree with the six-seed summary")
    for seed, digest in expected_hashes.items():
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"seed {seed}: invalid checkpoint SHA256")


def verify_head_interventions() -> None:
    """Recompute retained head aggregates from the six per-seed records."""
    summary = load_json(SELECTED / "interpretability" / "head_position_summary.json")
    records = summary["per_seed"]
    expected_seeds = [123, 124, 125, 126, 127, 128]
    if summary["seeds"] != expected_seeds or [record["seed"] for record in records] != expected_seeds:
        raise ValueError("head intervention summary does not contain seeds 123 to 128")

    for group in ("per_head_patching", "per_head_ablation"):
        aggregate = summary[group]
        sites = set(aggregate)
        if any(set(record[group]) != sites for record in records):
            raise ValueError(f"{group}: per-seed head sites differ")
        for site, metrics in aggregate.items():
            for metric, committed in metrics.items():
                values = [float(record[group][site][metric]) for record in records]
                calculated = {
                    "mean": _mean(values),
                    "min": min(values),
                    "max": max(values),
                    "n": len(values),
                }
                _assert_close(committed, calculated, context=f"{group}.{site}.{metric}")

    top_counts: dict[str, int] = {}
    for record in records:
        top_site = max(
            record["per_head_patching"],
            key=lambda site: record["per_head_patching"][site]["matched_action_recovery"],
        )
        top_counts[top_site] = top_counts.get(top_site, 0) + 1
    if top_counts != summary["top_head_counts"]:
        raise ValueError("top-head counts do not match the per-seed patching records")

    for record in records:
        if set(record["max_individual_position_action_recovery"]) != {
            "blocks.0.attn_out",
            "blocks.1.attn_out",
        }:
            raise ValueError("position-patching sites differ across seeds")


def write_integrity_files() -> None:
    evidence = sorted(
        path
        for path in SELECTED.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    )
    counts = {
        path.relative_to(SELECTED).as_posix(): len(load_jsonl(path))
        for path in evidence
        if path.suffix == ".jsonl"
    }
    manifest = {
        "schema_version": 1,
        "description": "Selected evidence used by the README and figures.",
        "provenance": {
            "benchmark": {
                "source_evidence": [
                    path.relative_to(SELECTED).as_posix()
                    for path in evidence
                    if path.parent == BENCHMARK and path.suffix == ".jsonl"
                ],
                "consolidation": (
                    "Numeric task outcomes were projected from eight completed direct-agent "
                    "runs. Prompts, model responses, caches and provider logs were excluded."
                ),
                "configuration": "configs/benchmark/hosted_pilot.yaml",
                "settings": {
                    "task_seed": 123,
                    "tasks_per_environment": 20,
                    "environments": 6,
                    "bootstrap_seed": BOOTSTRAP_SEED,
                    "bootstrap_resamples": N_RESAMPLES,
                    "confidence": CONFIDENCE,
                },
            },
            "interpretability": {
                "source_evidence": [
                    "interpretability/six_seed_summary.json",
                    "interpretability/head_position_summary.json",
                    "interpretability/checkpoint_hashes.json",
                ],
                "consolidation": (
                    "Numeric metrics were retained from six completed local training and causal-"
                    "intervention runs. Checkpoints, activations and Markdown reports were excluded."
                ),
                "configuration": [
                    "configs/training/medium.yaml",
                    "configs/training/medium_eval.yaml",
                    "configs/interpretability/six_seed.yaml",
                ],
                "settings": {
                    "training_seeds": [123, 124, 125, 126, 127, 128],
                    "training_traces_per_seed": 12000,
                    "heldout_traces_per_seed": 2000,
                    "layers": 2,
                    "attention_heads_per_layer": 4,
                },
            },
        },
        "benchmark": {
            "model_rows": len(MODEL_SPECS),
            "task_records": sum(counts.values()),
            "records_by_file": counts,
        },
        "interpretability": {"seeds": [123, 124, 125, 126, 127, 128]},
        "files": {
            path.relative_to(SELECTED).as_posix(): {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in evidence
        },
    }
    _write_json(MANIFEST_PATH, manifest)
    checksum_paths = [*evidence, MANIFEST_PATH]
    lines = [
        f"{sha256(path)}  {path.relative_to(SELECTED).as_posix()}" for path in checksum_paths
    ]
    CHECKSUMS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def verify_integrity_files() -> None:
    manifest = load_json(MANIFEST_PATH)
    actual_files = {
        path.relative_to(SELECTED).as_posix()
        for path in SELECTED.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "SHA256SUMS"}
    }
    if set(manifest["files"]) != actual_files:
        raise ValueError("manifest file list differs from selected evidence")
    for relative, metadata in manifest["files"].items():
        path = SELECTED / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        if path.stat().st_size != metadata["bytes"] or sha256(path) != metadata["sha256"]:
            raise ValueError(f"manifest mismatch: {relative}")

    expected: dict[str, str] = {}
    for line in CHECKSUMS_PATH.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", maxsplit=1)
        expected[relative] = digest
    if set(expected) != actual_files | {"manifest.json"}:
        raise ValueError("SHA256SUMS file list differs from selected evidence")
    for relative, digest in expected.items():
        if sha256(SELECTED / relative) != digest:
            raise ValueError(f"SHA256SUMS mismatch: {relative}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mean(values: Iterable[float]) -> float:
    materialised = list(values)
    return sum(materialised) / len(materialised)


def _assert_close(actual: Any, expected: Any, *, context: str = "summary") -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError(f"{context}: structure differs")
        for key, value in expected.items():
            _assert_close(actual[key], value, context=f"{context}.{key}")
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError(f"{context}: list differs")
        for index, value in enumerate(expected):
            _assert_close(actual[index], value, context=f"{context}[{index}]")
        return
    if isinstance(expected, float):
        if not isinstance(actual, (int, float)) or not np.isclose(actual, expected, atol=1e-12):
            raise ValueError(f"{context}: {actual!r} != {expected!r}")
        return
    if actual != expected:
        raise ValueError(f"{context}: {actual!r} != {expected!r}")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite the derived summary and integrity files.",
    )
    args = parser.parse_args()

    calculated = build_summary()
    if args.write:
        _write_json(SUMMARY_PATH, calculated)
        verify_interpretability()
        verify_head_interventions()
        write_integrity_files()
    else:
        _assert_close(load_json(SUMMARY_PATH), calculated, context="benchmark summary")
        verify_interpretability()
        verify_head_interventions()
        verify_integrity_files()

    print("8 hosted-model rows verified")
    print("960 aligned task records verified")
    print("6 interpretability seeds and checkpoint hashes verified")
    print("per-seed head and position interventions verified")
    print("selected-result integrity verified")


if __name__ == "__main__":
    main()
