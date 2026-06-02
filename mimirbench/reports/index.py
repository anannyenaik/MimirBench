"""Build a Markdown index over generated report artefacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["build_report_index"]


def build_report_index(reports_dir: str | Path = "reports") -> Path:
    """Scan ``reports/`` and write ``reports/INDEX.md``."""
    root = Path(reports_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "INDEX.md"
    lines = [
        "# MimirBench report index",
        "",
        "Generated from saved artefacts. Reference, mock, and reference-tool runs are non-model diagnostics; real-model rows are only present when an actual run directory exists.",
        "",
        "## Baseline runs",
        "",
    ]
    baseline_runs = _baseline_runs(root)
    lines.extend(_run_lines(baseline_runs, root=root, empty="No baseline runs found."))

    lines.extend(["", "## Robustness runs", ""])
    robustness_runs = _robustness_runs(root)
    lines.extend(_run_lines(robustness_runs, root=root, empty="No robustness runs found."))

    lines.extend(["", "## Comparison runs", ""])
    comparison_runs = _comparison_runs(root)
    lines.extend(_run_lines(comparison_runs, root=root, empty="No comparison runs found."))

    lines.extend(["", "## Interpretability runs", ""])
    interpretability_runs = _interpretability_runs(root)
    lines.extend(_interpretability_lines(interpretability_runs, root=root))

    lines.extend(["", "## Model cards", ""])
    cards = sorted((root / "model_cards").glob("*.md")) if (root / "model_cards").exists() else []
    cards = [card for card in cards if card.name.lower() != "readme.md"]
    lines.extend([f"- `{_rel(card, root)}`" for card in cards] or ["No model cards found."])

    lines.extend(["", "## Generated figures", ""])
    figures = sorted(root.rglob("figures/*.png"))
    lines.extend([f"- `{_rel(figure, root)}`" for figure in figures] or ["No generated figures found."])

    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- All entries are backed by files under `reports/`.",
            "- Do not treat reference, mock, or deterministic tool baselines as real model results.",
            "- Do not describe any result as evidence of trading ability, trading usefulness, or profitability.",
            "- Real API/local model reports remain pending unless actual run artefacts exist.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _baseline_runs(root: Path) -> list[dict[str, Any]]:
    runs_root = root / "runs"
    if not runs_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(runs_root.glob("*/summary.json")):
        data = _read_json(summary_path)
        runs.append(
            {
                "name": data.get("run_name", summary_path.parent.name),
                "path": summary_path.parent,
                "label": _baseline_kind(data),
                "n_tasks": data.get("metrics", {}).get("overall", {}).get("n_tasks"),
                "mean_score": data.get("metrics", {}).get("overall", {}).get("mean_score"),
            }
        )
    return runs


def _robustness_runs(root: Path) -> list[dict[str, Any]]:
    runs_root = root / "runs"
    if not runs_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(runs_root.glob("*/robustness_summary.json")):
        data = _read_json(summary_path)
        runs.append(
            {
                "name": data.get("run_name", summary_path.parent.name),
                "path": summary_path.parent,
                "label": data.get("baseline_kind"),
                "n_tasks": data.get("counts", {}).get("n_base_tasks"),
                "mean_score": data.get("metrics", {}).get("mean_score_drop"),
            }
        )
    return runs


def _comparison_runs(root: Path) -> list[dict[str, Any]]:
    comparison_root = root / "runs" / "comparisons"
    if not comparison_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(comparison_root.glob("*/comparison_summary.json")):
        data = _read_json(summary_path)
        runs.append(
            {
                "name": data.get("comparison_name", summary_path.parent.name),
                "path": summary_path.parent,
                "label": data.get("baseline_kind"),
                "n_tasks": sum(env.get("num_tasks", 0) for env in data.get("environments", [])),
                "mean_score": None,
            }
        )
    return runs


def _interpretability_runs(root: Path) -> list[dict[str, Any]]:
    interp_root = root / "interpretability"
    if not interp_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(interp_root.glob("*/summary.json")):
        data = _read_json(summary_path)
        experiments = data.get("experiments", {})
        probes = experiments.get("probes", {}).get("headline", {})
        action = probes.get("action", {}) if isinstance(probes, dict) else {}
        runs.append(
            {
                "name": data.get("run_name", summary_path.parent.name),
                "path": summary_path.parent,
                "status": data.get("status", "unknown"),
                "experiments": ", ".join(data.get("experiments_run", [])) or "n/a",
                "action_probe": action.get("test_accuracy"),
            }
        )
    return runs


def _interpretability_lines(runs: list[dict[str, Any]], *, root: Path) -> list[str]:
    if not runs:
        return ["No interpretability runs found."]
    lines = [
        "| Name | Path | Status | Experiments | Action probe acc |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for run in runs:
        lines.append(
            "| "
            f"{run['name']} | `{_rel(run['path'], root)}` | {run['status']} | "
            f"{run['experiments']} | {_fmt(run.get('action_probe'))} |"
        )
    lines.append("")
    lines.append(
        "Interpretability runs analyse a small synthetic Bayesian transformer. "
        "Probe accuracy is decodability, not causation; no frontier-model claim is made."
    )
    return lines


def _run_lines(runs: list[dict[str, Any]], *, root: Path, empty: str) -> list[str]:
    if not runs:
        return [empty]
    lines = [
        "| Name | Path | Label | Tasks | Mean score / drop |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for run in runs:
        lines.append(
            "| "
            f"{run['name']} | `{_rel(run['path'], root)}` | "
            f"{run.get('label') or 'n/a'} | {_fmt(run.get('n_tasks'))} | "
            f"{_fmt(run.get('mean_score'))} |"
        )
    return lines


def _baseline_kind(summary: dict[str, Any]) -> str:
    value = summary.get("baseline_kind")
    if isinstance(value, str):
        return value
    agent_type = str(summary.get("agent", {}).get("type") or "").lower()
    if agent_type == "reference":
        return "reference sanity check"
    if agent_type == "mock":
        return "mock diagnostic baseline"
    if agent_type == "tool":
        config = summary.get("agent", {}).get("config", {})
        if isinstance(config, dict) and str(config.get("tool_policy", "reference")).lower() == "reference":
            return "deterministic non-model tool baseline"
    if agent_type == "local":
        return "real local model"
    if agent_type in {"api", "direct", "reflective", "tool"}:
        return "real API model"
    return agent_type or "unknown"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.6g}"
    return str(value)
