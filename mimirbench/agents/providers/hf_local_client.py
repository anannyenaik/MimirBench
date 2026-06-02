"""Local Hugging Face ``transformers`` model client.

Implements :class:`~mimirbench.agents.model_client.ModelClient` against a locally
hosted causal / instruct language model. ``torch`` and ``transformers`` are
optional dependencies (``pip install -e ".[ml]"``) imported lazily; the model and
tokenizer are loaded on first :meth:`generate`, so constructing the client is
cheap and never downloads weights during tests.

Local generation has no provider-side token billing, so
:attr:`ModelUsage.estimated_cost_usd` is always ``None`` (reported as "not
estimated") and token counts come from the tokenizer where available.
"""

from __future__ import annotations

import time
from typing import Any

from mimirbench.agents.model_client import (
    ModelClient,
    ModelClientError,
    ModelRequest,
    ModelResponseEnvelope,
    ModelUsage,
    ProviderStatus,
)
from mimirbench.agents.parsing import extract_json

__all__ = ["HFLocalClient", "resolve_device"]

_VALID_DEVICES = {"auto", "cpu", "cuda", "mps"}


def resolve_device(device: str | None) -> str:
    """Resolve an ``auto`` / explicit device request to a concrete torch device.

    ``auto`` prefers CUDA, then Apple MPS, then CPU. Importing torch is the
    caller's responsibility (this is invoked only after a lazy import).
    """
    requested = (device or "auto").lower()
    if requested not in _VALID_DEVICES:
        raise ValueError(f"device must be one of {sorted(_VALID_DEVICES)}, got {device!r}.")
    if requested != "auto":
        return requested
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
    except ImportError:  # pragma: no cover - optional dependency
        pass
    return "cpu"


class HFLocalClient(ModelClient):
    """Generate completions from a local causal LM via ``transformers``."""

    provider = "hf_local"

    def __init__(
        self,
        model: str,
        *,
        device: str | None = "auto",
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float | None = None,
        do_sample: bool | None = None,
    ) -> None:
        if not model:
            raise ValueError("HFLocalClient requires a non-empty model name.")
        if device is not None and device.lower() not in _VALID_DEVICES:
            raise ValueError(f"device must be one of {sorted(_VALID_DEVICES)}, got {device!r}.")
        self.model = model
        self.device_request = device or "auto"
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._resolved_device: str | None = None

    def check_availability(self) -> ProviderStatus:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401

            package_available = True
        except ImportError:
            package_available = False
        detail = (
            f"torch+transformers available; model '{self.model}' will load on first use "
            f"(device request: {self.device_request})."
            if package_available
            else 'torch/transformers not installed (pip install -e ".[ml]").'
        )
        return ProviderStatus(
            provider=self.provider,
            package_available=package_available,
            key_required=False,
            key_present=False,
            key_env=None,
            usable=package_available,
            detail=detail,
        )

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            import torch  # noqa: F401
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelClientError(
                "Local model support requires the 'ml' extra. Install it with: "
                'pip install -e ".[ml]"'
            ) from exc
        self._resolved_device = resolve_device(self.device_request)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model)
        self._model = AutoModelForCausalLM.from_pretrained(self.model)
        if self._resolved_device != "cpu":
            self._model = self._model.to(self._resolved_device)

    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:  # pragma: no cover - needs ml extra
        self._ensure_loaded()
        assert self._model is not None and self._tokenizer is not None
        import torch

        text = self._render_chat(request)
        inputs = self._tokenizer(text, return_tensors="pt")
        if self._resolved_device and self._resolved_device != "cpu":
            inputs = {k: v.to(self._resolved_device) for k, v in inputs.items()}

        do_sample = self.do_sample if self.do_sample is not None else request.temperature > 0.0
        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": request.max_tokens or self.max_new_tokens,
            "do_sample": do_sample,
        }
        if do_sample:
            gen_kwargs["temperature"] = max(request.temperature, 1e-4)
            if request.top_p is not None or self.top_p is not None:
                gen_kwargs["top_p"] = request.top_p if request.top_p is not None else self.top_p

        prompt_tokens = int(inputs["input_ids"].shape[-1])
        start = time.perf_counter()
        with torch.no_grad():
            output_ids = self._model.generate(**inputs, **gen_kwargs)
        latency_ms = (time.perf_counter() - start) * 1000.0

        generated = output_ids[0][prompt_tokens:]
        completion_tokens = int(generated.shape[-1])
        raw_text = str(self._tokenizer.decode(generated, skip_special_tokens=True))

        usage = ModelUsage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=None,  # local inference: no provider billing.
        )
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=raw_text,
            parsed_json=extract_json(raw_text),
            usage=usage,
            latency_ms=latency_ms,
            finish_reason="stop",
            metadata={"device": self._resolved_device},
        )

    def _render_chat(self, request: ModelRequest) -> str:  # pragma: no cover - needs ml extra
        assert self._tokenizer is not None
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]
        if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template:
            return str(
                self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            )
        return f"{request.system_prompt}\n\n{request.user_prompt}"
