"""MimirBench command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from mimirbench import __version__
from mimirbench.evals import list_specs, run_eval
from mimirbench.evals.comparison_runner import (
    ComparisonConfig,
    load_comparison_config,
    run_comparison_config,
    validate_comparison_config,
)
from mimirbench.evals.comparison_runner import (
    summarise_comparison as read_comparison_summary,
)
from mimirbench.evals.robustness_runner import (
    load_robustness_config,
    run_robustness_config,
    validate_robustness_config,
)
from mimirbench.evals.runner import load_eval_config, run_eval_config, validate_eval_config
from mimirbench.evals.schemas import (
    EnvironmentRunConfig,
    EvalConfig,
    EvalRunConfig,
    ReportingConfig,
)
from mimirbench.evals.variants import (
    ANSWER_PRESERVING_BY_TYPE,
    ENVIRONMENT_VARIANT_TYPES,
    VariantType,
    variant_type_values,
)

app = typer.Typer(add_completion=False, help="MimirBench: strategic-reasoning evals for LM agents.")
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mimirbench {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """MimirBench CLI."""


@app.command("list-envs")
def list_envs() -> None:
    """List the environments registered with the eval runner."""
    table = Table(title="Registered environments")
    table.add_column("name", style="bold cyan")
    table.add_column("family")
    table.add_column("description")
    for spec in list_specs():
        table.add_row(spec.name, spec.family.value, spec.description)
    console.print(table)


@app.command("validate-config")
def validate_config(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to an eval YAML."),
) -> None:
    """Validate an evaluation config file against the schema and registry."""
    try:
        config = load_eval_config(config_path)
        validate_eval_config(config)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    kind = "run config" if isinstance(config, EvalRunConfig) else "legacy eval config"
    console.print(f"[green]OK[/green] - {kind} is valid: {config_path}")


@app.command("run-eval")
def run_eval_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to an eval YAML."),
    n_tasks: int | None = typer.Option(None, help="Override the number of tasks."),
    seed: int | None = typer.Option(None, help="Override the base seed."),
) -> None:
    """Run an evaluation config."""
    try:
        config = load_eval_config(config_path)
        config = _apply_overrides(config, n_tasks=n_tasks, seed=seed)
        validate_eval_config(config)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    if isinstance(config, EvalConfig):
        report = run_eval(config)
        _print_legacy_report(report.environment, report.agent, report.model_dump())
        return

    summary = run_eval_config(config)
    _print_summary(summary)


@app.command("summarise-run")
def summarise_run(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Print a concise summary for an existing run directory."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]No summary.json found:[/red] {summary_path}")
        raise typer.Exit(code=1)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _print_summary(summary)


@app.command("check-provider")
def check_provider(
    provider: str = typer.Argument(..., help="One of: openai, anthropic, gemini, local, generic_http."),
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        help="Base URL for generic_http/OpenAI-compatible endpoints.",
    ),
    api_key_env: str | None = typer.Option(
        None,
        "--api-key-env",
        help="Environment-variable name to check for API providers; the value is never printed.",
    ),
) -> None:
    """Check whether a model provider's package and key appear usable.

    Confirms package availability and (for API providers) whether the key
    environment variable is set. The key value itself is never printed.
    """
    from mimirbench.agents.providers import provider_status

    name = provider.lower().strip()
    if name not in {"openai", "anthropic", "gemini", "local", "generic_http"}:
        console.print(f"[red]Unknown provider:[/red] {provider}")
        console.print("Expected one of: openai, anthropic, gemini, local, generic_http.")
        raise typer.Exit(code=2)
    status = provider_status(name, base_url=base_url, api_key_env=api_key_env)

    table = Table(title=f"Provider check: {status.provider}")
    table.add_column("field", style="bold cyan")
    table.add_column("value")
    table.add_row("package_available", _yesno(status.package_available))
    table.add_row("key_required", _yesno(status.key_required))
    table.add_row(
        "key_present",
        _yesno(status.key_present) + (f" (env: {status.key_env})" if status.key_env else ""),
    )
    table.add_row("usable", _yesno(status.usable))
    table.add_row("detail", escape(status.detail))
    console.print(table)
    if status.usable:
        console.print("[green]Provider appears usable.[/green]")
    else:
        console.print("[yellow]Provider is not usable yet (see detail above).[/yellow]")


@app.command("estimate-run-cost")
def estimate_run_cost(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to an eval YAML."),
) -> None:
    """Roughly estimate task/token volume (and cost only if pricing is configured).

    This is a pre-run estimate using prompt character length (~4 chars/token); it
    is deliberately approximate and never claims an exact cost.
    """
    try:
        config = load_eval_config(config_path)
        validate_eval_config(config)
        estimate = _estimate_cost(config)
        _print_cost_estimate(estimate)
        return
    except (KeyError, ValueError, ValidationError) as eval_exc:
        try:
            comparison = load_comparison_config(config_path)
            validate_comparison_config(comparison)
        except (KeyError, ValueError, ValidationError) as comparison_exc:
            try:
                from mimirbench.evals.leaderboard import (
                    load_leaderboard_config,
                    validate_leaderboard_config,
                )

                leaderboard_config = load_leaderboard_config(config_path)
                validate_leaderboard_config(leaderboard_config)
            except (KeyError, ValueError, ValidationError) as leaderboard_exc:
                try:
                    robustness = load_robustness_config(config_path)
                    validate_robustness_config(robustness)
                except (KeyError, ValueError, ValidationError) as robustness_exc:
                    console.print(f"[red]Invalid config:[/red] {config_path}")
                    console.print(str(eval_exc))
                    console.print(str(comparison_exc))
                    console.print(str(leaderboard_exc))
                    console.print(str(robustness_exc))
                    raise typer.Exit(code=1) from robustness_exc
                _print_cost_estimate(_estimate_robustness_cost(robustness))
                return
            _print_leaderboard_cost_estimate(_estimate_leaderboard_cost(leaderboard_config))
            return
    _print_comparison_cost_estimate(_estimate_comparison_cost(comparison))


@app.command("inspect-failures")
def inspect_failures(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    limit: int = typer.Option(15, help="Maximum number of failures to show."),
) -> None:
    """List failing tasks (low score, violations, or errors) for a run directory."""
    from mimirbench.evals.writers import load_records_jsonl

    results_path = run_dir / "results.jsonl"
    if not results_path.exists():
        console.print(f"[red]No results.jsonl found:[/red] {results_path}")
        raise typer.Exit(code=1)
    records = load_records_jsonl(results_path)
    failures = [r for r in records if not r.grader_result.passed or r.error is not None]
    console.print(
        f"[bold]{run_dir.name}[/bold]: {len(failures)} / {len(records)} tasks failed or errored."
    )
    table = Table(title="Failures")
    table.add_column("task", style="bold cyan")
    table.add_column("env")
    table.add_column("score", justify="right")
    table.add_column("violations")
    table.add_column("error")
    for record in failures[:limit]:
        table.add_row(
            record.task_id,
            record.environment,
            f"{record.grader_result.score:.3f}",
            ", ".join(record.grader_result.violations) or "-",
            (record.error or "-")[:50],
        )
    console.print(table)


@app.command("inspect-tool-audit")
def inspect_tool_audit(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    limit: int = typer.Option(20, help="Maximum number of tool steps to show."),
) -> None:
    """Print tool-use audit metrics and a sample of tool steps for a run."""
    audit_path = run_dir / "tool_audit.jsonl"
    summary_path = run_dir / "summary.json"
    if not audit_path.exists():
        console.print(f"[yellow]No tool_audit.jsonl found in[/yellow] {run_dir} "
                      "(this run did not use a tool agent).")
        raise typer.Exit(code=0)

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        metrics = summary.get("tool_audit")
        if metrics:
            console.print("[bold]Tool-use metrics[/bold]")
            for key in (
                "tool_call_rate",
                "invalid_tool_call_rate",
                "tool_error_rate",
                "mean_tool_steps",
                "final_answer_after_tool_rate",
                "tool_result_ignored_rate",
            ):
                console.print(f"  {key}: {_fmt(metrics.get(key))}")

    table = Table(title="Tool steps")
    table.add_column("task", style="bold cyan")
    table.add_column("step", justify="right")
    table.add_column("tool")
    table.add_column("status")
    table.add_column("used_result")
    shown = 0
    with audit_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            used = row.get("final_answer_used_tool_result")
            table.add_row(
                str(row.get("task_id")),
                str(row.get("step_number")),
                str(row.get("requested_tool")),
                str(row.get("validation_status")),
                "unknown" if used is None else ("yes" if used else "no"),
            )
            shown += 1
            if shown >= limit:
                break
    console.print(table)


@app.command("list-variant-types")
def list_variant_types() -> None:
    """List all robustness variant types and which environments use them."""
    table = Table(title="Robustness variant types")
    table.add_column("variant type", style="bold cyan")
    table.add_column("answer preserving", justify="center")
    table.add_column("environments")
    env_by_type: dict[str, list[str]] = {value: [] for value in variant_type_values()}
    for env, types in ENVIRONMENT_VARIANT_TYPES.items():
        for vtype in types:
            env_by_type[vtype.value].append(env)
    for value in variant_type_values():
        vtype = VariantType(value)
        preserving = ANSWER_PRESERVING_BY_TYPE[vtype]
        envs = env_by_type.get(value, [])
        table.add_row(
            value,
            "yes" if preserving else "no",
            ", ".join(sorted(envs)) if envs else "(none)",
        )
    console.print(table)


@app.command("run-robustness")
def run_robustness_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a robustness YAML."),
    n_tasks: int | None = typer.Option(None, help="Override the number of base tasks per environment."),
    seed: int | None = typer.Option(None, help="Override the base seed."),
) -> None:
    """Run a robustness evaluation config."""
    try:
        config = load_robustness_config(config_path)
        if n_tasks is not None:
            environments = [env.model_copy(update={"num_tasks": n_tasks}) for env in config.environments]
            config = config.model_copy(update={"environments": environments})
        if seed is not None:
            config = config.model_copy(update={"run": config.run.model_copy(update={"seed": seed})})
        validate_robustness_config(config)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid robustness config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    summary = run_robustness_config(config)
    _print_robustness_summary(summary)


@app.command("summarise-robustness")
def summarise_robustness(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Print a concise summary for an existing robustness run directory."""
    summary_path = run_dir / "robustness_summary.json"
    if not summary_path.exists():
        console.print(f"[red]No robustness_summary.json found:[/red] {summary_path}")
        raise typer.Exit(code=1)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _print_robustness_summary(summary)


@app.command("run-comparison")
def run_comparison_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a comparison YAML."),
) -> None:
    """Run a paired comparison config."""
    try:
        config = load_comparison_config(config_path)
        validate_comparison_config(config)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid comparison config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    summary = run_comparison_config(config)
    _print_comparison_summary(summary)


@app.command("summarise-comparison")
def summarise_comparison(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Print a concise summary for an existing comparison directory."""
    try:
        summary = read_comparison_summary(run_dir)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    _print_comparison_summary(summary)


@app.command("run-leaderboard")
def run_leaderboard_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a leaderboard YAML."),
    allow_unavailable: bool = typer.Option(
        False,
        "--allow-unavailable",
        help="Allow unavailable non-model diagnostics such as reference/mock smoke runs.",
    ),
    allow_real_models: bool = typer.Option(
        False,
        "--allow-real-models",
        help="Permit actual API/local model calls after provider checks pass.",
    ),
) -> None:
    """Run a paired real-model leaderboard config.

    Real API/local models require both a usable provider check and
    ``--allow-real-models``. If no model is runnable, the run still writes a
    summary/report marking every model as pending.
    """
    from mimirbench.evals.leaderboard import (
        load_leaderboard_config,
        run_leaderboard_config,
        validate_leaderboard_config,
    )

    try:
        config = load_leaderboard_config(config_path)
        validate_leaderboard_config(config)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid leaderboard config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    summary = run_leaderboard_config(
        config,
        allow_unavailable=allow_unavailable,
        allow_real_models=allow_real_models,
    )
    _print_leaderboard_summary(summary)


@app.command("summarise-leaderboard")
def summarise_leaderboard_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Print a concise summary for an existing leaderboard run directory."""
    from mimirbench.evals.leaderboard import summarise_leaderboard

    try:
        summary = summarise_leaderboard(run_dir)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    _print_leaderboard_summary(summary)


@app.command("make-plots")
def make_plots(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Generate supported Matplotlib figures for a run or comparison directory."""
    from mimirbench.analysis.plots import generate_comparison_plots, generate_run_plots

    if (run_dir / "comparison_summary.json").exists():
        paths = generate_comparison_plots(run_dir)
    else:
        paths = generate_run_plots(run_dir)
    if not paths:
        console.print(f"[yellow]No plots generated for[/yellow] {run_dir}")
        return
    console.print(f"[green]Generated {len(paths)} figure(s):[/green]")
    for path in paths:
        console.print(f"  {path}")


@app.command("make-model-card")
def make_model_card(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    output_dir: Path = typer.Option(Path("reports") / "model_cards", help="Where to write the card."),
) -> None:
    """Generate a model/agent card from actual run artefacts."""
    from mimirbench.reports.model_cards import generate_model_card

    path = generate_model_card(run_dir, output_dir=output_dir)
    if path is None:
        console.print(
            f"[red]No model card generated:[/red] {run_dir} does not contain "
            "both summary.json and non-empty results.jsonl."
        )
        raise typer.Exit(code=1)
    console.print(f"[green]Model card written:[/green] {path}")


@app.command("generate-traces")
def generate_traces_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to training YAML."),
) -> None:
    """Generate synthetic Bayesian trace JSONL files from a training config."""
    from mimirbench.training.train_small_transformer import generate_traces_from_config

    try:
        paths = generate_traces_from_config(config_path)
    except Exception as exc:
        console.print(f"[red]Trace generation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print("[green]Trace files written:[/green]")
    for split, path in sorted(paths.items()):
        console.print(f"  {split}: {path}")


@app.command("train-small-transformer")
def train_small_transformer_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to training YAML."),
    model_card_dir: Path = typer.Option(
        Path("reports") / "model_cards", help="Where to write the generated model card."
    ),
) -> None:
    """Train the compact transformer on synthetic Bayesian traces."""
    from mimirbench.training.train_small_transformer import train

    try:
        summary = train(config_path, model_card_dir=model_card_dir)
    except Exception as exc:
        console.print(f"[red]Training failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    _print_training_summary(summary)


@app.command("eval-small-transformer")
def eval_small_transformer_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to eval YAML."),
    model_card_dir: Path = typer.Option(
        Path("reports") / "model_cards", help="Where to write the generated model card."
    ),
) -> None:
    """Evaluate a trained small-transformer checkpoint on held-out Bayesian traces."""
    from mimirbench.training.evaluate_small_transformer import evaluate_checkpoint

    try:
        summary = evaluate_checkpoint(config_path, model_card_dir=model_card_dir)
    except Exception as exc:
        console.print(f"[red]Evaluation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    metrics = summary["metrics"]
    console.print(
        f"[bold]{summary['run_name']}[/bold] | "
        f"posterior_bucket_acc={_fmt(metrics.get('posterior_bucket_accuracy'))} "
        f"action_acc={_fmt(metrics.get('action_accuracy'))} "
        f"risk_acc={_fmt(metrics.get('risk_flag_accuracy'))}"
    )
    console.print(f"artefacts: {summary['output_dir']}")


@app.command("inspect-training")
def inspect_training_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Summarise a small-transformer training run directory."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]No summary.json found:[/red] {summary_path}")
        raise typer.Exit(code=1)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _print_training_summary(summary)


@app.command("run-interpretability")
def run_interpretability_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to an interpretability YAML."),
) -> None:
    """Run the interpretability experiments (probes, patching, attention)."""
    from mimirbench.interpretability.runner import (
        load_interpretability_config,
        run_interpretability,
    )

    try:
        config = load_interpretability_config(config_path)
    except (KeyError, ValueError) as exc:
        console.print(f"[red]Invalid interpretability config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    summary = run_interpretability(config)
    if summary.get("status") == "pending":
        console.print(
            f"[yellow]Experiments pending for[/yellow] {summary['run_name']} "
            "(infrastructure ran, but prerequisites are missing):"
        )
        for blocker in summary.get("blockers", []):
            console.print(f"  - {blocker}")
        console.print(f"report: {summary['output_dir']}/INTERPRETABILITY_REPORT.md")
        return
    _print_interpretability_summary(summary)


@app.command("run-extended-interpretability")
def run_extended_interpretability_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to interp YAML."),
) -> None:
    """Run position-resolved patching and negative controls (local-only, no API calls)."""
    from mimirbench.interpretability.extended_interpretability import run_extended_interpretability

    summary = run_extended_interpretability(config_path)
    if summary.get("status") == "pending":
        console.print(f"[yellow]{summary.get('run_name')}: extended experiments pending[/yellow]")
        for blocker in summary.get("blockers", []):
            console.print(f"  - {blocker}")
        return
    console.print(f"[green]Extended interpretability complete:[/green] {summary['output_dir']}")
    shuffle = summary.get("label_shuffle_control", {})
    console.print(
        "label-shuffle control: "
        f"real={_fmt(shuffle.get('real_test_accuracy'))} "
        f"shuffled={_fmt(shuffle.get('shuffled_test_accuracy'))} "
        f"baseline={_fmt(shuffle.get('majority_baseline_accuracy'))}"
    )


@app.command("run-multiseed-interpretability")
def run_multiseed_interpretability_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a multiseed YAML."),
) -> None:
    """Replicate medium-model interpretability across seeds (local-only, no API calls).

    Trains any missing per-seed checkpoints, runs whole-site and extended
    interpretability per seed, evaluates held-out metrics, and writes an explicit
    mean/range aggregate. Per-seed failures are fail-soft.
    """
    from mimirbench.interpretability.multiseed import (
        load_multiseed_config,
        run_multiseed_interpretability,
    )

    try:
        config = load_multiseed_config(config_path)
    except (KeyError, ValueError) as exc:
        console.print(f"[red]Invalid multiseed config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    summary = run_multiseed_interpretability(config)
    _print_multiseed_summary(summary)


@app.command("run-head-token-interpretability")
def run_head_token_interpretability_command(
    config_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a multiseed YAML."),
) -> None:
    """Run local per-head and individual-token causal analysis across saved checkpoints."""
    from mimirbench.interpretability.head_token_analysis import run_head_token_multiseed

    summary = run_head_token_multiseed(config_path)
    console.print(
        f"[green]Head/token interpretability complete:[/green] "
        f"{summary['n_completed']}/{summary['n_attempted']} seeds"
    )
    console.print(summary["interpretation"])


@app.command("inspect-interpretability")
def inspect_interpretability_command(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
) -> None:
    """Summarise an interpretability run directory."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        console.print(f"[red]No summary.json found:[/red] {summary_path}")
        raise typer.Exit(code=1)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _print_interpretability_summary(summary, inspect=True)


@app.command("build-report-index")
def build_report_index_command(
    reports_dir: Path = typer.Option(Path("reports"), help="Reports directory to scan."),
) -> None:
    """Build reports/INDEX.md from saved artefacts."""
    from mimirbench.reports.index import build_report_index

    path = build_report_index(reports_dir)
    console.print(f"[green]Report index written:[/green] {path}")


@app.command("statistical-validity")
def statistical_validity_command(
    base_dir: Path = typer.Option(
        Path("reports") / "runs" / "leaderboard",
        help="Leaderboard run directory holding saved real-model artefacts.",
    ),
    output_path: Path | None = typer.Option(
        None, help="Destination markdown file (defaults inside base-dir)."
    ),
) -> None:
    """Compute bootstrap CIs and paired deltas over saved artefacts only (no model runs)."""
    from mimirbench.analysis.statistical_validity import write_statistical_validity_report

    path = write_statistical_validity_report(base_dir, output_path=output_path)
    console.print(f"[green]Statistical validity report written:[/green] {path}")
    console.print(
        "[dim]Pilot CIs over the saved synthetic sample, not population-level "
        "benchmark claims. No model was run.[/dim]"
    )


@app.command("plan-full-benchmark")
def plan_full_benchmark_command(
    config_path: Path = typer.Argument(
        ..., exists=True, readable=True, help="Path to a full hosted-model leaderboard YAML."
    ),
    output_dir: Path = typer.Option(
        Path("reports") / "plans", help="Directory for the no-execute plan manifest."
    ),
) -> None:
    """Plan and cost a full hosted benchmark without checking or calling providers."""
    from mimirbench.analysis.full_benchmark_planning import (
        build_full_benchmark_plan,
        write_full_benchmark_plan,
    )

    try:
        plan = build_full_benchmark_plan(config_path)
        path = write_full_benchmark_plan(config_path, output_dir=output_dir)
    except (KeyError, ValueError, ValidationError) as exc:
        console.print(f"[red]Invalid full benchmark config:[/red] {config_path}")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    counts = plan["counts"]
    tokens = plan["token_estimate"]
    console.print(
        f"[bold]{plan['leaderboard_name']}[/bold] | track=[cyan]{plan['protocol']['track']}[/cyan] | "
        f"models={counts['models']} environments={counts['environments']} seeds={counts['seeds']}"
    )
    console.print(
        f"tasks/model={counts['tasks_per_model']:,} | "
        f"scheduled calls={counts['scheduled_model_calls']:,} | "
        f"retry-attempt upper={counts['retry_attempt_upper']:,}"
    )
    console.print(
        f"estimated total tokens={tokens['total_tokens_range'][0]:,}-"
        f"{tokens['total_tokens_range'][1]:,} | "
        f"cost={plan['cost_estimate_usd']['formatted']}"
    )
    model_table = Table(title="Planned hosted models")
    model_table.add_column("model", style="bold cyan")
    model_table.add_column("provider")
    model_table.add_column("calls", justify="right")
    model_table.add_column("cost range", justify="right")
    for model in plan["models"]:
        model_table.add_row(
            str(model["label"]),
            str(model["provider"]),
            f"{int(model['scheduled_calls']):,}",
            str(model["cost_range_formatted"]),
        )
    console.print(model_table)
    environment_table = Table(title="Environment/seed cells")
    environment_table.add_column("environment", style="bold cyan")
    environment_table.add_column("seed", justify="right")
    environment_table.add_column("tasks", justify="right")
    for environment in plan["environments"]:
        environment_table.add_row(
            str(environment["environment"]),
            str(environment["seed"]),
            f"{int(environment['tasks']):,}",
        )
    console.print(environment_table)
    console.print(f"[green]No-execute manifest written:[/green] {path}")
    console.print(f"Exact run command: {plan['exact_run_command']}")
    console.print("[dim]No provider was checked or called; no credential value was read.[/dim]")


@app.command("power-plan-full-benchmark")
def power_plan_full_benchmark_command(
    base_dir: Path = typer.Option(
        Path("reports") / "runs" / "leaderboard",
        help="Leaderboard directory holding saved pilot artefacts.",
    ),
    output_path: Path = typer.Option(
        Path("reports") / "runs" / "leaderboard" / "full_benchmark_power_plan.md",
        help="Destination planning report.",
    ),
) -> None:
    """Estimate full-track CI widths from saved pilot artefacts only."""
    from mimirbench.analysis.power_planning import write_power_planning_report

    path = write_power_planning_report(base_dir, output_path=output_path)
    console.print(f"[green]Full benchmark power plan written:[/green] {path}")
    console.print("[dim]Planning estimates only; no model was run.[/dim]")


def _print_interpretability_summary(summary: dict[str, Any], *, inspect: bool = False) -> None:
    if summary.get("status") == "pending":
        console.print(
            f"[yellow]{summary.get('run_name')}: experiments pending[/yellow]"
        )
        for blocker in summary.get("blockers", []):
            console.print(f"  - {blocker}")
        return
    model = summary.get("model", {})
    data = summary.get("data", {})
    console.print(
        f"[bold]{summary.get('run_name')}[/bold] | "
        f"checkpoint=[cyan]{summary.get('checkpoint_path')}[/cyan] | "
        f"model={model.get('n_layers')}L d_model={model.get('d_model')} heads={model.get('n_heads')}"
    )
    console.print(
        f"data: {data.get('num_examples')} traces/split, {data.get('num_pairs')} pairs "
        f"(seed {data.get('seed')}) | experiments: {', '.join(summary.get('experiments_run', [])) or 'none'}"
    )
    experiments = summary.get("experiments", {})

    probes = experiments.get("probes")
    if probes:
        table = Table(title="Linear probes (best site)")
        table.add_column("label", style="bold cyan")
        table.add_column("best site")
        table.add_column("test acc", justify="right")
        table.add_column("baseline", justify="right")
        table.add_column("above", justify="right")
        for label, row in probes.get("headline", {}).items():
            table.add_row(
                label,
                str(row.get("site")),
                _fmt(row.get("test_accuracy")),
                _fmt(row.get("majority_baseline_accuracy")),
                _fmt(row.get("test_accuracy_above_baseline")),
            )
        console.print(table)

    patching = experiments.get("patching") or experiments.get("activation_patching")
    if patching:
        table = Table(title="Activation patching (per site)")
        table.add_column("site", style="bold cyan")
        table.add_column("action causal effect", justify="right")
        table.add_column("action recovery", justify="right")
        table.add_column("label recovery", justify="right")
        for site, block in patching.get("by_site", {}).items():
            action = block.get("heads", {}).get("action", {})
            table.add_row(
                site,
                _fmt(action.get("mean_causal_effect")),
                _fmt(block.get("action_recovery_rate")),
                _fmt(block.get("label_recovery_rate")),
            )
        console.print(table)
        console.print(f"best action-recovery site: {patching.get('best_action_recovery_site') or 'n/a'}")

    attention = experiments.get("attention_analysis")
    if attention:
        table = Table(title="Attention (per layer)")
        table.add_column("layer", style="bold cyan")
        table.add_column("mean entropy", justify="right")
        table.add_column("prior", justify="right")
        table.add_column("evidence", justify="right")
        table.add_column("payoff/risk", justify="right")
        for layer, block in attention.get("by_layer", {}).items():
            mass = block.get("mean_group_mass", {})
            table.add_row(
                str(layer),
                _fmt(block.get("mean_entropy")),
                _fmt(mass.get("prior")),
                _fmt(mass.get("evidence")),
                _fmt(mass.get("payoff_risk")),
            )
        console.print(table)

    if inspect:
        figures = _collect_interpretability_figures(experiments)
        if figures:
            console.print(f"[bold]figures[/bold] ({len(figures)}):")
            for figure in figures:
                console.print(f"  {figure}")
    console.print(
        "[dim]Caveat: small synthetic model organism; decodability is not causation; "
        "no frontier-model claim is made.[/dim]"
    )
    console.print(f"report: {summary.get('output_dir')}/INTERPRETABILITY_REPORT.md")


def _print_multiseed_summary(summary: dict[str, Any]) -> None:
    console.print(
        f"[bold]{summary.get('run_name')}[/bold] | "
        f"completed=[green]{summary.get('n_completed')}[/green]/{summary.get('n_attempted')} | "
        f"replicated_all=[magenta]{_yesno(bool(summary.get('causal_story_replicated_all_completed')))}[/magenta]"
    )
    console.print(f"seeds completed: {summary.get('seeds_completed')}")
    failed = summary.get("seeds_failed", [])
    if failed:
        console.print("[yellow]failed/skipped seeds:[/yellow]")
        for item in failed:
            console.print(f"  - seed {item.get('seed')}: {escape(str(item.get('reason')))}")

    table = Table(title="Per-seed headline metrics")
    table.add_column("seed", style="bold cyan")
    table.add_column("status")
    table.add_column("val action", justify="right")
    table.add_column("L0 attn rec", justify="right")
    table.add_column("L0 mlp rec", justify="right")
    table.add_column("tok-grp max", justify="right")
    table.add_column("story")
    for seed in summary.get("per_seed", []):
        metrics = seed.get("metrics") or {}
        action_recovery = metrics.get("whole_site_action_recovery", {})
        table.add_row(
            str(seed.get("seed")),
            str(seed.get("status")),
            _fmt(_dig_cli(metrics, "validation", "action_accuracy")),
            _fmt(action_recovery.get("blocks.0.attn_out")),
            _fmt(action_recovery.get("blocks.0.mlp_out")),
            _fmt(_dig_cli(metrics, "token_group", "max_action_recovery")),
            _yesno(bool(_dig_cli(seed, "story", "replicated"))),
        )
    console.print(table)

    aggregate = summary.get("aggregate_metrics", {})
    if summary.get("n_completed", 0) >= 2:
        agg_table = Table(title="Aggregate across completed seeds (mean [min, max])")
        agg_table.add_column("metric", style="bold cyan")
        agg_table.add_column("mean", justify="right")
        agg_table.add_column("range", justify="right")
        agg_table.add_column("n", justify="right")
        for key in (
            "validation_action_accuracy",
            "heldout_action_accuracy",
            "layer0_attn_action_recovery",
            "layer0_mlp_action_recovery",
            "layer1_attn_action_recovery",
            "token_group_max_action_recovery",
            "mismatched_action_matched_recovery",
            "mismatched_action_mismatched_recovery",
            "label_shuffle_real_accuracy",
            "label_shuffle_shuffled_accuracy",
        ):
            stat = aggregate.get(key, {})
            agg_table.add_row(
                key,
                _fmt(stat.get("mean")),
                f"[{_fmt(stat.get('min'))}, {_fmt(stat.get('max'))}]",
                str(stat.get("n", 0)),
            )
        console.print(agg_table)

    console.print(f"[dim]{summary.get('headline')}[/dim]")
    console.print(f"summary: {summary.get('summary_path')}")


def _dig_cli(data: Any, *keys: str) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _collect_interpretability_figures(experiments: dict[str, Any]) -> list[str]:
    figures: list[str] = []
    for block in experiments.values():
        if isinstance(block, dict):
            figures.extend(str(path) for path in block.get("figures", []))
    return figures


def _print_training_summary(summary: dict[str, Any]) -> None:
    counts = summary.get("counts", {})
    model = summary.get("model", {})
    paths = summary.get("paths", {})
    console.print(
        f"[bold]{summary.get('run_name')}[/bold] | "
        f"train={counts.get('train')} val={counts.get('val')} test={counts.get('test')} | "
        f"params={model.get('parameter_count')}"
    )
    table = Table(title="Best validation metrics")
    table.add_column("metric", style="bold cyan")
    table.add_column("value", justify="right")
    for key, value in sorted(summary.get("best_metrics", {}).items()):
        if key != "epoch":
            table.add_row(key, _fmt(value))
    console.print(table)
    console.print(f"best checkpoint: {paths.get('best_checkpoint')}")
    console.print(f"final checkpoint: {paths.get('final_checkpoint')}")
    figures = paths.get("figures") or []
    if figures:
        console.print("figures:")
        for figure in figures:
            console.print(f"  {figure}")
    if paths.get("model_card"):
        console.print(f"model card: {paths.get('model_card')}")
    console.print(f"artefacts: {summary.get('output_dir')}")


def _print_robustness_summary(summary: dict[str, Any]) -> None:
    agent = summary["agent"]
    metrics = summary["metrics"]
    counts = summary["counts"]
    console.print(
        f"[bold]{summary['run_name']}[/bold] | run_id=[cyan]{summary['run_id']}[/cyan] | "
        f"agent={agent.get('name')} ({agent.get('type')}) | "
        f"baseline=[magenta]{summary['baseline_kind']}[/magenta]"
    )
    if agent.get("warning"):
        console.print(f"[yellow]{agent['warning']}[/yellow]")
    console.print(
        f"base_tasks={counts['n_base_tasks']} variants={counts['n_variants']} | "
        f"paraphrase_consistency=[green]{_fmt(metrics.get('paraphrase_consistency_rate'))}[/green] "
        f"action_flip_rate={_fmt(metrics.get('action_flip_rate'))} "
        f"mean_score_drop={_fmt(metrics.get('mean_score_drop'))} "
        f"unsafe_action_increase={_fmt(metrics.get('unsafe_action_increase'))}"
    )
    table = Table(title="Variant-type breakdown")
    table.add_column("variant type", style="bold cyan")
    table.add_column("variants", justify="right")
    table.add_column("paraphrase consist.", justify="right")
    table.add_column("action flip", justify="right")
    table.add_column("mean drop", justify="right")
    table.add_column("pressure susc.", justify="right")
    for vtype, vmetrics in metrics.get("variant_type_breakdown", {}).items():
        table.add_row(
            vtype,
            str(vmetrics["n_variants"]),
            _fmt(vmetrics.get("paraphrase_consistency_rate")),
            _fmt(vmetrics.get("action_flip_rate")),
            _fmt(vmetrics.get("mean_score_drop")),
            _fmt(vmetrics.get("pressure_susceptibility_rate")),
        )
    console.print(table)
    console.print(f"artefacts: {summary['output_dir']}")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.3f}"
    return str(value)


def _print_comparison_summary(summary: dict[str, Any]) -> None:
    console.print(
        f"[bold]{summary['comparison_name']}[/bold] | "
        f"run_id=[cyan]{summary['run_id']}[/cyan] | "
        f"baseline=[magenta]{summary['baseline_agent_key']}[/magenta] "
        f"({summary['baseline_kind']})"
    )
    table = Table(title="Agents")
    table.add_column("agent key", style="bold cyan")
    table.add_column("label")
    table.add_column("tasks", justify="right")
    table.add_column("mean score", justify="right")
    table.add_column("parse fail", justify="right")
    for agent in summary["agents"]:
        overall = agent["metrics"]["overall"]
        table.add_row(
            agent["agent_key"],
            agent["baseline_kind"],
            str(overall["n_tasks"]),
            _fmt(overall["mean_score"]),
            _fmt(overall["parse_failure_rate"]),
        )
    console.print(table)
    if summary.get("paired_metrics"):
        delta_table = Table(title="Paired deltas (candidate - baseline)")
        delta_table.add_column("candidate", style="bold cyan")
        delta_table.add_column("pairs", justify="right")
        delta_table.add_column("score", justify="right")
        delta_table.add_column("posterior error", justify="right")
        delta_table.add_column("risk viol.", justify="right")
        delta_table.add_column("parse fail", justify="right")
        for candidate, metrics in summary["paired_metrics"].items():
            delta_table.add_row(
                candidate,
                str(metrics["n_pairs"]),
                _fmt(metrics.get("mean_score_difference")),
                _fmt(metrics.get("mean_posterior_error_difference")),
                _fmt(metrics.get("mean_risk_violation_difference")),
                _fmt(metrics.get("mean_parse_failure_difference")),
            )
        console.print(delta_table)
    console.print(f"artefacts: {summary['output_dir']}")


def _print_leaderboard_summary(summary: dict[str, Any]) -> None:
    console.print(
        f"[bold]{summary['leaderboard_name']}[/bold] | "
        f"run_id=[cyan]{summary['run_id']}[/cyan] | "
        f"preliminary=[magenta]{_yesno(bool(summary.get('preliminary')))}[/magenta]"
    )
    availability = summary.get("provider_availability", {})
    if availability:
        table = Table(title="Provider availability")
        table.add_column("model", style="bold cyan")
        table.add_column("provider")
        table.add_column("usable", justify="right")
        table.add_column("detail")
        for label, status in availability.items():
            table.add_row(
                str(label),
                str(status.get("provider")),
                _yesno(bool(status.get("usable"))),
                escape(str(status.get("detail", ""))),
            )
        console.print(table)

    rows = summary.get("leaderboard", [])
    table = Table(title="Leaderboard")
    table.add_column("model", style="bold cyan")
    table.add_column("provider")
    table.add_column("agent")
    table.add_column("envs", justify="right")
    table.add_column("tasks", justify="right")
    table.add_column("mean score", justify="right")
    table.add_column("robustness", justify="right")
    table.add_column("risk viol.", justify="right")
    table.add_column("parse fail", justify="right")
    table.add_column("cost")
    table.add_column("latency p50/p95", justify="right")
    if rows:
        for row in rows:
            table.add_row(
                str(row.get("model")),
                str(row.get("provider")),
                str(row.get("agent")),
                _fmt(row.get("n_envs")),
                _fmt(row.get("n_tasks")),
                _fmt(row.get("mean_score")),
                f"{_fmt(row.get('robustness_paraphrase_consistency'))}/"
                f"{_fmt(row.get('robustness_mean_score_drop'))}",
                _fmt(row.get("risk_violation_rate")),
                _fmt(row.get("parse_failure_rate")),
                _leaderboard_cost_cell(row),
                f"{_fmt(row.get('latency_p50_ms'))}/{_fmt(row.get('latency_p95_ms'))}",
            )
    else:
        table.add_row("no models run", "", "", "", "", "", "", "", "", "", "")
    console.print(table)

    pending = summary.get("models_pending", [])
    if pending:
        console.print("[yellow]No real model run was performed for pending providers.[/yellow]")
        for model in pending:
            console.print(
                f"  {model.get('label')} ({model.get('provider')}): "
                f"{escape(str(model.get('detail', '')))}"
            )

    candidates = summary.get("headline_candidates", [])
    if candidates:
        console.print("[bold]headline candidates[/bold]")
        for candidate in candidates:
            console.print(f"  - {candidate.get('text')}")
    else:
        console.print("headline candidates: none")
    console.print(f"artefacts: {summary['output_dir']}")


def _leaderboard_cost_cell(row: dict[str, Any]) -> str:
    cost = row.get("estimated_cost_usd")
    if row.get("cost_estimated") and cost is not None:
        return f"${_fmt(cost)}"
    return "not estimated"


def _yesno(value: bool) -> str:
    return "[green]yes[/green]" if value else "[red]no[/red]"


def _approx_tokens(chars: int) -> int:
    """Very rough token estimate (~4 characters per token)."""
    return max(1, round(chars / 4))


def _calls_per_task(agent_type: str, agent_config: Any) -> tuple[int, bool]:
    """Return (model_calls_per_task, is_model_backed) for cost estimation."""
    if agent_type in {"reference", "mock"}:
        return 0, False
    if agent_type == "reflective":
        return 3, True
    if agent_type == "tool":
        policy = (getattr(agent_config, "tool_policy", "reference") or "reference").lower()
        if policy == "reference":
            return 0, False
        return int(getattr(agent_config, "tool_max_steps", 3)) + 1, True
    return 1, True  # api / local / direct


def _estimate_cost(config: EvalRunConfig | EvalConfig) -> dict[str, Any]:
    from mimirbench.agents.model_client import Pricing
    from mimirbench.agents.prompts import build_messages
    from mimirbench.evals import registry

    if isinstance(config, EvalConfig):
        envs = [(config.environment, config.n_tasks, config.seed)]
        agent_type = config.agent if isinstance(config.agent, str) else "reference"
        agent_config: Any = None
        system_prompt = None
        max_output = 1024
    else:
        envs = [
            (e.name, e.num_tasks, e.seed if e.seed is not None else config.run.seed)
            for e in config.environments
        ]
        agent_config = config.agent
        agent_type = config.agent.type.lower()
        system_prompt = config.agent.system_prompt
        max_output = (
            config.agent.max_new_tokens if agent_type == "local" else config.agent.max_tokens
        )

    calls_per_task, model_backed = _calls_per_task(agent_type, agent_config)
    per_env: list[dict[str, Any]] = []
    total_tasks = 0
    est_input_tokens = 0
    for name, num, seed in envs:
        spec = registry.get(name)
        bundle = build_messages(spec.generator(seed).task, system_prompt=system_prompt)
        tokens = _approx_tokens(len(bundle.system) + len(bundle.user))
        per_env.append({"environment": name, "num_tasks": num, "input_tokens_per_task": tokens})
        total_tasks += num
        est_input_tokens += tokens * num

    total_input = est_input_tokens * calls_per_task
    total_output_upper = total_tasks * calls_per_task * max_output
    pricing = Pricing.from_mapping(getattr(agent_config, "pricing", None)) if agent_config else None

    cost_upper = None
    if pricing is not None and model_backed:
        cost_upper = round(
            total_input / 1000.0 * pricing.input_usd_per_1k
            + total_output_upper / 1000.0 * pricing.output_usd_per_1k,
            4,
        )

    return {
        "agent_type": agent_type,
        "model_backed": model_backed,
        "model_calls_per_task": calls_per_task,
        "total_tasks": total_tasks,
        "model_calls_total": total_tasks * calls_per_task,
        "est_total_input_tokens": total_input,
        "est_total_output_tokens_upper": total_output_upper,
        "pricing_configured": pricing is not None,
        "est_cost_usd_upper": cost_upper,
        "per_env": per_env,
    }


def _estimate_comparison_cost(config: ComparisonConfig) -> dict[str, Any]:
    agents: list[dict[str, Any]] = []
    for agent in config.agents:
        eval_config = EvalRunConfig(
            run=config.run,
            agent=agent,
            environments=config.environments,
            reporting=config.reporting,
        )
        estimate = _estimate_cost(eval_config)
        estimate["agent_name"] = agent.name or agent.type
        agents.append(estimate)

    return {
        "comparison_name": config.run.name,
        "agents": agents,
        "total_tasks_per_agent": sum(env.num_tasks for env in config.environments),
        "model_calls_total": sum(int(agent["model_calls_total"]) for agent in agents),
        "est_total_input_tokens": sum(int(agent["est_total_input_tokens"]) for agent in agents),
        "est_total_output_tokens_upper": sum(
            int(agent["est_total_output_tokens_upper"]) for agent in agents
        ),
        "model_backed": any(bool(agent["model_backed"]) for agent in agents),
        "est_cost_usd_upper": _sum_optional_costs(agents),
    }


def _estimate_leaderboard_cost(config: Any) -> dict[str, Any]:
    from mimirbench.evals.leaderboard import build_agent_config

    cells: list[dict[str, Any]] = []
    robustness_modes = {
        mode.lower().strip() for mode in (config.robustness.agents or config.agents)
    }
    for model in config.models:
        for mode in config.agents:
            agent_config = build_agent_config(model, mode)
            eval_config = EvalRunConfig(
                run=config.run,
                agent=agent_config,
                environments=config.environments,
                reporting=config.reporting,
            )
            estimate = _estimate_cost(eval_config)
            estimate.update(
                {
                    "model_label": model.label,
                    "provider": model.provider,
                    "agent_mode": mode,
                    "phase": "eval",
                }
            )
            cells.append(estimate)

            if config.robustness.enabled and mode.lower().strip() in robustness_modes:
                variant_count = config.robustness.max_variants_per_task
                robustness_envs = [
                    EnvironmentRunConfig(
                        name=env.name,
                        num_tasks=env.num_tasks * variant_count,
                        seed=env.seed,
                    )
                    for env in config.environments
                ]
                robustness_estimate = _estimate_cost(
                    EvalRunConfig(
                        run=config.run,
                        agent=agent_config,
                        environments=robustness_envs,
                        reporting=config.reporting,
                    )
                )
                robustness_estimate.update(
                    {
                        "model_label": model.label,
                        "provider": model.provider,
                        "agent_mode": mode,
                        "phase": "robustness",
                    }
                )
                cells.append(robustness_estimate)

    return {
        "leaderboard_name": config.run.name,
        "cells": cells,
        "base_tasks_per_cell": sum(env.num_tasks for env in config.environments),
        "model_calls_total": sum(int(cell["model_calls_total"]) for cell in cells),
        "est_total_input_tokens": sum(int(cell["est_total_input_tokens"]) for cell in cells),
        "est_total_output_tokens_upper": sum(
            int(cell["est_total_output_tokens_upper"]) for cell in cells
        ),
        "model_backed": any(bool(cell["model_backed"]) for cell in cells),
        "est_cost_usd_upper": _sum_optional_costs(cells),
        "robustness_enabled": config.robustness.enabled,
    }


def _estimate_robustness_cost(config: Any) -> dict[str, Any]:
    robustness_envs = [
        EnvironmentRunConfig(
            name=env.name,
            num_tasks=env.num_tasks
            * (1 + min(env.variants_per_task, config.robustness.max_variants_per_task)),
            seed=env.seed,
        )
        for env in config.environments
    ]
    estimate = _estimate_cost(
        EvalRunConfig(
            run=config.run,
            agent=config.agent,
            environments=robustness_envs,
            reporting=ReportingConfig(),
        )
    )
    estimate["robustness_base_tasks"] = sum(env.num_tasks for env in config.environments)
    estimate["robustness_variant_tasks_upper"] = sum(
        env.num_tasks * min(env.variants_per_task, config.robustness.max_variants_per_task)
        for env in config.environments
    )
    return estimate


def _print_cost_estimate(estimate: dict[str, Any]) -> None:
    console.print(
        f"[bold]Run estimate[/bold] | agent_type=[cyan]{estimate['agent_type']}[/cyan] | "
        f"tasks={estimate['total_tasks']}"
    )
    if not estimate["model_backed"]:
        console.print(
            "[green]Non-model baseline (reference / mock / reference-tool): no API calls, "
            "no token cost.[/green]"
        )
        return
    console.print(
        f"model calls/task={estimate['model_calls_per_task']} "
        f"total model calls={estimate['model_calls_total']}"
    )
    console.print(
        f"est. input tokens ~{estimate['est_total_input_tokens']:,}; "
        f"est. output tokens (upper bound) ~{estimate['est_total_output_tokens_upper']:,}"
    )
    if estimate["pricing_configured"]:
        console.print(
            f"[yellow]Rough cost upper bound:[/yellow] ~${estimate['est_cost_usd_upper']} USD "
            "(assumes max output tokens every call)."
        )
    else:
        console.print(
            "[yellow]Cost not estimated:[/yellow] no pricing configured. Add a 'pricing' block "
            "(input_usd_per_1k / output_usd_per_1k) to the agent config to estimate cost."
        )
    console.print(
        "[dim]Estimate uses ~4 chars/token on one representative task per environment and an "
        "upper-bound output length. Actual tokens, retries, and tool steps will differ; this is "
        "not an exact cost.[/dim]"
    )


def _print_comparison_cost_estimate(estimate: dict[str, Any]) -> None:
    console.print(
        f"[bold]Comparison estimate[/bold] | "
        f"name=[cyan]{estimate['comparison_name']}[/cyan] | "
        f"tasks/agent={estimate['total_tasks_per_agent']}"
    )
    table = Table(title="Agent estimates")
    table.add_column("agent", style="bold cyan")
    table.add_column("type")
    table.add_column("model calls", justify="right")
    table.add_column("input tokens", justify="right")
    table.add_column("output upper", justify="right")
    table.add_column("cost upper", justify="right")
    for agent in estimate["agents"]:
        table.add_row(
            str(agent["agent_name"]),
            str(agent["agent_type"]),
            str(agent["model_calls_total"]),
            f"{int(agent['est_total_input_tokens']):,}",
            f"{int(agent['est_total_output_tokens_upper']):,}",
            "n/a" if agent["est_cost_usd_upper"] is None else f"${agent['est_cost_usd_upper']}",
        )
    console.print(table)
    if not estimate["model_backed"]:
        console.print("[green]All agents are non-model baselines: no API calls, no token cost.[/green]")
        return
    console.print(
        f"total model calls={estimate['model_calls_total']} | "
        f"est. input tokens ~{estimate['est_total_input_tokens']:,}; "
        f"est. output tokens upper bound ~{estimate['est_total_output_tokens_upper']:,}"
    )
    if estimate["est_cost_usd_upper"] is None:
        console.print(
            "[yellow]Cost not estimated:[/yellow] no pricing configured for one or more model-backed agents."
        )
    else:
        console.print(f"[yellow]Rough total cost upper bound:[/yellow] ~${estimate['est_cost_usd_upper']} USD")


def _print_leaderboard_cost_estimate(estimate: dict[str, Any]) -> None:
    console.print(
        f"[bold]Leaderboard estimate[/bold] | "
        f"name=[cyan]{estimate['leaderboard_name']}[/cyan] | "
        f"base tasks/cell={estimate['base_tasks_per_cell']}"
    )
    table = Table(title="Cell estimates")
    table.add_column("model", style="bold cyan")
    table.add_column("agent")
    table.add_column("phase")
    table.add_column("tasks", justify="right")
    table.add_column("model calls", justify="right")
    table.add_column("input tokens", justify="right")
    table.add_column("output upper", justify="right")
    table.add_column("cost upper", justify="right")
    for cell in estimate["cells"]:
        table.add_row(
            str(cell["model_label"]),
            str(cell["agent_mode"]),
            str(cell["phase"]),
            str(cell["total_tasks"]),
            str(cell["model_calls_total"]),
            f"{int(cell['est_total_input_tokens']):,}",
            f"{int(cell['est_total_output_tokens_upper']):,}",
            "n/a" if cell["est_cost_usd_upper"] is None else f"${cell['est_cost_usd_upper']}",
        )
    console.print(table)
    if not estimate["model_backed"]:
        console.print("[green]All cells are non-model baselines: no API calls, no token cost.[/green]")
        return
    console.print(
        f"total model calls={estimate['model_calls_total']} | "
        f"est. input tokens ~{estimate['est_total_input_tokens']:,}; "
        f"est. output tokens upper bound ~{estimate['est_total_output_tokens_upper']:,}"
    )
    if estimate["est_cost_usd_upper"] is None:
        console.print(
            "[yellow]Cost not estimated:[/yellow] no pricing configured for one or more model-backed cells."
        )
    else:
        console.print(
            f"[yellow]Rough total cost upper bound:[/yellow] ~${estimate['est_cost_usd_upper']} USD"
        )
    if estimate["robustness_enabled"]:
        console.print("[dim]Robustness cells are included using max_variants_per_task as an upper bound.[/dim]")


def _sum_optional_costs(agent_estimates: list[dict[str, Any]]) -> float | None:
    costs = [agent["est_cost_usd_upper"] for agent in agent_estimates]
    model_costs = [
        float(cost)
        for cost in costs
        if isinstance(cost, (int, float)) and not isinstance(cost, bool)
    ]
    model_backed = [agent for agent in agent_estimates if agent["model_backed"]]
    if not model_backed:
        return None
    if len(model_costs) != len(model_backed):
        return None
    return round(sum(model_costs), 4)


def _apply_overrides(
    config: EvalRunConfig | EvalConfig,
    *,
    n_tasks: int | None,
    seed: int | None,
) -> EvalRunConfig | EvalConfig:
    if isinstance(config, EvalConfig):
        updates: dict[str, Any] = {}
        if n_tasks is not None:
            updates["n_tasks"] = n_tasks
        if seed is not None:
            updates["seed"] = seed
        return config.model_copy(update=updates) if updates else config

    updated = config
    if n_tasks is not None:
        environments = [
            EnvironmentRunConfig(name=env.name, num_tasks=n_tasks, seed=env.seed)
            for env in updated.environments
        ]
        updated = updated.model_copy(update={"environments": environments})
    if seed is not None:
        updated = updated.model_copy(update={"run": updated.run.model_copy(update={"seed": seed})})
    return updated


def _print_legacy_report(environment: str, agent: str, report: dict[str, Any]) -> None:
    console.print(
        f"[bold]{environment}[/bold] | agent=[cyan]{agent}[/cyan] | "
        f"n_tasks={report['n_tasks']} | seed={report['seed']}"
    )
    console.print(
        f"mean_score=[green]{report['mean_score']:.4f}[/green] "
        f"pass_rate={report['pass_rate']:.3f} violation_rate={report['violation_rate']:.3f}"
    )


def _print_summary(summary: dict[str, Any]) -> None:
    agent = summary["agent"]
    overall = summary["metrics"]["overall"]
    console.print(
        f"[bold]{summary['run_name']}[/bold] | run_id=[cyan]{summary['run_id']}[/cyan] | "
        f"agent={agent.get('name')} ({agent.get('type')})"
    )
    warning = agent.get("warning")
    if warning:
        console.print(f"[yellow]{warning}[/yellow]")
    console.print(
        f"tasks={overall['n_tasks']} mean_score=[green]{overall['mean_score']:.4f}[/green] "
        f"pass_rate={overall['pass_rate']:.3f} runtime_error_rate={overall['runtime_error_rate']:.3f}"
    )
    table = Table(title="Environment summaries")
    table.add_column("environment", style="bold cyan")
    table.add_column("tasks", justify="right")
    table.add_column("mean score", justify="right")
    table.add_column("pass rate", justify="right")
    table.add_column("invalid", justify="right")
    for environment, metrics in summary["metrics"]["environments"].items():
        table.add_row(
            environment,
            str(metrics["n_tasks"]),
            f"{metrics['mean_score']:.4f}",
            f"{metrics['pass_rate']:.3f}",
            f"{metrics['invalid_response_rate']:.3f}",
        )
    console.print(table)
    console.print(f"artefacts: {summary['output_dir']}")


if __name__ == "__main__":  # pragma: no cover
    app()
