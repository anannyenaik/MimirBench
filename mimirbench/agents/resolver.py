"""Agent factory for config-driven evaluation runs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mimirbench.agents.api_model_agent import APIModelAgent
from mimirbench.agents.base import BaseAgent, ReferenceAgent
from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.agents.local_model_agent import LocalModelAgent
from mimirbench.agents.mock_agents import (
    AlwaysAbstainAgent,
    NoisyReferenceAgent,
    RandomValidAgent,
)
from mimirbench.agents.model_client import Pricing, RetryConfig
from mimirbench.agents.prompts import DEFAULT_SYSTEM_PROMPT
from mimirbench.agents.reflective_agent import ReflectiveAgent
from mimirbench.agents.small_transformer_agent import SmallTransformerAgent
from mimirbench.agents.tool_agent import ModelToolAgent, ReferenceToolAgent, ToolAgent
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import AgentConfig

__all__ = ["resolve_agent"]


def resolve_agent(
    config: AgentConfig | Mapping[str, Any] | str,
    *,
    spec: EnvironmentSpec | None = None,
) -> BaseAgent:
    """Instantiate an agent from a config dictionary.

    Optional dependencies remain lazy: resolving ``api``, ``local``, or a
    model-backed ``tool`` agent creates the agent object but imports ``openai``,
    ``anthropic``, ``torch``, or ``transformers`` only on the first model call.
    """

    agent_config = _coerce_config(config)
    agent_type = agent_config.type.lower().strip()

    if agent_type == "reference":
        if spec is None:
            raise ValueError("agent type 'reference' requires an environment spec.")
        return ReferenceAgent(spec.reference_solver, name=agent_config.name or "reference")
    if agent_type == "mock":
        return _resolve_mock(agent_config)
    if agent_type == "api":
        return _resolve_api(agent_config)
    if agent_type == "local":
        return _resolve_local(agent_config)
    if agent_type == "direct":
        return _resolve_direct(agent_config)
    if agent_type == "reflective":
        return _resolve_reflective(agent_config, spec=spec)
    if agent_type == "tool":
        return _resolve_tool(agent_config, spec=spec)
    if agent_type == "small_transformer":
        return _resolve_small_transformer(agent_config)

    raise ValueError(
        f"unknown agent type {agent_config.type!r}. Expected one of: "
        "reference, direct, tool, reflective, local, api, mock, small_transformer."
    )


def _coerce_config(config: AgentConfig | Mapping[str, Any] | str) -> AgentConfig:
    if isinstance(config, AgentConfig):
        return config
    if isinstance(config, str):
        return AgentConfig(type=config)
    return AgentConfig(**dict(config))


def _system_prompt(config: AgentConfig) -> str:
    return config.system_prompt or DEFAULT_SYSTEM_PROMPT


def _pricing(config: AgentConfig) -> Pricing | None:
    return Pricing.from_mapping(config.pricing)


def _resolve_mock(config: AgentConfig) -> BaseAgent:
    behaviour = (config.behaviour or "random_valid").lower().strip()
    if behaviour in {"always_abstain", "abstain"}:
        return AlwaysAbstainAgent(name=config.name or "mock::always_abstain")
    if behaviour == "random_valid":
        return RandomValidAgent(seed=config.seed, name=config.name or "mock::random_valid")
    if behaviour in {"noisy_reference", "noisy"}:
        return NoisyReferenceAgent(
            seed=config.seed,
            posterior_noise=config.posterior_noise,
            action_error_rate=config.action_error_rate,
            confidence_bias=config.confidence_bias,
            risk_violation_rate=config.risk_violation_rate,
            name=config.name or "mock::noisy_reference",
        )
    raise ValueError(
        f"unknown mock behaviour {config.behaviour!r}. Expected one of: "
        "always_abstain, random_valid, noisy_reference."
    )


def _resolve_api(config: AgentConfig) -> APIModelAgent:
    provider = (config.provider or "openai").lower().strip()
    if not config.model:
        raise ValueError("agent type 'api' requires a non-empty 'model' field.")
    return APIModelAgent(
        model=config.model,
        provider=provider,
        name=config.name,
        system_prompt=_system_prompt(config),
        temperature=config.temperature,
        top_p=config.top_p,
        max_tokens=config.max_tokens,
        max_retries=config.max_retries,
        timeout_seconds=config.timeout_seconds,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
        pricing=_pricing(config),
        seed=config.seed,
        request_extra=config.request_extra,
    )


def _resolve_local(config: AgentConfig) -> LocalModelAgent:
    if not config.model_name:
        raise ValueError("agent type 'local' requires a non-empty 'model_name' field.")
    device = None if config.device in {None, "auto"} else config.device
    return LocalModelAgent(
        model_name=config.model_name,
        name=config.name,
        system_prompt=_system_prompt(config),
        max_new_tokens=config.max_new_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
        do_sample=config.do_sample,
        device=device,
    )


def _resolve_direct(config: AgentConfig) -> DirectAgent:
    if config.provider or config.model:
        api_config = config.model_copy(update={"type": "api"})
        return _resolve_api(api_config)
    if config.model_name:
        local_config = config.model_copy(update={"type": "local"})
        return _resolve_local(local_config)
    raise ValueError(
        "agent type 'direct' requires either API fields ('provider'/'model') "
        "or local-model fields ('model_name'/'device')."
    )


def _resolve_reflective(
    config: AgentConfig,
    *,
    spec: EnvironmentSpec | None,
) -> ReflectiveAgent:
    if config.backend is not None:
        backend_config = AgentConfig(**config.backend)
    elif config.provider or config.model:
        backend_config = config.model_copy(update={"type": "api", "name": None})
    elif config.model_name:
        backend_config = config.model_copy(update={"type": "local", "name": None})
    else:
        raise ValueError(
            "agent type 'reflective' requires a direct backend, either as "
            "'backend: {type: api|local|direct, ...}' or top-level model fields."
        )

    backend = resolve_agent(backend_config, spec=spec)
    if not isinstance(backend, DirectAgent):
        raise ValueError("reflective agent backend must resolve to a DirectAgent.")
    return ReflectiveAgent(backend=backend, name=config.name)


def _resolve_tool(config: AgentConfig, *, spec: EnvironmentSpec | None) -> ToolAgent:
    if spec is None:
        raise ValueError("agent type 'tool' requires an environment spec.")
    policy = (config.tool_policy or "reference").lower().strip()

    if policy == "reference":
        return ReferenceToolAgent(
            environment=spec.name,
            family=spec.family,
            reference_solver=spec.reference_solver,
            name=config.name,
            allowed_tools=config.allowed_tools,
            max_steps=config.tool_max_steps,
        )
    if policy in {"model", "api", "local"}:
        client = _build_tool_client(config)
        return ModelToolAgent(
            client,
            environment=spec.name,
            family=spec.family,
            name=config.name,
            allowed_tools=config.allowed_tools,
            max_steps=config.tool_max_steps,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            seed=config.seed,
            require_tool_first=config.require_tool_first,
            request_extra=config.request_extra,
        )
    raise ValueError(
        f"unknown tool_policy {config.tool_policy!r}. Expected one of: reference, model."
    )


def _resolve_small_transformer(config: AgentConfig) -> SmallTransformerAgent:
    checkpoint_path = config.checkpoint_path or config.model_name
    if not checkpoint_path:
        raise ValueError("agent type 'small_transformer' requires 'checkpoint_path'.")
    return SmallTransformerAgent(
        checkpoint_path,
        device=config.device or "cpu",
        name=config.name or "small_transformer",
    )


def _build_tool_client(config: AgentConfig) -> Any:
    from mimirbench.agents.providers import HFLocalClient, build_api_client

    if config.model_name and not config.model:
        device = None if config.device in {None, "auto"} else config.device
        return HFLocalClient(
            config.model_name,
            device=device or "auto",
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            do_sample=config.do_sample,
        )
    if not config.model:
        raise ValueError(
            "model-backed tool agent requires a 'model' (API) or 'model_name' (local) field."
        )
    return build_api_client(
        (config.provider or "openai").lower().strip(),
        config.model,
        base_url=config.base_url,
        timeout_s=config.timeout_seconds,
        retry=RetryConfig(max_retries=config.max_retries),
        pricing=_pricing(config),
        api_key_env=config.api_key_env,
    )
