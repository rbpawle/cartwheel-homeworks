"""Reconstruct the model exchange (request -> response) for one trace.

Langfuse records each model call's request in ``observations.input``, but the
LiteLLM path leaves ``output`` empty, so no step's own response is stored. Every
response is still recoverable, because the next step's request contains it:

    step N+1 request = step N request + [assistant message, tool responses]

The assistant message carries the narration and the tool calls, and the final
step's response is the trace-level output. Anything derived this way is marked
``provenance="reconstructed"`` so a reviewer never mistakes it for a logged value.
"""

from __future__ import annotations

from typing import Any


def _parts(message: dict[str, Any]) -> list[dict[str, Any]]:
    parts = message.get("parts")
    return parts if isinstance(parts, list) else []


def _text(message: dict[str, Any]) -> str:
    return "\n".join(
        str(part.get("content", ""))
        for part in _parts(message)
        if part.get("type") == "text" and part.get("content")
    ).strip()


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": part.get("id"), "name": part.get("name"), "arguments": part.get("arguments")}
        for part in _parts(message)
        if part.get("type") == "tool_call"
    ]


def _messages(value: Any) -> list[dict[str, Any]]:
    return [m for m in value if isinstance(m, dict)] if isinstance(value, list) else []


def _system_prompt(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "system":
            return _text(message)
    return ""


def _summarize(message: dict[str, Any]) -> dict[str, Any]:
    role = message.get("role")
    summary: dict[str, Any] = {"role": role, "text": _text(message)}
    calls = _tool_calls(message)
    if calls:
        summary["tool_calls"] = calls
    responses = [
        {"id": part.get("id"), "response": part.get("response")}
        for part in _parts(message)
        if part.get("type") == "tool_call_response"
    ]
    if responses:
        summary["tool_responses"] = responses
    return summary


def build_steps(observations: list[dict[str, Any]], trace_output: Any) -> dict[str, Any]:
    """Return the per-step exchange for one trace.

    Args:
        observations: normalized observation dicts (``analysis.helpers.normalization``).
        trace_output: the trace-level output, i.e. the final assistant reply.

    Returns:
        ``{"system_prompt": str, "system_prompt_varies": bool, "steps": [...]}`` where each
        step records its request (messages added since the previous step), the response
        recovered for it, and how each side was obtained.
    """
    generations = sorted(
        (o for o in observations if o.get("type") == "GENERATION"),
        key=lambda o: o.get("start_time") or "",
    )
    steps: list[dict[str, Any]] = []
    prompts: set[str] = set()
    previous: list[dict[str, Any]] = []

    for index, generation in enumerate(generations, start=1):
        messages = _messages(generation.get("input"))
        prompts.add(_system_prompt(messages))
        added = messages[len(previous):] if index > 1 else [m for m in messages if m.get("role") != "system"]
        response: dict[str, Any] | None = None
        if index < len(generations):
            following = _messages(generations[index].get("input"))
            for message in following[len(messages):]:
                if message.get("role") == "assistant":
                    response = {
                        "provenance": "reconstructed",
                        "text": _text(message),
                        "tool_calls": _tool_calls(message),
                    }
                    break
        else:
            final = _messages(trace_output)
            response = {
                "provenance": "logged",
                "text": "\n".join(_text(m) for m in final if m.get("role") == "assistant").strip(),
                "tool_calls": [],
            }
        usage = generation.get("usage_details") or {}
        steps.append({
            "step": index,
            "observation_id": generation.get("id"),
            "model": generation.get("model"),
            "latency_seconds": generation.get("latency_seconds"),
            "input_tokens": usage.get("input") or usage.get("total"),
            "message_count": len(messages),
            "request": {"provenance": "logged", "added": [_summarize(m) for m in added]},
            "response": response or {"provenance": "missing", "text": "", "tool_calls": []},
        })
        previous = messages

    return {
        "system_prompt": next(iter(sorted(prompts, key=len, reverse=True)), ""),
        "system_prompt_varies": len({p for p in prompts if p}) > 1,
        "steps": steps,
    }
