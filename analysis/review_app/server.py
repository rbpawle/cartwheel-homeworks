"""Review interface for Homework 4 open coding.

Serves one conversation per Cartwheel session (``cartwheel.session_id``), with
its turns in chronological order, each tool call paired with its result, and
the Homework 3 answer key joined in from ``scenarios/support_scenarios.jsonl``.

Trace source
------------
Live Langfuse by default (``analysis.helpers.langfuse_io.fetch_traces``), cached
on disk so a restart is fast. ``--offline`` reads the Homework 3 export instead,
for when Docker is down; the UI shows which source is in use.

Storage
-------
Annotations, taxonomy, suggestions, labels, and the sample manifest live under
``analysis/state/`` in the formats the Module 2 helpers already read. Accepted
labels are also written to Langfuse as scores (one score per mode per trace,
1 = failure present) unless ``--no-scores`` is passed.

Usage
-----
    uv run python -m analysis.review_app.server [--port 8020] [--offline]
        [--refresh] [--no-scores] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import threading
import traceback
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from analysis.helpers import _state
from analysis.review_app.steps import build_steps
from analysis.review_app.toolset import model_settings, tool_schemas

REPO = Path(__file__).resolve().parents[2]
UI_DIR = Path(__file__).resolve().parent / "ui"
CACHE_PATH = Path(__file__).resolve().parent / ".cache" / "traces.json"
SCENARIO_PATH = REPO / "scenarios" / "support_scenarios.jsonl"
RESULTS_PATH = REPO / "scenarios" / "final-results.jsonl"
EXPORT_PATH = REPO / "traces" / "support_traces.json"
SCENARIO_PREFIX = "support-"

_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# loading and shaping
# ---------------------------------------------------------------------------


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def load_from_langfuse(limit: int) -> list[dict[str, Any]]:
    """Pull normalized traces from the live project (one per user turn)."""
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
    from analysis.helpers import langfuse_io

    traces = langfuse_io.fetch_traces(limit=limit)
    return [t for t in traces if str(t["meta"].get("scenario_id", "")).startswith(SCENARIO_PREFIX)]


def load_from_export() -> list[dict[str, Any]]:
    """Read the Homework 3 export and normalize it the same way."""
    from analysis.helpers.normalization import normalize_trace

    payload = json.loads(EXPORT_PATH.read_text())
    out = []
    for raw in payload.get("traces", []):
        trace = normalize_trace(raw)
        if str(trace["meta"].get("scenario_id", "")).startswith(SCENARIO_PREFIX):
            out.append(trace)
    return out


def _session_id(trace: dict[str, Any]) -> str:
    attrs = (trace.get("metadata") or {}).get("attributes", {})
    return (
        attrs.get("cartwheel.session_id")
        # Fallback: traces recorded before server/app.py stamped the session id
        # still group correctly, because the runner opens one session per scenario.
        or f"scenario:{trace['meta'].get('scenario_id')}"
    )


def _pair_tools(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold each tool_call and its tool_result into one block for rendering."""
    blocks: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    for message in messages:
        role = message.get("role")
        if role == "tool_call":
            if pending:
                blocks.append({"kind": "tool", "name": pending.get("name"), "arguments": pending.get("arguments"), "result": None})
            pending = message
            continue
        if role == "tool_result" and pending is not None:
            blocks.append({
                "kind": "tool",
                "name": pending.get("name") or message.get("name"),
                "arguments": pending.get("arguments"),
                "result": message.get("content"),
            })
            pending = None
            continue
        if pending:
            blocks.append({"kind": "tool", "name": pending.get("name"), "arguments": pending.get("arguments"), "result": None})
            pending = None
        blocks.append({"kind": role, "text": message.get("text", ""), "name": message.get("name")})
    if pending:
        blocks.append({"kind": "tool", "name": pending.get("name"), "arguments": pending.get("arguments"), "result": None})
    return blocks


_WRITE_TOOLS = {"issue_refund", "cancel_order", "escalate_to_human"}


def _tool_status(result: Any) -> str:
    if not isinstance(result, dict):
        return "unknown"
    if result.get("ok") is False:
        return str(result.get("error") or "error")
    for key in ("status", "ticket_id", "order_id"):
        if key in result:
            value = result[key]
            return str(value) if key == "status" else f"{key} {value}"
    return "ok"


def build_sessions(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group traces into conversations and join the Homework 3 answer key."""
    scenarios = {s["id"]: s for s in _read_jsonl(SCENARIO_PATH)}
    results = {r["scenario_id"]: r for r in _read_jsonl(RESULTS_PATH)}

    grouped: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        grouped.setdefault(_session_id(trace), []).append(trace)

    sessions = []
    for session_id, group in grouped.items():
        group.sort(key=lambda t: t.get("timestamp") or "")
        scenario_id = group[0]["meta"].get("scenario_id")
        scenario = scenarios.get(scenario_id, {})
        result = results.get(scenario_id, {})
        turns = []
        for index, trace in enumerate(group, start=1):
            blocks = _pair_tools(trace.get("trace") or [])
            for block in blocks:
                if block["kind"] == "tool":
                    block["write"] = block["name"] in _WRITE_TOOLS
                    block["status"] = _tool_status(block.get("result"))
            exchange = build_steps(trace.get("observations") or [], trace.get("output"))
            turns.append({
                "turn": index,
                "trace_id": trace["trace_id"],
                "timestamp": trace.get("timestamp"),
                "models": trace.get("models") or [],
                "blocks": blocks,
                "tool_calls": sum(1 for b in blocks if b["kind"] == "tool"),
                "exchange": exchange,
            })
        tool_calls = sum(turn["tool_calls"] for turn in turns)
        sessions.append({
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_group": scenario.get("scenario_group"),
            "data_quality_case_id": scenario.get("data_quality_case_id"),
            "tuple": scenario.get("tuple", {}),
            "expected": scenario.get("expected", {}),
            "run_status": result.get("status"),
            "trace_ids": [t["trace_id"] for t in group],
            "turns": turns,
            "features": {
                "turn_count": len(turns),
                "tool_calls": tool_calls,
                "distinct_tools": len({b["name"] for turn in turns for b in turn["blocks"] if b["kind"] == "tool"}),
                "chars": sum(len(b.get("text") or "") for turn in turns for b in turn["blocks"]),
            },
        })
    sessions.sort(key=lambda s: s["scenario_id"] or "")
    _flag_outliers(sessions)
    return sessions


def _flag_outliers(sessions: list[dict[str, Any]]) -> None:
    """Badge the top decile for tool calls and length (skill: header badges only)."""
    if not sessions:
        return
    def cut(key: str) -> float:
        values = sorted(s["features"][key] for s in sessions)
        return values[int(len(values) * 0.9)] if values else 0

    tool_cut, char_cut = cut("tool_calls"), cut("chars")
    for session in sessions:
        flags = []
        if session["features"]["tool_calls"] >= max(tool_cut, 1):
            flags.append("tool-heavy")
        if session["features"]["chars"] >= max(char_cut, 1):
            flags.append("long")
        if session["features"]["turn_count"] > 1:
            flags.append(f"{session['features']['turn_count']} turns")
        session["flags"] = flags


# ---------------------------------------------------------------------------
# state files
# ---------------------------------------------------------------------------

STATE_DEFAULTS = {
    "annotations.json": {"annotations": []},
    "patterns.json": {"modes": []},
    "suggestions.json": [],
    "sample_manifest.json": {"batches": {}},
}


def read_state(name: str) -> Any:
    return _state.read_json(_state.state_path(name), STATE_DEFAULTS[name])


def write_state(name: str, payload: Any) -> None:
    _state.write_json(_state.state_path(name), payload)


def label_rows(mode: str) -> list[dict[str, Any]]:
    return _state.read_jsonl(_state.state_path("labels", f"{mode}.jsonl"))


def save_label(mode: str, trace_id: str, label: int, comment: str | None, write_score: bool) -> dict[str, Any]:
    """Upsert one human label, then mirror it to Langfuse as a score."""
    rows = [row for row in label_rows(mode) if row.get("trace_id") != trace_id]
    row = {
        "trace_id": trace_id,
        "label": int(label),
        "source": "human",
        "ts": _utcnow(),
        "label_id": f"{trace_id}#{mode}",
    }
    if comment:
        row["comment"] = comment
    rows.append(row)
    rows.sort(key=lambda r: r["trace_id"])
    _state.write_jsonl(_state.state_path("labels", f"{mode}.jsonl"), rows)

    scored, error = False, None
    if write_score:
        try:
            from analysis.helpers import langfuse_io

            langfuse_io.write_label_score(trace_id, mode, int(label), comment)
            scored = True
        except Exception as exc:  # keep labeling usable when Langfuse is down
            error = f"{type(exc).__name__}: {exc}"
    return {"saved": row, "scored": scored, "score_error": error}


# ---------------------------------------------------------------------------
# sampling
# ---------------------------------------------------------------------------


def sample_batch(strategy: str, k: int, exclude_reviewed: bool) -> dict[str, Any]:
    """Draw a review batch with ``analysis.helpers.tools.select_traces``.

    Selection runs over the Homework 3 export, the same 283 traces the app shows, and
    returns trace ids; the sessions containing them become the sidebar filter. The picks
    are also recorded under ``sample_manifest.json``'s ``batches`` so the progress view can
    track them, without discarding the manifest fields ``select_traces`` writes.
    """
    from analysis.helpers import tools

    # select_traces rewrites sample_manifest.json in its own shape, so read the
    # existing batches before calling it.
    prior = read_state("sample_manifest.json")
    prior_batches = prior.get("batches") if isinstance(prior.get("batches"), dict) else {}

    # The handout counts each trace toward one batch only, so exclude anything already
    # drawn, and (by default) anything already annotated outside a batch.
    exclude = {
        tid
        for batch in prior_batches.values()
        for entry in (batch.get("sessions", []) if isinstance(batch, dict) else [])
        for tid in entry.get("trace_ids", [])
    }
    if exclude_reviewed:
        annotated = {a.get("session_id") for a in read_state("annotations.json")["annotations"]}
        exclude |= {tid for s in State.sessions if s["session_id"] in annotated for tid in s["trace_ids"]}
    exclude = sorted(exclude)

    picks = tools.select_traces(EXPORT_PATH, k=k, strategy=strategy, exclude_ids=list(exclude))
    chosen = {pick["trace_id"] for pick in picks}
    reasons = {pick["trace_id"]: pick["reason"] for pick in picks}

    sessions = [s for s in State.sessions if chosen & set(s["trace_ids"])]
    batch = {
        "strategy": strategy,
        "k": k,
        "selected_at": _utcnow(),
        "sessions": [
            {
                "session_id": s["session_id"],
                "scenario_id": s["scenario_id"],
                "trace_ids": sorted(chosen & set(s["trace_ids"])),
                "reason": reasons[sorted(chosen & set(s["trace_ids"]))[0]],
            }
            for s in sessions
        ],
    }
    manifest = read_state("sample_manifest.json")
    batches = dict(prior_batches)
    name = f"{strategy}_{k}"
    suffix = 2
    while name in batches:
        name, suffix = f"{strategy}_{k}_{suffix}", suffix + 1
    batches[name] = batch
    manifest["batches"] = batches
    write_state("sample_manifest.json", manifest)
    return {"batch_name": name, **batch}


# ---------------------------------------------------------------------------
# progress
# ---------------------------------------------------------------------------


def progress(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    annotations = read_state("annotations.json")["annotations"]
    patterns = read_state("patterns.json")
    manifest = read_state("sample_manifest.json")
    final_modes = [m["name"] for m in patterns.get("modes", []) if m.get("status") in ("confirmed", "frozen")]
    draft_modes = [m["name"] for m in patterns.get("modes", []) if m.get("status") not in ("confirmed", "frozen")]

    annotated = {a.get("session_id") for a in annotations if a.get("session_id")}
    labels = {mode: {row["trace_id"]: row["label"] for row in label_rows(mode)} for mode in final_modes}
    all_trace_ids = [tid for session in sessions for tid in session["trace_ids"]]
    reviewed_trace_ids = {
        tid for session in sessions if session["session_id"] in annotated for tid in session["trace_ids"]
    }

    incomplete = []
    for session in sessions:
        if session["session_id"] not in annotated:
            continue
        missing = [
            {"trace_id": tid, "modes": [m for m in final_modes if tid not in labels[m]]}
            for tid in session["trace_ids"]
        ]
        missing = [entry for entry in missing if entry["modes"]]
        if missing:
            incomplete.append({"session_id": session["session_id"], "scenario_id": session["scenario_id"], "missing": missing})

    batches = {}
    for name, batch in (manifest.get("batches") or {}).items():
        # a batch is {"sessions": [{"session_id", ...}]}; tolerate a bare id list too
        ids = [entry["session_id"] if isinstance(entry, dict) else entry
               for entry in (batch.get("sessions", []) if isinstance(batch, dict) else batch)]
        batches[name] = {"size": len(ids), "reviewed": sum(1 for sid in ids if sid in annotated)}
    mode_counts = {
        mode: {
            "fail": sum(1 for v in labels[mode].values() if v == 1),
            "pass": sum(1 for v in labels[mode].values() if v == 0),
            "labeled": len(labels[mode]),
        }
        for mode in final_modes
    }
    return {
        "sessions_total": len(sessions),
        "sessions_reviewed": len(annotated & {s["session_id"] for s in sessions}),
        "traces_total": len(all_trace_ids),
        "traces_reviewed": len(reviewed_trace_ids),
        "annotations": len(annotations),
        "final_modes": final_modes,
        "draft_modes": draft_modes,
        "mode_counts": mode_counts,
        "incomplete": incomplete,
        "batches": batches,
        "target_traces": 100,
    }


# ---------------------------------------------------------------------------
# http
# ---------------------------------------------------------------------------


class State:
    sessions: list[dict[str, Any]] = []
    source: str = "langfuse"
    loaded_at: str = ""
    write_scores: bool = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter console
        return

    # -- helpers ----------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, status: int = 200) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json")

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    # -- routes -----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        try:
            path = self.path.split("?")[0]
            if path in ("/", "/index.html"):
                return self._send(200, (UI_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
            if path.startswith("/static/"):
                target = UI_DIR / path[len("/static/"):]
                if target.exists():
                    ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                    return self._send(200, target.read_bytes(), ctype)
                return self._json({"error": "not found"}, 404)
            if path == "/api/meta":
                return self._json({
                    "source": State.source,
                    "loaded_at": State.loaded_at,
                    "write_scores": State.write_scores,
                    "sessions": len(State.sessions),
                    "traces": sum(len(s["trace_ids"]) for s in State.sessions),
                })
            if path == "/api/sessions":
                brief = [
                    {k: session[k] for k in ("session_id", "scenario_id", "scenario_group", "data_quality_case_id", "features", "flags", "run_status")}
                    | {"role": session["tuple"].get("role"), "intent": session["tuple"].get("intent"),
                       "difficulty": session["tuple"].get("difficulty"), "user_style": session["tuple"].get("user_style"),
                       "opening": next((b.get("text", "") for turn in session["turns"] for b in turn["blocks"] if b["kind"] == "user"), "")[:140]}
                    for session in State.sessions
                ]
                return self._json(brief)
            match = re.fullmatch(r"/api/sessions/([^/]+)", path)
            if match:
                sid = match.group(1)
                session = next((s for s in State.sessions if s["session_id"] == sid), None)
                return self._json(session or {"error": "not found"}, 200 if session else 404)
            if path in ("/api/annotations", "/api/patterns", "/api/suggestions", "/api/manifest"):
                name = {"annotations": "annotations.json", "patterns": "patterns.json",
                        "suggestions": "suggestions.json", "manifest": "sample_manifest.json"}[path.rsplit("/", 1)[1]]
                return self._json(read_state(name))
            if path == "/api/labels":
                patterns = read_state("patterns.json")
                return self._json({m["name"]: label_rows(m["name"]) for m in patterns.get("modes", [])})
            if path == "/api/toolset":
                model = next((m for s in State.sessions for t in s["turns"] for m in t["models"]), "claude-sonnet-5")
                return self._json({
                    "provenance": "from_code",
                    "note": "tool schemas and model settings are not on the traces; these come from agent/agent.py as it stands now",
                    "model": model,
                    "tools": tool_schemas(),
                    "model_settings": model_settings(model),
                })
            if path == "/api/progress":
                return self._json(progress(State.sessions))
            return self._json({"error": "not found"}, 404)
        except Exception:
            return self._json({"error": traceback.format_exc()}, 500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            path = self.path.split("?")[0]
            body = self._body()
            with _LOCK:
                if path == "/api/annotations":
                    return self._json(self._save_annotation(body))
                if path == "/api/annotations/delete":
                    data = read_state("annotations.json")
                    data["annotations"] = [a for a in data["annotations"] if a.get("annotation_id") != body.get("annotation_id")]
                    write_state("annotations.json", data)
                    return self._json(data)
                if path == "/api/patterns":
                    write_state("patterns.json", body)
                    return self._json(body)
                if path == "/api/suggestions":
                    write_state("suggestions.json", body)
                    return self._json(body)
                if path == "/api/suggestions/accept":
                    return self._json(self._accept_suggestion(body))
                if path == "/api/manifest":
                    write_state("sample_manifest.json", body)
                    return self._json(body)
                if path == "/api/labels":
                    return self._json(save_label(
                        body["mode"], body["trace_id"], int(body["label"]),
                        body.get("comment"), State.write_scores))
                if path == "/api/sample":
                    return self._json(sample_batch(
                        body.get("strategy", "diversity"), int(body.get("k", 15)),
                        bool(body.get("exclude_reviewed", True))))
                if path == "/api/sample/delete":
                    manifest = read_state("sample_manifest.json")
                    batches = manifest.get("batches") or {}
                    removed = batches.pop(body.get("batch_name"), None)
                    manifest["batches"] = batches
                    write_state("sample_manifest.json", manifest)
                    return self._json({"removed": body.get("batch_name") if removed else None,
                                       "batches": batches})
            return self._json({"error": "not found"}, 404)
        except Exception:
            return self._json({"error": traceback.format_exc()}, 500)

    # -- writes -----------------------------------------------------------
    def _save_annotation(self, body: dict[str, Any]) -> dict[str, Any]:
        data = read_state("annotations.json")
        annotation = {
            "annotation_id": body.get("annotation_id") or uuid.uuid4().hex[:12],
            "session_id": body.get("session_id"),
            "trace_id": body.get("trace_id"),
            "scenario_id": body.get("scenario_id"),
            "block_index": body.get("block_index"),
            "quote": body.get("quote", ""),
            "note": body.get("note", ""),
            "ts": _utcnow(),
            "author": "human",
        }
        data["annotations"] = [a for a in data["annotations"] if a.get("annotation_id") != annotation["annotation_id"]]
        data["annotations"].append(annotation)
        write_state("annotations.json", data)
        return annotation

    def _accept_suggestion(self, body: dict[str, Any]) -> dict[str, Any]:
        """Promote an agent suggestion to a human annotation, or dismiss it."""
        suggestions = read_state("suggestions.json")
        target = next((s for s in suggestions if s.get("suggestion_id") == body.get("suggestion_id")), None)
        if target is None:
            return {"error": "unknown suggestion"}
        target["decision"] = body.get("decision", "accepted")
        target["decided_at"] = _utcnow()
        write_state("suggestions.json", suggestions)
        if target["decision"] == "accepted":
            self._save_annotation({
                "session_id": target.get("session_id"), "trace_id": target.get("trace_id"),
                "scenario_id": target.get("scenario_id"), "block_index": target.get("block_index"),
                "quote": target.get("quote", ""),
                "note": f"[accepted agent suggestion] {target.get('note', '')}",
            })
        return target


def load(offline: bool, refresh: bool, limit: int) -> list[dict[str, Any]]:
    if offline:
        State.source = f"export ({EXPORT_PATH.relative_to(REPO)})"
        return build_sessions(load_from_export())
    if CACHE_PATH.exists() and not refresh:
        State.source = "langfuse (cached)"
        return build_sessions(json.loads(CACHE_PATH.read_text()))
    State.source = "langfuse (live)"
    traces = load_from_langfuse(limit)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(traces))
    return build_sessions(traces)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cartwheel trace review interface (HW4).")
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--offline", action="store_true", help="read traces/support_traces.json instead of Langfuse")
    parser.add_argument("--refresh", action="store_true", help="re-pull from Langfuse, ignoring the local cache")
    parser.add_argument("--no-scores", action="store_true", help="save labels locally but do not write Langfuse scores")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    State.write_scores = not args.no_scores
    print(f"loading traces ({'export' if args.offline else 'langfuse'})...")
    State.sessions = load(args.offline, args.refresh, args.limit)
    State.loaded_at = _utcnow()
    traces = sum(len(s["trace_ids"]) for s in State.sessions)
    print(f"{len(State.sessions)} sessions / {traces} traces from {State.source}")
    print(f"http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
