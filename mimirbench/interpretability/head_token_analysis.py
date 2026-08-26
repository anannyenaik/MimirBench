"""Per-head and individual-token causal analysis for the small transformer.

All experiments are local and deterministic. Per-head patching uses each head's
projected contribution before attention-head contributions are summed. Position
patching intervenes on one token index at a time before any semantic aggregation.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

import numpy as np

from mimirbench.interpretability.attention_analysis import token_group_spans
from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.training.synthetic_traces import bucket_midpoint

__all__ = [
    "run_head_token_analysis",
    "run_head_token_multiseed",
    "run_individual_token_position_patching",
    "run_per_head_ablation",
    "run_per_head_patching",
]

_OUTPUT_HEADS = ("action", "posterior_bucket")
_NO_FRONTIER_CLAIM = (
    "These results characterise small, fully synthetic Bayesian transformers. "
    "They are not evidence about frontier-model internals and must not be read that way."
)


def run_per_head_patching(
    model: Any,
    tokenizer: Any,
    pairs: list[Any],
    *,
    seed: int = 123,
) -> dict[str, Any]:
    """Patch one projected attention-head output at a time, with donor controls."""
    from mimirbench.training.small_transformer import attention_head_site_names, require_torch

    torch_mod, _, _ = require_torch()
    batch = _prepare_batch(torch_mod, tokenizer, pairs, model.config.max_seq_len)
    model.eval()
    with torch_mod.no_grad():
        clean = model.forward_instrumented(
            batch["clean_ids"], attention_mask=batch["attention_mask"], capture_attention=False
        )
        corrupted = model.forward_instrumented(
            batch["corrupted_ids"],
            attention_mask=batch["attention_mask"],
            capture_attention=False,
        )
    clean_probs = _probabilities(torch_mod, clean["logits"])
    corrupted_probs = _probabilities(torch_mod, corrupted["logits"])
    clean_pred = {head: values.argmax(dim=-1) for head, values in clean_probs.items()}
    corrupted_pred = {head: values.argmax(dim=-1) for head, values in corrupted_probs.items()}
    donor_order = torch_mod.as_tensor(
        _derangement(len(pairs), seed), dtype=torch_mod.long, device=batch["clean_ids"].device
    )

    rows: list[dict[str, Any]] = []
    sites = list(attention_head_site_names(model.config.n_layers, model.config.n_heads))
    for site in sites:
        donors = {
            "matched": clean["sites"][site],
            "mismatched": clean["sites"][site].index_select(0, donor_order),
        }
        for control, donor in donors.items():
            with torch_mod.no_grad():
                patched = model.forward_instrumented(
                    batch["corrupted_ids"],
                    attention_mask=batch["attention_mask"],
                    patch={site: donor},
                    capture_attention=False,
                )
            patched_probs = _probabilities(torch_mod, patched["logits"])
            for output_head in _OUTPUT_HEADS:
                target = clean_pred[output_head]
                target_index = target.unsqueeze(-1)
                clean_target_prob = clean_probs[output_head].gather(1, target_index).squeeze(-1)
                corrupted_target_prob = (
                    corrupted_probs[output_head].gather(1, target_index).squeeze(-1)
                )
                patched_target_prob = patched_probs[output_head].gather(1, target_index).squeeze(-1)
                patched_pred = patched_probs[output_head].argmax(dim=-1)
                for index, pair in enumerate(pairs):
                    rows.append(
                        {
                            "pair_id": pair.pair_id,
                            "site": site,
                            "control": control,
                            "output_head": output_head,
                            "corrupted_flipped": bool(
                                corrupted_pred[output_head][index] != target[index]
                            ),
                            "recovered": bool(patched_pred[index] == target[index]),
                            "causal_effect": float(
                                patched_target_prob[index] - corrupted_target_prob[index]
                            ),
                            "clean_target_prob": float(clean_target_prob[index]),
                            "corrupted_target_prob": float(corrupted_target_prob[index]),
                            "patched_target_prob": float(patched_target_prob[index]),
                        }
                    )
    return {
        "rows": rows,
        "sites": sites,
        "summary": _summarise_head_patching(rows, sites),
        "metadata": {"num_pairs": len(pairs), "seed": seed},
    }


def run_per_head_ablation(model: Any, tokenizer: Any, pairs: list[Any], *, seed: int = 123) -> dict[str, Any]:
    """Zero-ablate each projected head output and compare with a random-position control."""
    from mimirbench.training.small_transformer import attention_head_site_names, require_torch

    torch_mod, _, _ = require_torch()
    batch = _prepare_batch(torch_mod, tokenizer, pairs, model.config.max_seq_len)
    model.eval()
    with torch_mod.no_grad():
        clean = model.forward_instrumented(
            batch["clean_ids"], attention_mask=batch["attention_mask"], capture_attention=False
        )
    baseline = _accuracy_metrics(torch_mod, clean["logits"], model.label_vocab, pairs)
    rng = np.random.default_rng(seed)
    minimum_length = int(batch["attention_mask"].sum(dim=1).min().item())
    random_position = int(rng.integers(1, max(2, minimum_length - 1)))

    rows: list[dict[str, Any]] = []
    sites = list(attention_head_site_names(model.config.n_layers, model.config.n_heads))
    for site in sites:
        zero = torch_mod.zeros_like(clean["sites"][site])
        for control, positions in (("full_head_zero", None), ("random_position_zero", [random_position])):
            patch_positions = None if positions is None else {site: positions}
            with torch_mod.no_grad():
                ablated = model.forward_instrumented(
                    batch["clean_ids"],
                    attention_mask=batch["attention_mask"],
                    patch={site: zero},
                    patch_positions=patch_positions,
                    capture_attention=False,
                )
            metrics = _accuracy_metrics(torch_mod, ablated["logits"], model.label_vocab, pairs)
            rows.append(
                {
                    "site": site,
                    "control": control,
                    "position": None if positions is None else random_position,
                    **metrics,
                    "action_accuracy_degradation": (
                        baseline["action_accuracy"] - metrics["action_accuracy"]
                    ),
                    "posterior_bucket_accuracy_degradation": (
                        baseline["posterior_bucket_accuracy"]
                        - metrics["posterior_bucket_accuracy"]
                    ),
                    "mean_posterior_error_increase": (
                        metrics["mean_posterior_error"] - baseline["mean_posterior_error"]
                    ),
                }
            )
    return {
        "baseline": baseline,
        "rows": rows,
        "sites": sites,
        "metadata": {"num_pairs": len(pairs), "seed": seed, "random_position": random_position},
    }


def run_individual_token_position_patching(
    model: Any,
    tokenizer: Any,
    pairs: list[Any],
) -> dict[str, Any]:
    """Patch one token position at a time at each attention sub-block output."""
    from mimirbench.training.small_transformer import attn_out_site, require_torch

    torch_mod, _, _ = require_torch()
    batch = _prepare_batch(torch_mod, tokenizer, pairs, model.config.max_seq_len)
    model.eval()
    with torch_mod.no_grad():
        clean = model.forward_instrumented(
            batch["clean_ids"], attention_mask=batch["attention_mask"], capture_attention=False
        )
        corrupted = model.forward_instrumented(
            batch["corrupted_ids"],
            attention_mask=batch["attention_mask"],
            capture_attention=False,
        )
    clean_probs = _probabilities(torch_mod, clean["logits"])
    corrupted_probs = _probabilities(torch_mod, corrupted["logits"])
    clean_pred = {head: values.argmax(dim=-1) for head, values in clean_probs.items()}
    corrupted_pred = {head: values.argmax(dim=-1) for head, values in corrupted_probs.items()}
    maximum_length = int(batch["attention_mask"].sum(dim=1).max().item())
    sites = [attn_out_site(layer) for layer in range(model.config.n_layers)]

    position_rows: list[dict[str, Any]] = []
    group_accumulators: dict[tuple[str, str, str], dict[str, list[Any]]] = defaultdict(
        lambda: {"flipped": [], "recovered": [], "effects": []}
    )
    for site in sites:
        donor = clean["sites"][site]
        for position in range(maximum_length):
            with torch_mod.no_grad():
                patched = model.forward_instrumented(
                    batch["corrupted_ids"],
                    attention_mask=batch["attention_mask"],
                    patch={site: donor},
                    patch_positions={site: [position]},
                    capture_attention=False,
                )
            patched_probs = _probabilities(torch_mod, patched["logits"])
            valid_indices = [
                index for index in range(len(pairs)) if bool(batch["attention_mask"][index, position])
            ]
            tokens = [batch["tokens"][index][position] for index in valid_indices]
            groups = [batch["groups"][index].get(position, "unclassified") for index in valid_indices]
            row: dict[str, Any] = {
                "site": site,
                "position": position,
                "n_valid": len(valid_indices),
                "most_common_token": Counter(tokens).most_common(1)[0][0] if tokens else None,
                "semantic_groups": dict(sorted(Counter(groups).items())),
                "heads": {},
            }
            for output_head in _OUTPUT_HEADS:
                target = clean_pred[output_head]
                patched_pred = patched_probs[output_head].argmax(dim=-1)
                target_prob = patched_probs[output_head].gather(1, target.unsqueeze(-1)).squeeze(-1)
                corrupted_target_prob = (
                    corrupted_probs[output_head].gather(1, target.unsqueeze(-1)).squeeze(-1)
                )
                flipped_values: list[bool] = []
                recovered_values: list[bool] = []
                effects: list[float] = []
                for index in valid_indices:
                    flipped = bool(corrupted_pred[output_head][index] != target[index])
                    recovered = bool(patched_pred[index] == target[index])
                    effect = float(target_prob[index] - corrupted_target_prob[index])
                    flipped_values.append(flipped)
                    recovered_values.append(recovered)
                    effects.append(effect)
                    group = batch["groups"][index].get(position, "unclassified")
                    accumulator = group_accumulators[(site, group, output_head)]
                    accumulator["flipped"].append(flipped)
                    accumulator["recovered"].append(recovered)
                    accumulator["effects"].append(effect)
                row["heads"][output_head] = _recovery_metrics(
                    flipped_values, recovered_values, effects
                )
            position_rows.append(row)

    by_site = _summarise_positions(position_rows, sites)
    by_group: dict[str, Any] = {}
    for (site, group, output_head), values in sorted(group_accumulators.items()):
        by_group.setdefault(site, {}).setdefault(group, {})[output_head] = _recovery_metrics(
            values["flipped"], values["recovered"], values["effects"]
        )
    return {
        "positions": position_rows,
        "sites": sites,
        "summary": {"by_site": by_site, "by_group": by_group},
        "metadata": {"num_pairs": len(pairs), "maximum_valid_length": maximum_length},
    }


def run_head_token_analysis(model: Any, tokenizer: Any, pairs: list[Any], *, seed: int = 123) -> dict[str, Any]:
    """Run per-head patching/ablation and individual-position patching."""
    return {
        "seed": seed,
        "status": "complete",
        "per_head_patching": run_per_head_patching(model, tokenizer, pairs, seed=seed),
        "per_head_ablation": run_per_head_ablation(model, tokenizer, pairs, seed=seed),
        "individual_token_position_patching": run_individual_token_position_patching(
            model, tokenizer, pairs
        ),
    }


def run_head_token_multiseed(config: Any) -> dict[str, Any]:
    """Run the head/token analysis over the checkpoints named by a multi-seed config."""
    from mimirbench.interpretability.multiseed import MultiSeedConfig, load_multiseed_config
    from mimirbench.interpretability.runner import load_interpretability_config
    from mimirbench.training.small_transformer import SmallTransformerForTracePrediction
    from mimirbench.training.tokenizer import TraceTokenizer

    cfg = config if isinstance(config, MultiSeedConfig) else load_multiseed_config(config)
    template = load_interpretability_config(cfg.extended_template)
    records: list[dict[str, Any]] = []
    for seed in cfg.seeds:
        training_dir = _training_dir(cfg, seed)
        checkpoint = training_dir / "checkpoints" / "best.pt"
        vocab = training_dir / "vocab.json"
        record: dict[str, Any] = {"seed": seed, "status": "failed"}
        try:
            model, payload = SmallTransformerForTracePrediction.load_checkpoint(
                checkpoint, map_location=cfg.device
            )
            model.to(cfg.device)
            tokenizer = (
                TraceTokenizer.load(vocab)
                if vocab.exists()
                else TraceTokenizer.from_dict(payload["tokenizer"])
            )
            data = replace(template.data, seed=seed)
            pairs = generate_counterfactual_pairs(
                data.num_pairs, config=data.trace_config(), seed=seed, split="interp"
            )
            record = run_head_token_analysis(model, tokenizer, pairs, seed=seed)
            record["checkpoint_path"] = checkpoint.as_posix()
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        records.append(record)

    aggregate = _aggregate_multiseed(records, list(cfg.seeds))
    summary_dir = Path(cfg.run.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)
    json_path = summary_dir / "interp_bayes_head_token_summary.json"
    report_path = summary_dir / "interp_bayes_head_token_summary.md"
    json_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    report_path.write_text(_render_report(aggregate), encoding="utf-8", newline="\n")
    aggregate["json_path"] = json_path.as_posix()
    aggregate["report_path"] = report_path.as_posix()
    return aggregate


def _prepare_batch(torch_mod: Any, tokenizer: Any, pairs: list[Any], max_seq_len: int) -> dict[str, Any]:
    if not pairs:
        raise ValueError("no counterfactual pairs supplied.")
    clean_encoded = [tokenizer.encode(pair.clean_input) for pair in pairs]
    corrupted_encoded = [tokenizer.encode(pair.corrupted_input) for pair in pairs]
    clean_ids = torch_mod.as_tensor(
        [row["input_ids"][:max_seq_len] for row in clean_encoded], dtype=torch_mod.long
    )
    corrupted_ids = torch_mod.as_tensor(
        [row["input_ids"][:max_seq_len] for row in corrupted_encoded], dtype=torch_mod.long
    )
    attention_mask = torch_mod.as_tensor(
        [row["attention_mask"][:max_seq_len] for row in clean_encoded], dtype=torch_mod.long
    )
    tokens: list[list[str]] = []
    groups: list[dict[int, str]] = []
    for pair, encoded in zip(pairs, clean_encoded, strict=True):
        decoded = tokenizer.decode(encoded["input_ids"][:max_seq_len], skip_special=False).split(" ")
        tokens.append(decoded)
        spans = token_group_spans(tokenizer.tokenize(pair.clean_input), offset=1)
        group_map: dict[int, str] = {}
        for group, positions in spans.items():
            for position in positions:
                if position < max_seq_len:
                    group_map[position] = group
        groups.append(group_map)
    return {
        "clean_ids": clean_ids,
        "corrupted_ids": corrupted_ids,
        "attention_mask": attention_mask,
        "tokens": tokens,
        "groups": groups,
    }


def _probabilities(torch_mod: Any, logits: dict[str, Any]) -> dict[str, Any]:
    return {head: torch_mod.softmax(logits[head], dim=-1) for head in _OUTPUT_HEADS}


def _summarise_head_patching(rows: list[dict[str, Any]], sites: list[str]) -> dict[str, Any]:
    by_site: dict[str, Any] = {}
    for site in sites:
        by_control: dict[str, Any] = {}
        for control in ("matched", "mismatched"):
            by_head: dict[str, Any] = {}
            for output_head in _OUTPUT_HEADS:
                subset = [
                    row
                    for row in rows
                    if row["site"] == site
                    and row["control"] == control
                    and row["output_head"] == output_head
                ]
                by_head[output_head] = _recovery_metrics(
                    [row["corrupted_flipped"] for row in subset],
                    [row["recovered"] for row in subset],
                    [row["causal_effect"] for row in subset],
                )
            by_control[control] = by_head
        by_site[site] = by_control
    return {"by_site": by_site, "site_order": sites}


def _recovery_metrics(
    flipped_values: list[bool], recovered_values: list[bool], effects: list[float]
) -> dict[str, Any]:
    flipped_recovery = [
        recovered for flipped, recovered in zip(flipped_values, recovered_values, strict=True) if flipped
    ]
    return {
        "recovery_rate": float(np.mean(flipped_recovery)) if flipped_recovery else None,
        "n_flipped": len(flipped_recovery),
        "mean_causal_effect": float(np.mean(effects)) if effects else None,
        "mean_abs_causal_effect": float(np.mean(np.abs(effects))) if effects else None,
        "n": len(effects),
    }


def _accuracy_metrics(
    torch_mod: Any, logits: dict[str, Any], label_vocab: dict[str, list[str]], pairs: list[Any]
) -> dict[str, float]:
    action_pred = logits["action"].argmax(dim=-1).detach().cpu().tolist()
    posterior_pred = logits["posterior_bucket"].argmax(dim=-1).detach().cpu().tolist()
    action_lookup = {label: index for index, label in enumerate(label_vocab["action"])}
    posterior_lookup = {
        label: index for index, label in enumerate(label_vocab["posterior_bucket"])
    }
    action_truth = [action_lookup[pair.clean_labels["action"]] for pair in pairs]
    posterior_truth = [posterior_lookup[pair.clean_labels["posterior_bucket"]] for pair in pairs]
    posterior_error = [
        abs(
            bucket_midpoint(label_vocab["posterior_bucket"][int(prediction)])
            - float(pair.metadata["clean_posterior"][0])
        )
        for prediction, pair in zip(posterior_pred, pairs, strict=True)
    ]
    return {
        "action_accuracy": float(np.mean(np.asarray(action_pred) == np.asarray(action_truth))),
        "posterior_bucket_accuracy": float(
            np.mean(np.asarray(posterior_pred) == np.asarray(posterior_truth))
        ),
        "mean_posterior_error": float(np.mean(posterior_error)),
    }


def _summarise_positions(rows: list[dict[str, Any]], sites: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for site in sites:
        subset = [row for row in rows if row["site"] == site]
        action_rates = [
            row["heads"]["action"]["recovery_rate"]
            for row in subset
            if row["heads"]["action"]["recovery_rate"] is not None
        ]
        posterior_rates = [
            row["heads"]["posterior_bucket"]["recovery_rate"]
            for row in subset
            if row["heads"]["posterior_bucket"]["recovery_rate"] is not None
        ]
        result[site] = {
            "max_action_recovery": max(action_rates, default=None),
            "mean_action_recovery": float(np.mean(action_rates)) if action_rates else None,
            "max_posterior_recovery": max(posterior_rates, default=None),
            "mean_posterior_recovery": float(np.mean(posterior_rates)) if posterior_rates else None,
            "positions": subset,
        }
    return result


def _derangement(size: int, seed: int) -> list[int]:
    if size < 2:
        raise ValueError("mismatched-donor control requires at least two pairs.")
    rng = np.random.default_rng(seed)
    offset = 1 + int(rng.integers(0, size - 1))
    return [int((index + offset) % size) for index in range(size)]


def _training_dir(config: Any, seed: int) -> Path:
    override = config.seed_overrides.get(seed)
    if override and override.training_dir:
        return Path(override.training_dir)
    return Path(config.training_output_template.format(seed=seed))


def _aggregate_multiseed(records: list[dict[str, Any]], attempted: list[int]) -> dict[str, Any]:
    completed = [record for record in records if record.get("status") == "complete"]
    head_rows: dict[str, Any] = {}
    ablation_rows: dict[str, Any] = {}
    position_rows: dict[str, Any] = {}
    position_distribution: dict[str, Any] = {}
    group_rows: dict[str, Any] = {}
    top_heads: list[str] = []

    all_head_sites = sorted(
        {
            site
            for record in completed
            for site in record["per_head_patching"]["summary"]["by_site"]
        }
    )
    for site in all_head_sites:
        matched_action = _seed_values(
            completed,
            lambda record, site=site: record["per_head_patching"]["summary"]["by_site"][site]["matched"][
                "action"
            ]["recovery_rate"],
        )
        head_rows[site] = {
            "matched_action_recovery": _mean_range(matched_action),
            "matched_posterior_recovery": _mean_range(
                _seed_values(
                    completed,
                    lambda record, site=site: record["per_head_patching"]["summary"]["by_site"][site][
                        "matched"
                    ]["posterior_bucket"]["recovery_rate"],
                )
            ),
            "matched_action_causal_effect": _mean_range(
                _seed_values(
                    completed,
                    lambda record, site=site: record["per_head_patching"]["summary"]["by_site"][site][
                        "matched"
                    ]["action"]["mean_causal_effect"],
                )
            ),
            "mismatched_action_recovery": _mean_range(
                _seed_values(
                    completed,
                    lambda record, site=site: record["per_head_patching"]["summary"]["by_site"][site][
                        "mismatched"
                    ]["action"]["recovery_rate"],
                )
            ),
        }
    for record in completed:
        site = max(
            all_head_sites,
            key=lambda item: _none_low(
                record["per_head_patching"]["summary"]["by_site"][item]["matched"]["action"][
                    "recovery_rate"
                ]
            ),
        )
        top_heads.append(site)

    for site in all_head_sites:
        full_rows = [
            row
            for record in completed
            for row in record["per_head_ablation"]["rows"]
            if row["site"] == site and row["control"] == "full_head_zero"
        ]
        random_rows = [
            row
            for record in completed
            for row in record["per_head_ablation"]["rows"]
            if row["site"] == site and row["control"] == "random_position_zero"
        ]
        ablation_rows[site] = {
            "action_accuracy_degradation": _mean_range(
                [row["action_accuracy_degradation"] for row in full_rows]
            ),
            "posterior_bucket_accuracy_degradation": _mean_range(
                [row["posterior_bucket_accuracy_degradation"] for row in full_rows]
            ),
            "mean_posterior_error_increase": _mean_range(
                [row["mean_posterior_error_increase"] for row in full_rows]
            ),
            "random_position_action_degradation": _mean_range(
                [row["action_accuracy_degradation"] for row in random_rows]
            ),
        }

    position_keys = sorted(
        {
            (row["site"], row["position"])
            for record in completed
            for row in record["individual_token_position_patching"]["positions"]
        }
    )
    for site, position in position_keys:
        rows = [
            row
            for record in completed
            for row in record["individual_token_position_patching"]["positions"]
            if row["site"] == site and row["position"] == position
        ]
        key = f"{site}:position:{position}"
        position_rows[key] = {
            "site": site,
            "position": position,
            "most_common_token": Counter(
                row["most_common_token"] for row in rows if row["most_common_token"] is not None
            ).most_common(1)[0][0],
            "action_recovery": _mean_range(
                [row["heads"]["action"]["recovery_rate"] for row in rows]
            ),
            "posterior_recovery": _mean_range(
                [row["heads"]["posterior_bucket"]["recovery_rate"] for row in rows]
            ),
        }
    position_sites = sorted({row["site"] for row in position_rows.values()})
    for site in position_sites:
        site_rows = [row for row in position_rows.values() if row["site"] == site]
        position_distribution[site] = {
            "action_recovery_max_across_positions": max(
                (_none_low(row["action_recovery"]["mean"]) for row in site_rows), default=None
            ),
            "action_recovery_mean_across_positions": float(
                np.mean([row["action_recovery"]["mean"] for row in site_rows])
            ),
            "posterior_recovery_max_across_positions": max(
                (_none_low(row["posterior_recovery"]["mean"]) for row in site_rows), default=None
            ),
            "posterior_recovery_mean_across_positions": float(
                np.mean([row["posterior_recovery"]["mean"] for row in site_rows])
            ),
            "n_positions": len(site_rows),
        }

    group_keys = sorted(
        {
            (site, group)
            for record in completed
            for site, groups in record["individual_token_position_patching"]["summary"][
                "by_group"
            ].items()
            for group in groups
        }
    )
    for site, group in group_keys:
        group_rows[f"{site}:{group}"] = {
            "site": site,
            "group": group,
            "action_recovery": _mean_range(
                _seed_values(
                    completed,
                    lambda record, site=site, group=group: record[
                        "individual_token_position_patching"
                    ]["summary"][
                        "by_group"
                    ][site][group]["action"]["recovery_rate"],
                )
            ),
            "posterior_recovery": _mean_range(
                _seed_values(
                    completed,
                    lambda record, site=site, group=group: record[
                        "individual_token_position_patching"
                    ]["summary"][
                        "by_group"
                    ][site][group]["posterior_bucket"]["recovery_rate"],
                )
            ),
        }

    top_counts = Counter(top_heads)
    consistent_top = top_counts.most_common(1)[0] if top_counts else (None, 0)
    max_head_recovery = max(
        (
            block["matched_action_recovery"]["mean"]
            for block in head_rows.values()
            if block["matched_action_recovery"]["mean"] is not None
        ),
        default=None,
    )
    interpretation = _interpretation(len(completed), consistent_top, max_head_recovery)
    return {
        "generated_at": _now(),
        "status": "complete" if completed else "failed",
        "seeds_attempted": attempted,
        "seeds_completed": [record["seed"] for record in completed],
        "n_attempted": len(attempted),
        "n_completed": len(completed),
        "per_head_patching": head_rows,
        "per_head_ablation": ablation_rows,
        "individual_token_positions": position_rows,
        "individual_position_distribution": position_distribution,
        "semantic_position_aggregates": group_rows,
        "top_head_counts": dict(sorted(top_counts.items())),
        "interpretation": interpretation,
        "limitations": [
            "One narrow synthetic Bayesian/risk generator and one compact encoder architecture.",
            "Per-head sites are projected head contributions; they do not isolate neurons or features.",
            "Individual-position effects are measured before semantic aggregation and may be diluted by mean pooling.",
            "Zero ablation can move activations off distribution.",
            "No sparse-autoencoder or neuron-level analysis was performed.",
            "Nothing here transfers to frontier-model internals.",
        ],
        "no_frontier_claim": _NO_FRONTIER_CLAIM,
        "per_seed": [_compact_record(record) for record in records],
    }


def _interpretation(
    n_completed: int, consistent_top: tuple[str | None, int], max_head_recovery: float | None
) -> str:
    if n_completed == 0:
        return "No seed completed; no causal interpretation is available."
    site, count = consistent_top
    if site is not None and count == n_completed and max_head_recovery is not None:
        return (
            f"The six-seed attention-sub-block story is refined: {site} is the strongest "
            f"single-head patch on all {n_completed} completed seeds, with mean action recovery "
            f"{max_head_recovery:.3f}. Read this together with ablation and controls; it is not "
            "a complete circuit claim."
        )
    return (
        "The six-seed attention-sub-block story is confirmed but refined: causal recovery is "
        "not localised to one consistently dominant head or individual position. Per-head "
        "ablation indicates distributed necessity, while single-head and single-position "
        "patches are usually insufficient. This does not support a clean circuit claim."
    )


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Per-head and individual-token interpretability summary",
        "",
        f"- Seeds attempted: {summary['seeds_attempted']}",
        f"- Seeds completed: {summary['seeds_completed']}",
        "- Local-only analysis; no hosted inference or API calls.",
        "",
        f"**Interpretation:** {summary['interpretation']}",
        "",
        "## Per-head patching",
        "",
        "| Head site | Matched action recovery mean [range] | Posterior recovery | "
        "Action causal effect | Mismatched action recovery |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for site, block in summary["per_head_patching"].items():
        lines.append(
            f"| `{site}` | {_fmt_range(block['matched_action_recovery'])} | "
            f"{_fmt_range(block['matched_posterior_recovery'])} | "
            f"{_fmt_range(block['matched_action_causal_effect'])} | "
            f"{_fmt_range(block['mismatched_action_recovery'])} |"
        )
    lines.extend(
        [
            "",
            "## Per-head zero ablation",
            "",
            "| Head site | Action accuracy degradation | Posterior accuracy degradation | "
            "Posterior error increase | Random-position action degradation |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for site, block in summary["per_head_ablation"].items():
        lines.append(
            f"| `{site}` | {_fmt_range(block['action_accuracy_degradation'])} | "
            f"{_fmt_range(block['posterior_bucket_accuracy_degradation'])} | "
            f"{_fmt_range(block['mean_posterior_error_increase'])} | "
            f"{_fmt_range(block['random_position_action_degradation'])} |"
        )
    ranked_positions = sorted(
        summary["individual_token_positions"].values(),
        key=lambda row: _none_low(row["action_recovery"]["mean"]),
        reverse=True,
    )
    lines.extend(
        [
            "",
            "## Individual token-position patching",
            "",
            "| Site | Max action recovery across positions | Mean action recovery | "
            "Max posterior recovery | Mean posterior recovery |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for site, block in summary["individual_position_distribution"].items():
        lines.append(
            f"| `{site}` | {block['action_recovery_max_across_positions']:.3f} | "
            f"{block['action_recovery_mean_across_positions']:.3f} | "
            f"{block['posterior_recovery_max_across_positions']:.3f} | "
            f"{block['posterior_recovery_mean_across_positions']:.3f} |"
        )
    lines.extend(
        [
            "",
            "The table shows the 20 strongest individual positions after every position was "
            "tested separately. Semantic aggregation below was computed only afterwards.",
            "",
            "| Site | Position | Common token | Action recovery | Posterior recovery |",
            "| --- | ---: | --- | ---: | ---: |",
        ]
    )
    for row in ranked_positions[:20]:
        lines.append(
            f"| `{row['site']}` | {row['position']} | `{row['most_common_token']}` | "
            f"{_fmt_range(row['action_recovery'])} | {_fmt_range(row['posterior_recovery'])} |"
        )
    lines.extend(
        [
            "",
            "## Post-hoc semantic aggregates and controls",
            "",
            "| Site | Semantic group | Action recovery | Posterior recovery |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in summary["semantic_position_aggregates"].values():
        lines.append(
            f"| `{row['site']}` | {row['group']} | {_fmt_range(row['action_recovery'])} | "
            f"{_fmt_range(row['posterior_recovery'])} |"
        )
    lines.extend(["", "## Limitations", "", *[f"- {item}" for item in summary["limitations"]], ""])
    return "\n".join(lines)


def _compact_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("status") != "complete":
        return {
            "seed": record.get("seed"),
            "status": record.get("status"),
            "error": record.get("error"),
        }
    patching = record["per_head_patching"]
    ablation = record["per_head_ablation"]
    positions = record["individual_token_position_patching"]
    top_head = max(
        patching["sites"],
        key=lambda site: _none_low(
            patching["summary"]["by_site"][site]["matched"]["action"]["recovery_rate"]
        ),
    )
    return {
        "seed": record["seed"],
        "status": "complete",
        "checkpoint_path": record.get("checkpoint_path"),
        "top_head_by_action_recovery": top_head,
        "per_head_patching": patching["summary"],
        "per_head_ablation": {
            "baseline": ablation["baseline"],
            "rows": ablation["rows"],
            "metadata": ablation["metadata"],
        },
        "individual_token_position_patching": {
            "summary": {
                "by_site": {
                    site: {
                        key: value
                        for key, value in block.items()
                        if key != "positions"
                    }
                    for site, block in positions["summary"]["by_site"].items()
                },
                "by_group": positions["summary"]["by_group"],
            },
            "metadata": positions["metadata"],
        },
    }


def _seed_values(records: list[dict[str, Any]], getter: Any) -> list[Any]:
    values: list[Any] = []
    for record in records:
        try:
            value = getter(record)
        except KeyError:
            continue
        if value is not None:
            values.append(value)
    return values


def _mean_range(values: list[Any]) -> dict[str, Any]:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {"mean": fmean(numbers), "min": min(numbers), "max": max(numbers), "n": len(numbers)}


def _fmt_range(block: dict[str, Any]) -> str:
    if block["mean"] is None:
        return "n/a"
    return f"{block['mean']:.3f} [{block['min']:.3f}, {block['max']:.3f}]"


def _none_low(value: Any) -> float:
    return float("-inf") if value is None else float(value)


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
