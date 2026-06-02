"""Local JSONL response cache for evaluation runs."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from mimirbench.evals.schemas import AgentConfig, ModelResponse, Task

__all__ = ["CacheEntry", "ResponseCache", "make_cache_key", "stable_json_dumps"]


def stable_json_dumps(data: Any) -> str:
    """Dump JSON with stable key ordering and compact separators."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _package_version() -> str:
    try:
        return version("mimirbench")
    except PackageNotFoundError:
        return "0.1.0"


def make_cache_key(
    *,
    agent_config: AgentConfig,
    environment: str,
    task: Task,
    package_version: str | None = None,
) -> str:
    """Build a deterministic cache key for one agent/task pair."""
    payload = {
        "agent_config": agent_config.model_dump(mode="json"),
        "environment": environment,
        "package_version": package_version or _package_version(),
        "task": task.model_dump(mode="json"),
    }
    return hashlib.sha256(stable_json_dumps(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CacheEntry:
    """A cached model response and its metadata."""

    key: str
    model_response: ModelResponse
    metadata: dict[str, Any]


class ResponseCache:
    """Append-only JSONL cache with an in-memory index."""

    def __init__(
        self,
        path: Path,
        *,
        enabled: bool = True,
        bypass: bool = False,
    ) -> None:
        self.path = path
        self.enabled = enabled
        self.bypass = bypass
        self._lock = threading.Lock()
        self._entries: dict[str, CacheEntry] = {}
        if self.enabled:
            self._load()

    def get(self, key: str) -> CacheEntry | None:
        """Return a cache entry unless disabled or bypassed."""
        if not self.enabled or self.bypass:
            return None
        return self._entries.get(key)

    def set(
        self,
        key: str,
        response: ModelResponse,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a response to the cache and update the in-memory index."""
        if not self.enabled or self.bypass:
            return
        entry = CacheEntry(key=key, model_response=response, metadata=metadata or {})
        row = {
            "key": entry.key,
            "model_response": response.model_dump(mode="json"),
            "metadata": entry.metadata,
        }
        encoded = stable_json_dumps(row)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(encoded + "\n")
            self._entries[key] = entry

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                    key = row["key"]
                    response = ModelResponse.model_validate(row["model_response"])
                    metadata = row.get("metadata", {})
                except Exception as exc:
                    raise RuntimeError(
                        f"failed to read cache row {line_no} from {self.path}: "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                if not isinstance(key, str) or not isinstance(metadata, dict):
                    raise RuntimeError(f"invalid cache row {line_no} in {self.path}.")
                self._entries[key] = CacheEntry(
                    key=key,
                    model_response=response,
                    metadata=metadata,
                )
