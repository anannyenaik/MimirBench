"""Generate research figures from the selected results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ROOT / "experiments" / "selected_results"

BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
GREY = "#6B7280"
INK = "#111827"
GRID = "#D1D5DB"

ENVIRONMENTS = (
    "bayesian_games",
    "auctions",
    "hidden_regimes",
    "market_making",
    "prediction_markets",
    "adversarial_risk",
)
ENVIRONMENT_LABELS = (
    "Bayesian\nupdating",
    "Auctions",
    "Hidden\nregimes",
    "Market\nmaking",
    "Prediction\nmarkets",
    "Adversarial\nrisk",
)
HEAD_SITES = tuple(
    f"blocks.{layer}.attn_heads.{head}.out" for layer in range(2) for head in range(4)
)
HEAD_LABELS = tuple(f"L{layer} H{head}" for layer in range(2) for head in range(4))

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "lines.linewidth": 1.3,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def ordered_models(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Order models by protocol, then decreasing mean score."""
    return sorted(
        summary["models"],
        key=lambda model: (
            0 if model["track"] == "strict-512" else 1,
            -float(model["mean_score"]["mean"]),
        ),
    )


def environment_score_matrix(
    summary: dict[str, Any],
) -> tuple[list[str], npt.NDArray[np.float64]]:
    """Return model labels and their six environment-level mean scores."""
    models = ordered_models(summary)
    values = np.asarray(
        [
            [
                float(model["environment_metrics"][environment]["mean_score"])
                for environment in ENVIRONMENTS
            ]
            for model in models
        ],
        dtype=np.float64,
    )
    return [str(model["display"]) for model in models], values


def head_metric_matrix(
    summary: dict[str, Any], group: str, metric: str
) -> tuple[list[int], npt.NDArray[np.float64]]:
    """Return a seed-by-head matrix from retained intervention records."""
    records = summary["per_seed"]
    values = np.asarray(
        [
            [float(record[group][site][metric]) for site in HEAD_SITES]
            for record in records
        ],
        dtype=np.float64,
    )
    return [int(record["seed"]) for record in records], values


def save_figure(figure: plt.Figure, output_dir: Path, stem: str) -> list[Path]:
    """Save one figure in GitHub and vector-paper formats."""
    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{stem}.png"
    pdf = output_dir / f"{stem}.pdf"
    figure.savefig(png, dpi=180, bbox_inches="tight", metadata={"Software": "MimirBench"})
    figure.savefig(
        pdf,
        bbox_inches="tight",
        metadata={"Creator": "MimirBench", "CreationDate": None, "ModDate": None},
    )
    plt.close(figure)
    return [png, pdf]


def benchmark_scores(summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Plot aggregate model scores and task-bootstrap intervals."""
    models = ordered_models(summary)
    labels = [model["display"] for model in models]
    means = np.asarray([model["mean_score"]["mean"] for model in models])
    lower = means - np.asarray([model["mean_score"]["low"] for model in models])
    upper = np.asarray([model["mean_score"]["high"] for model in models]) - means
    colours = [BLUE if model["track"] == "strict-512" else ORANGE for model in models]

    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    positions = np.arange(len(models))[::-1]
    for position, mean, low, high, colour in zip(
        positions, means, lower, upper, colours, strict=True
    ):
        axis.errorbar(
            mean,
            position,
            xerr=np.asarray([[low], [high]]),
            fmt="o",
            color=colour,
            capsize=3,
            markersize=5,
        )
    axis.axhline(2.5, color=GRID, linewidth=0.8)
    axis.set_yticks(positions, labels)
    axis.set_xlabel("Mean benchmark score with 95% task-bootstrap CI")
    axis.set_xlim(0.35, 0.95)
    axis.grid(axis="x", color=GRID, linewidth=0.7)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    axis.scatter([], [], color=BLUE, label="Strict-512")
    axis.scatter([], [], color=ORANGE, label="Best-valid")
    axis.legend(frameon=False, loc="lower left")
    figure.tight_layout()
    return save_figure(figure, output_dir, "benchmark_scores")


def benchmark_profiles(summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Plot model performance across the six strategic environments."""
    labels, values = environment_score_matrix(summary)
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    image = axis.imshow(values, cmap="cividis", vmin=0.0, vmax=1.0, aspect="auto")
    axis.set_xticks(range(len(ENVIRONMENT_LABELS)), ENVIRONMENT_LABELS)
    axis.set_yticks(range(len(labels)), labels)
    axis.axhline(4.5, color="white", linewidth=1.2)
    track_axis = axis.secondary_yaxis("right")
    track_axis.set_yticks((2.0, 6.0), ("Strict-512", "Best-valid"))
    track_axis.tick_params(length=0, pad=6, colors=GREY)
    track_axis.spines["right"].set_visible(False)
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = values[row, column]
            colour = "white" if value < 0.32 or value > 0.78 else INK
            axis.text(column, row, f"{value:.2f}", ha="center", va="center", color=colour)
    colour_bar = figure.colorbar(image, ax=axis, pad=0.12)
    colour_bar.set_label("Mean score")
    axis.tick_params(length=0)
    figure.tight_layout()
    return save_figure(figure, output_dir, "benchmark_profiles")


def interpretability_recovery(summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Plot seed observations, means and ranges for three intervention sites."""
    sites = (
        ("Layer 0\nattention", "blocks.0.attn_out", BLUE),
        ("Layer 0\nMLP", "blocks.0.mlp_out", ORANGE),
        ("Layer 1\nattention", "blocks.1.attn_out", GREEN),
    )
    offsets = np.linspace(-0.13, 0.13, len(summary["seeds"]))
    figure, axis = plt.subplots(figsize=(6.4, 4.0))
    for position, (_label, site, colour) in enumerate(sites):
        values = np.asarray(
            [seed["metrics"]["whole_site_action_recovery"][site] for seed in summary["seeds"]]
        )
        axis.vlines(position, values.min(), values.max(), color=GREY, linewidth=1.3, zorder=1)
        axis.scatter(
            position + offsets,
            values,
            color=colour,
            edgecolor="white",
            linewidth=0.5,
            s=30,
            zorder=2,
        )
        axis.scatter(
            position,
            values.mean(),
            marker="D",
            color=INK,
            edgecolor="white",
            linewidth=0.5,
            s=35,
            zorder=3,
        )
    axis.set_xticks(range(len(sites)), [site[0] for site in sites])
    axis.set_ylabel("Clean-action recovery")
    axis.set_ylim(-0.04, 1.04)
    axis.grid(axis="y", color=GRID, linewidth=0.7)
    axis.spines[["top", "right"]].set_visible(False)
    axis.scatter([], [], color=GREY, s=30, label="Seed")
    axis.scatter([], [], marker="D", color=INK, s=35, label="Mean")
    axis.legend(frameon=False, loc="center", ncols=2, bbox_to_anchor=(0.5, 1.04))
    figure.tight_layout()
    return save_figure(figure, output_dir, "interpretability_recovery")


def head_mechanisms(summary: dict[str, Any], output_dir: Path) -> list[Path]:
    """Plot per-seed head patching and ablation results."""
    seeds, patching = head_metric_matrix(
        summary, "per_head_patching", "matched_action_recovery"
    )
    ablation_seeds, ablation = head_metric_matrix(
        summary, "per_head_ablation", "posterior_bucket_accuracy_degradation"
    )
    if ablation_seeds != seeds:
        raise ValueError("head patching and ablation seed orders differ")

    figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.1), sharey=True)
    panels = (
        (patching, "a  Matched action recovery", "Recovery rate"),
        (ablation, "b  Posterior accuracy degradation", "Accuracy degradation"),
    )
    for axis, (values, title, colour_label) in zip(axes, panels, strict=True):
        image = axis.imshow(values, cmap="cividis", vmin=0.0, vmax=0.75, aspect="auto")
        axis.set_title(title, loc="left")
        axis.set_xticks(range(len(HEAD_LABELS)), HEAD_LABELS, rotation=45, ha="right")
        axis.set_yticks(range(len(seeds)), seeds)
        axis.set_xlabel("Attention head")
        axis.tick_params(length=0)
        for row in range(values.shape[0]):
            for column in range(values.shape[1]):
                value = values[row, column]
                colour = "white" if value < 0.15 or value > 0.58 else INK
                axis.text(column, row, f"{value:.2f}", ha="center", va="center", color=colour)
        colour_bar = figure.colorbar(image, ax=axis, pad=0.025, shrink=0.9)
        colour_bar.set_label(colour_label)
    axes[0].set_ylabel("Training seed")
    axes[0].axvline(3.5, color="white", linewidth=1.1)
    axes[1].axvline(3.5, color="white", linewidth=1.1)
    figure.tight_layout()
    return save_figure(figure, output_dir, "head_mechanisms")


def generate_all(output_dir: Path) -> list[Path]:
    """Generate all figures from the committed selected-result files."""
    benchmark = load_json(SELECTED / "benchmark" / "summary.json")
    interpretability = load_json(SELECTED / "interpretability" / "six_seed_summary.json")
    heads = load_json(SELECTED / "interpretability" / "head_position_summary.json")

    generated: list[Path] = []
    generated.extend(benchmark_scores(benchmark, output_dir))
    generated.extend(benchmark_profiles(benchmark, output_dir))
    generated.extend(interpretability_recovery(interpretability, output_dir))
    generated.extend(head_mechanisms(heads, output_dir))
    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    destinations = parser.add_mutually_exclusive_group()
    destinations.add_argument(
        "--output-dir",
        type=Path,
        help="Write figures to this directory instead of build/figures/.",
    )
    destinations.add_argument(
        "--publication",
        action="store_true",
        help="Regenerate the tracked publication figures under figures/.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir or ROOT / ("figures" if args.publication else "build/figures")
    generated = generate_all(output_dir)
    for path in generated:
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


if __name__ == "__main__":
    main()
