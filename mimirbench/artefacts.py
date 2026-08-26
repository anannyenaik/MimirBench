"""How a run writes and identifies the files it commits to ``reports/``.

Run summaries, model cards, and reports are committed and reviewed, so nothing
about them may vary with the machine that produced them:

* **Path separators.** ``str(Path("reports") / "runs")`` yields ``reports\\runs``
  on Windows and ``reports/runs`` elsewhere, so otherwise identical runs diff
  against each other and the paths render wrongly in Markdown.
* **JSON layout.** Keys are sorted and separators fixed, so a re-run produces a
  byte-identical file rather than a reordered one.
* **Line endings.** Writers pass ``newline="\\n"`` so a report regenerated on
  Windows matches the committed copy byte for byte.
* **Run identity.** Every runner stamps its output with the same UTC timestamp
  format and derives run IDs the same way.

This module is the single home for all four. It is a leaf: it imports nothing
from the rest of the package, so any layer may use it.

Note that :func:`mimirbench.evals.cache.stable_json_dumps` is deliberately
separate. It feeds cache keys and config hashes, where the exact byte sequence is
part of the reproducibility contract and must not be refactored casually.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import Any

__all__ = [
    "artefact_path",
    "make_run_id",
    "stable_json",
    "utc_timestamp",
    "write_json",
    "write_jsonl",
]


def artefact_path(path: str | PurePath) -> str:
    """Render ``path`` with forward slashes for storage in an artefact."""
    return Path(path).as_posix()


def utc_timestamp() -> str:
    """Return the current UTC time as ``YYYY-MM-DDTHH:MM:SSZ``."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_run_id(run_name: str, timestamp: str) -> str:
    """Build a filesystem-safe run identifier from a run name and timestamp."""
    safe_timestamp = timestamp.replace(":", "").replace("-", "").replace("Z", "")
    safe_name = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in run_name)
    return f"{safe_name}-{safe_timestamp}"


def stable_json(data: Any, *, indent: int | None = None) -> str:
    """Serialise ``data`` deterministically: sorted keys, no ASCII escaping."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
        indent=indent,
        ensure_ascii=False,
    )


def write_json(data: dict[str, Any], path: Path) -> None:
    """Write one indented JSON document, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    """Write one compact JSON document per line, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")
