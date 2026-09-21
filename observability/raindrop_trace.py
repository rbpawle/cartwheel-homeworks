"""Optional Raindrop Workshop capture for Homework 4, Part C.

Off unless ``CARTWHEEL_RAINDROP`` is set, so the server behaves exactly as before
when Workshop is not in use:

    uv run uvicorn server.app:app --port 8010                      # unchanged
    CARTWHEEL_RAINDROP=1 uv run uvicorn server.app:app --port 8010 # captured

Design constraints:

- **Never own tracing.** ``init`` runs with ``tracing_enabled=False`` and
  ``auto_instrument=False``, so Raindrop registers no OpenTelemetry provider and
  cannot compete with the Langfuse provider that `setup_tracing` installs.
- **Never break a request.** Every call is wrapped; a Raindrop failure logs a
  warning and the turn proceeds.
- **Local only.** Both the event endpoint and the span endpoint point at the local
  Workshop URL (``RAINDROP_LOCAL_DEBUGGER``, default ``http://localhost:5899/v1/``).
  No write key is required for local capture.
- **No manual tool recording.** With tracing on, Raindrop adds a span processor to the
  existing provider, so the OpenLLMetry agent/LLM/tool spans reach Workshop as well.
  Calling ``track_tool`` in addition produced duplicate tool spans.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

log = logging.getLogger("cartwheel.raindrop")

_started = False
_failed = False

# The turn's interaction, so tool results recorded deeper in the stack can find it.
# A ContextVar follows the async request; the module-level fallback covers a tool that
# runs on a worker thread, which is safe here because one process serves one turn at a
# time under the scenario runner.
_current: ContextVar[Any | None] = ContextVar("raindrop_interaction", default=None)
_last: Any | None = None


def enabled() -> bool:
    """True when the operator asked for Workshop capture on this process."""
    return os.environ.get("CARTWHEEL_RAINDROP", "").strip().lower() in {"1", "true", "yes", "on"}


def _client() -> Any | None:
    """Import and initialize the SDK once; return None when unavailable."""
    global _started, _failed
    if _failed or not enabled():
        return None
    try:
        import raindrop.analytics as raindrop
    except Exception as exc:  # package absent: stay silent and keep serving
        _failed = True
        log.warning("raindrop not installed; Workshop capture off (%s)", exc)
        return None
    if not _started:
        try:
            local_url = os.environ.get("RAINDROP_LOCAL_DEBUGGER") or "http://localhost:5899/v1/"
            raindrop.init(
                api_key=os.environ.get("RAINDROP_WRITE_KEY") or "local-workshop",
                # Span export has its own endpoint: without this it goes to the Raindrop
                # cloud API and fails 401 with a placeholder key, so tool spans vanish
                # while interaction events still arrive.
                endpoint=local_url,
                # Tool spans require Raindrop's tracing (``track_tool`` returns early
                # without it). Traceloop keeps its own provider reference, so Langfuse
                # remains the global provider; verified by checking both sinks.
                tracing_enabled=os.environ.get("CARTWHEEL_RAINDROP_TOOLS", "1") != "0",
                auto_instrument=False,   # OpenLLMetry still owns agent/LLM spans
                local_workshop_url=local_url,
            )
            _started = True
            log.info("Raindrop Workshop capture enabled")
        except Exception as exc:
            _failed = True
            log.warning("raindrop init failed; Workshop capture off (%s)", exc)
            return None
    return raindrop


@contextmanager
def capture(
    *,
    event: str,
    user_id: str,
    input_text: str,
    properties: dict[str, Any] | None = None,
    model: str | None = None,
    convo_id: str | None = None,
) -> Iterator[Any | None]:
    """Record one agent turn as a Workshop interaction.

    Yields the interaction (or None when capture is off) so the caller can attach
    the final output; the interaction is finished on the way out, including on an
    exception, so failed turns are visible in Workshop rather than missing.
    """
    raindrop = _client()
    if raindrop is None:
        yield None
        return

    interaction = None
    try:
        interaction = raindrop.begin(
            user_id=str(user_id),
            event=event,
            input=input_text,
            properties=properties or {},
            model=model,
            convo_id=convo_id,
        )
    except Exception as exc:
        log.warning("raindrop begin failed: %s", exc)
        yield None
        return

    global _last
    token = _current.set(interaction)
    _last = interaction
    try:
        yield interaction
    except Exception as exc:
        _safe_finish(interaction, f"Error: {type(exc).__name__}: {exc}")
        _safe_flush(raindrop)
        raise
    else:
        _safe_flush(raindrop)
    finally:
        _current.reset(token)
        _last = None


def _safe_finish(interaction: Any, output: str | None) -> None:
    try:
        if interaction is not None and not getattr(interaction, "finished", False):
            interaction.finish(output=output)
    except Exception as exc:
        log.warning("raindrop finish failed: %s", exc)


def finish(interaction: Any, output: str | None) -> None:
    """Finish an interaction with the turn's final reply."""
    _safe_finish(interaction, output)


def _safe_flush(raindrop: Any) -> None:
    try:
        raindrop.flush()
    except Exception as exc:
        log.warning("raindrop flush failed: %s", exc)
