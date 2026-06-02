"""Agent wrapper for Stage 7 small-transformer Bayesian checkpoints."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from mimirbench.agents.base import BaseAgent
from mimirbench.environments.bayesian_games.schemas import BayesianTaskParams
from mimirbench.evals.schemas import EnvironmentFamily, ModelResponse, Task
from mimirbench.training.small_transformer import SmallTransformerForTracePrediction, require_torch
from mimirbench.training.synthetic_traces import bucket_midpoint, task_params_to_trace_input
from mimirbench.training.tokenizer import TraceTokenizer

__all__ = ["SmallTransformerAgent"]


class SmallTransformerAgent(BaseAgent):
    """Load a saved small-transformer checkpoint and answer Bayesian tasks."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        *,
        device: str = "cpu",
        name: str = "small_transformer",
    ) -> None:
        super().__init__(name)
        torch_mod, _, _ = require_torch()
        self.checkpoint_path = Path(checkpoint_path)
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"checkpoint not found: {self.checkpoint_path}")
        self.device = torch_mod.device(device)
        model, payload = SmallTransformerForTracePrediction.load_checkpoint(
            self.checkpoint_path,
            map_location=str(self.device),
        )
        model.to(self.device)
        self.model = model
        tokenizer_payload = payload.get("tokenizer")
        if not isinstance(tokenizer_payload, dict):
            raise ValueError("checkpoint is missing tokenizer payload.")
        self.tokenizer = TraceTokenizer.from_dict(tokenizer_payload)
        self._torch = torch_mod

    def act(self, task: Task) -> ModelResponse:
        """Predict structured fields for a Bayesian task."""
        if task.family != EnvironmentFamily.BAYESIAN_GAMES:
            raise ValueError(
                "SmallTransformerAgent only supports bayesian_games tasks; "
                f"got {task.family.value}."
            )
        params = BayesianTaskParams(**task.metadata)
        input_text = task_params_to_trace_input(params)
        start = time.perf_counter()
        encoded = self.tokenizer.encode(input_text)
        input_ids = self._torch.as_tensor(
            [encoded["input_ids"]],
            dtype=self._torch.long,
            device=self.device,
        )
        attention_mask = self._torch.as_tensor(
            [encoded["attention_mask"]],
            dtype=self._torch.long,
            device=self.device,
        )
        prediction = self.model.predict(input_ids, attention_mask=attention_mask)
        posterior = _posterior_from_bucket(
            prediction.get("posterior_bucket"),
            params.n_hypotheses,
        )
        parsed = {
            "posterior": posterior,
            "posterior_bucket": prediction.get("posterior_bucket"),
            "action": prediction.get("action"),
            "risk_flag": prediction.get("risk_flag"),
            "confidence_bucket": prediction.get("confidence_bucket"),
            "rationale_class": prediction.get("rationale_class"),
        }
        raw = json.dumps(parsed, sort_keys=True)
        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text=raw,
            parsed_answer=parsed,
            reasoning_summary=(
                "Small synthetic checkpoint prediction using posterior bucket "
                f"{prediction.get('posterior_bucket')}."
            ),
            latency_s=time.perf_counter() - start,
            metadata={
                "checkpoint_path": str(self.checkpoint_path),
                "provider": "local_synthetic",
                "model": "small_transformer_bayes",
            },
        )


def _posterior_from_bucket(bucket: Any, n_hypotheses: int) -> list[float]:
    if not isinstance(bucket, str):
        p_a = 1.0 / n_hypotheses
    else:
        p_a = min(1.0, max(0.0, bucket_midpoint(bucket)))
    if n_hypotheses == 1:
        return [1.0]
    remaining = max(0.0, 1.0 - p_a)
    other = remaining / (n_hypotheses - 1)
    posterior = [p_a, *([other] * (n_hypotheses - 1))]
    total = sum(posterior)
    return [value / total for value in posterior]
