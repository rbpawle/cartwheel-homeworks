"""The tool schemas and model settings the agent is built with.

Neither is recorded on the Module 1 traces: the generation spans carry only
``gen_ai.operation.name``, ``gen_ai.provider.name`` and ``gen_ai.request.model``.
Both are deterministic, so the review interface can show them from the code, marked
``provenance="from_code"`` rather than presented as logged evidence.
"""

from __future__ import annotations

from typing import Any


def tool_schemas() -> list[dict[str, Any]]:
    """Return one entry per function tool exposed to the model."""
    from agent import agent as agent_module

    out: list[dict[str, Any]] = []
    for name in dir(agent_module):
        tool = getattr(agent_module, name)
        params = getattr(tool, "params_json_schema", None)
        if params is None or not hasattr(tool, "name"):
            continue
        properties = (params or {}).get("properties", {}) or {}
        out.append({
            "name": tool.name,
            "description": (getattr(tool, "description", "") or "").strip(),
            "parameters": sorted(properties.keys()),
            "required": sorted((params or {}).get("required", []) or []),
            "schema": params,
        })
    out.sort(key=lambda entry: entry["name"])
    return out


def model_settings(model_name: str) -> dict[str, Any]:
    """Return the settings `model_settings_for` applies to this model."""
    from agent.agent import model_settings_for, resolve_model

    try:
        settings = model_settings_for(resolve_model(model_name))
    except Exception as exc:  # a missing provider key must not break the UI
        return {"error": f"{type(exc).__name__}: {exc}"}
    fields = {}
    for key in ("reasoning", "verbosity", "include_usage", "extra_args", "temperature", "top_p", "max_tokens"):
        value = getattr(settings, key, None)
        if value is not None:
            fields[key] = value if isinstance(value, (str, int, float, bool, dict, list)) else str(value)
    return fields
