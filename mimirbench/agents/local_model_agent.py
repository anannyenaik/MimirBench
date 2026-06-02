"""Local (Hugging Face ``transformers``) model agent.

A :class:`~mimirbench.agents.direct_agent.DirectAgent` backed by an
:class:`~mimirbench.agents.providers.hf_local_client.HFLocalClient`. ``torch`` and
``transformers`` are optional dependencies (``pip install -e ".[ml]"``) imported
lazily by the client; constructing this agent never loads or downloads a model.
"""

from __future__ import annotations

from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.agents.prompts import DEFAULT_SYSTEM_PROMPT
from mimirbench.agents.providers import HFLocalClient

__all__ = ["LocalModelAgent"]


class LocalModelAgent(DirectAgent):
    """Generate completions from a local causal/instruct language model."""

    def __init__(
        self,
        model_name: str,
        *,
        name: str | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float | None = None,
        do_sample: bool | None = None,
        device: str | None = None,
    ) -> None:
        client = HFLocalClient(
            model_name,
            device=device or "auto",
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
        )
        super().__init__(
            client,
            name=name or f"local::{model_name}",
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_new_tokens,
            top_p=top_p,
        )
        # Convenience attributes for resolvers/tests; the client owns the weights.
        self.model_name = model_name
        self.device = device
        self.max_new_tokens = max_new_tokens
