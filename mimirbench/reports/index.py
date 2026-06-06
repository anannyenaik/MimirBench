"""Build a Markdown index over generated report artefacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["build_report_index"]

# Curated track classification for the saved real-model leaderboard rows, keyed by
# leaderboard run-directory name. Tracks follow BENCHMARK_PROTOCOL.md. This is the
# single source of truth for "is this row a clean comparison or a protocol/probe
# artefact?" and is emitted into INDEX.md so the distinction survives regeneration.
_ROW_CLASSIFICATION: dict[str, str] = {
    "leaderboard_openai_minis_all_envs_direct_20": "strict-track clean (gpt-4.1-mini, gpt-5.4-mini)",
    "leaderboard_openai_frontier_all_envs_direct_20": (
        "strict-track clean (gpt-5.4); protocol-limited (gpt-5.5)"
    ),
    "leaderboard_openai_gpt55_all_envs_direct_20": "protocol-limited (default temp, 512 budget)",
    "leaderboard_openai_gpt55_rescue_probe": "rescue probe (6 tasks, raised budget)",
    "leaderboard_claude_haiku_all_envs_direct_20": "strict-track clean",
    "leaderboard_claude_sonnet_all_envs_direct_20": "protocol-limited (max_tokens=512 truncation)",
    "leaderboard_claude_sonnet_all_envs_direct_20_maxtok1536": "best-valid clean (max_tokens=1536)",
    "leaderboard_claude_sonnet_rescue_probe_1024": "rescue probe (30 tasks, max_tokens=1024)",
    "leaderboard_claude_sonnet_robustness_tiny": "real-model robustness probe (best-valid row)",
    "leaderboard_gemini_flash_lite_all_envs_direct_20": "strict-track clean",
    "leaderboard_gemini_flash_lite_smoke": "smoke run (6 tasks)",
    "leaderboard_gemini_flash_all_envs_direct_20": "protocol-limited (default thinking, 512 budget)",
    "leaderboard_gemini_flash_all_envs_direct_20_thinking0": "best-valid clean (thinking_budget=0)",
    "leaderboard_gemini_flash_rescue_probe_thinking0": "rescue probe (6 tasks, thinking disabled)",
    "leaderboard_gemini_pro_all_envs_direct_20": "provider-failed diagnostic (14/120 503/504)",
    "leaderboard_gemini_pro_all_envs_direct_20_retry": "best-valid clean (cache-backed; provider-load caveat)",
    "leaderboard_gemini_pro_rescue_probe_low_thinking": "rescue probe (6 tasks, thinking_level=low)",
    "leaderboard_gemini_pro_smoke": "smoke run (request rejected, no model usage)",
    "leaderboard_gemini_pro_robustness_small": "real-model robustness probe (best-valid row)",
    "leaderboard_gemini_strongest_robustness_tiny": "real-model robustness probe (best-valid row)",
    "leaderboard_openai_gpt54_robustness_tiny": "real-model robustness probe (strict-track row)",
    "leaderboard_openai_gpt54mini_bayes_direct_tool_50": "diagnostic forced-tool run (direct vs tool)",
    "leaderboard_openai_gpt54mini_bayes_pred_direct_tool_25": "diagnostic forced-tool run (direct vs tool)",
    "leaderboard_openai_all_envs_direct_tiny": "smoke run (30 tasks)",
    "leaderboard_openai_modern_mini_all_envs_direct_tiny": "smoke run (30 tasks)",
    "leaderboard_openai_bayes_direct_20": "smoke run (single-environment)",
    "leaderboard_openai_bayes_direct_micro": "smoke run (5 tasks)",
    "leaderboard_all_available_tiny": "reference/mock/non-model status check (no model run)",
}


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

    lines.extend(["", "## Leaderboard runs", ""])
    leaderboard_runs = _leaderboard_runs(root)
    lines.extend(_leaderboard_lines(leaderboard_runs, root=root))

    lines.extend(["", "## Real-model row classification (tracks)", ""])
    lines.extend(_classification_lines(leaderboard_runs))

    lines.extend(["", "## Standalone leaderboard analysis notes", ""])
    leaderboard_notes = _leaderboard_notes(root)
    lines.extend([f"- {_link(note, root)}" for note in leaderboard_notes] or ["No standalone leaderboard notes found."])

    lines.extend(["", "## Interpretability runs", ""])
    interpretability_runs = _interpretability_runs(root)
    lines.extend(_interpretability_lines(interpretability_runs, root=root))

    lines.extend(["", "## Model cards", ""])
    cards = sorted((root / "model_cards").glob("*.md")) if (root / "model_cards").exists() else []
    cards = [card for card in cards if card.name.lower() != "readme.md"]
    lines.extend([f"- {_link(card, root)}" for card in cards] or ["No model cards found."])

    lines.extend(["", "## Generated figures", ""])
    figures = sorted(root.rglob("figures/*.png"))
    lines.extend([f"- {_link(figure, root)}" for figure in figures] or ["No generated figures found."])

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
    for summary_path in sorted(runs_root.rglob("robustness_summary.json")):
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


def _leaderboard_runs(root: Path) -> list[dict[str, Any]]:
    leaderboard_root = root / "runs" / "leaderboard"
    if not leaderboard_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for summary_path in sorted(leaderboard_root.glob("*/leaderboard_summary.json")):
        data = _read_json(summary_path)
        runs.append(
            {
                "name": data.get("leaderboard_name", summary_path.parent.name),
                "path": summary_path.parent,
                "models_run": len(data.get("models_run", [])),
                "models_pending": len(data.get("models_pending", [])),
                "tasks_per_agent": data.get("tasks_per_agent"),
                "headlines": len(data.get("headline_candidates", [])),
                "preliminary": data.get("preliminary"),
            }
        )
    return runs


def _classification_lines(runs: list[dict[str, Any]]) -> list[str]:
    """Emit the curated track classification for each saved leaderboard run."""
    if not runs:
        return ["No leaderboard runs to classify."]
    lines = [
        "Tracks follow [BENCHMARK_PROTOCOL.md](../BENCHMARK_PROTOCOL.md). Only "
        "`strict-track clean` and `best-valid clean` rows are headline comparisons; "
        "everything else is a documented protocol/probe/diagnostic artefact.",
        "",
        "| Leaderboard run | Track / classification |",
        "| --- | --- |",
    ]
    for run in runs:
        name = str(run["name"])
        classification = _ROW_CLASSIFICATION.get(
            name, "unclassified (treat as diagnostic until reviewed)"
        )
        lines.append(f"| `{name}` | {classification} |")
    return lines


def _leaderboard_notes(root: Path) -> list[Path]:
    leaderboard_root = root / "runs" / "leaderboard"
    if not leaderboard_root.exists():
        return []
    return sorted(leaderboard_root.glob("*.md"))


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


def _leaderboard_lines(runs: list[dict[str, Any]], *, root: Path) -> list[str]:
    if not runs:
        return ["No leaderboard runs found."]
    lines = [
        "| Name | Path | Models run | Pending | Tasks/agent | Headlines | Preliminary |",
        "| --- | --- | ---: | ---: | ---: | ---: | :---: |",
    ]
    for run in runs:
        lines.append(
            "| "
            f"{run['name']} | {_link(run['path'], root)} | "
            f"{_fmt(run.get('models_run'))} | {_fmt(run.get('models_pending'))} | "
            f"{_fmt(run.get('tasks_per_agent'))} | {_fmt(run.get('headlines'))} | "
            f"{'yes' if run.get('preliminary') else 'no'} |"
        )
    lines.append("")
    lines.append(
        "Leaderboard rows are real model results only when `models_run > 0` and the "
        "saved summary contains concrete per-agent run artefacts."
    )
    return lines


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
            f"{run['name']} | {_link(run['path'], root)} | {run['status']} | "
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
            f"{run['name']} | {_link(run['path'], root)} | "
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


def _link(path: Path, root: Path) -> str:
    """Clickable Markdown link (relative to ``reports/INDEX.md``) with code-styled text."""
    rel = _rel(path, root)
    return f"[`{rel}`]({rel})"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.6g}"
    return str(value)
