"""Homework 5: judge inputs and label splits for one failure mode.

Part B only. Three steps, each runnable on its own:

    uv run python -m analysis.run_judges prepare   # write the judge inputs
    uv run python -m analysis.run_judges labels    # export labels in HW5 polarity
    uv run python -m analysis.run_judges split     # partition them 20/40/40

Everything reads the committed export at ``traces/support_traces.json`` and the
Homework 4 labels under ``analysis/state/labels/``. Nothing here calls a model.

Two conventions are easy to get backwards, so they are stated once here:

**Polarity.** Homework 4 stores ``1`` for *Fail* (the failure is present).
Homework 5 stores ``1`` for *Pass*. ``analysis.helpers.tools._load_labels``
prefers ``state/hw5_labels/<mode>.jsonl`` when it exists and inverts it back to
the internal failure flag, so the export written here must be in HW5 polarity
and the Homework 4 files must be left alone.

**Granularity.** A Langfuse trace is one user turn; the handout wants one record
per *conversation*. Turns are grouped by scenario id, which is what
``normalize_traces`` does internally, and each conversation contributes exactly
one record anchored on one turn -- see ``_anchor`` for which one.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from analysis.helpers import _state, split_labels
from analysis.helpers.normalization import normalize_trace
from observability.instrument import load_env

REPO = Path(__file__).resolve().parents[1]
EXPORT_PATH = REPO / "traces" / "support_traces.json"
INPUTS_PATH = _state.state_path("hw5_trace_inputs.json")
MODE = "escalation_without_basis"
JUDGE_MODEL = "gpt-4o-mini"
PROMPT_DIR = REPO / "analysis" / "prompts"
REPORT_DIR = REPO / "analysis" / "report"
SEED = 7  # shared by the Pass cap and split_labels, so both draws are reproducible

# Fields a record may carry. Anything else risks handing the judge the answer:
# the trace source is re-normalized at judge time and `trace` becomes the text
# the model reads, so review notes, labels, and scenario metadata stay out.
RECORD_FIELDS = {"trace_id", "trace"}


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------


def _judge_store() -> list[dict[str, Any]]:
    """The judge inputs as the judge will see them, via the documented env var."""
    os.environ.setdefault("CARTWHEEL_JUDGE_TRACE_SOURCE", str(INPUTS_PATH))
    from analysis.helpers.scale import load_store_traces

    return load_store_traces()


def live_labels(mode: str) -> dict[str, int]:
    """The current Homework 4 label per trace (``1`` = failure present).

    Label files are append-only: a flip appends a replacement and marks the old
    record ``superseded_by``. This collapses the log the same way the helpers do.
    """
    rows = _state.read_jsonl(_state.state_path("labels", f"{mode}.jsonl"))
    live: dict[str, int] = {}
    for row in rows:
        if row.get("superseded_by"):
            continue
        if row.get("label") not in (0, 1):
            raise ValueError(f"non-binary label on trace {row.get('trace_id')}")
        live[row["trace_id"]] = int(row["label"])
    return live


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------


def conversations(source: Path = EXPORT_PATH) -> dict[str, list[dict[str, Any]]]:
    """Group the export's traces into conversations, turns in time order.

    Each turn keeps its own trace id and its own normalized message list, which
    a merged record cannot provide: merging hides turn boundaries, and the
    boundary is what decides where a record has to stop.
    """
    raw = json.loads(source.read_text())
    records = raw.get("traces") if isinstance(raw, dict) else raw
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        scenario = (
            record.get("cartwheel_scenario_id")
            or ((record.get("metadata") or {}).get("attributes") or {}).get("cartwheel.scenario_id")
        )
        normalized = normalize_trace(record)
        grouped[scenario or normalized["trace_id"]].append({
            "trace_id": normalized["trace_id"],
            "timestamp": normalized.get("timestamp") or "",
            "messages": normalized["trace"],
        })
    for turns in grouped.values():
        turns.sort(key=lambda t: t["timestamp"])
    return dict(grouped)


def _name_tools(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fold each tool's name into its payload so the flattened text keeps it.

    ``normalization._flatten`` renders a ``tool_call`` from its ``arguments`` and a
    ``tool_result`` from its ``content``, dropping the ``name`` field -- and that
    flattened text is exactly what the judge reads. Left alone, a call with no
    arguments reaches the judge as ``tool_call: {}``, and no trace ever shows
    *which* tool ran. For this failure mode that is the deciding evidence: whether
    the reply offered a handoff is one question, whether ``escalate_to_human`` was
    actually called is the other.
    """
    out: list[dict[str, Any]] = []
    for message in messages:
        role, name = message.get("role"), message.get("name")
        if role not in ("tool_call", "tool_result") or not name:
            out.append(message)
            continue
        key = "arguments" if role == "tool_call" else "content"
        payload = message.get(key)
        named = {"tool": name, **payload} if isinstance(payload, dict) else {"tool": name, key: payload}
        out.append({**message, key: named})
    return out


def _anchor(turns: list[dict[str, Any]], labels: dict[str, int]) -> int | None:
    """Index of the turn whose reply the judge evaluates, or None if unlabeled.

    The label that travels into the split is this turn's label, so the choice
    decides the class balance. A conversation labeled Fail on a later turn would
    silently become a Pass if anchored on its first turn, so prefer the last
    labeled failing turn and otherwise take the last labeled turn.
    """
    labeled = [i for i, turn in enumerate(turns) if turn["trace_id"] in labels]
    if not labeled:
        return None
    failing = [i for i in labeled if labels[turns[i]["trace_id"]] == 1]
    return failing[-1] if failing else labeled[-1]


# ---------------------------------------------------------------------------
# Part B: inputs
# ---------------------------------------------------------------------------


def prepare_inputs(
    mode: str = MODE,
    source: Path = EXPORT_PATH,
    out: Path = INPUTS_PATH,
    max_pass: int | None = None,
) -> dict[str, Any]:
    """Write one judge-input record per labeled conversation.

    A record is ``{"trace_id": ..., "trace": [messages]}``: the anchor turn's
    user request and assistant reply, the earlier turns of the same conversation
    ahead of them, and the tool calls and results (which carry the help-center
    policy passages) in the order they happened.

    Turns *after* the anchor are dropped. A later user turn often reacts to the
    reply under judgment -- correcting it, or accepting it -- which would tell
    the judge the answer.

    ``max_pass`` caps the Pass class, keeping every Fail. The kept Passes are
    drawn with a fixed seed rather than chosen by content: picking which Passes
    to keep on any property of the conversation would bias the evaluation set
    toward cases the judge finds easy or hard.
    """
    labels = live_labels(mode)
    records, skipped, anchors = [], [], {}
    for scenario, turns in sorted(conversations(source).items()):
        index = _anchor(turns, labels)
        if index is None:
            continue
        messages: list[dict[str, Any]] = []
        for turn in turns[: index + 1]:
            messages.extend(_name_tools(turn["messages"]))
        anchor = turns[index]
        if not messages:
            skipped.append(scenario)
            continue
        records.append({"trace_id": anchor["trace_id"], "trace": messages})
        anchors[anchor["trace_id"]] = {
            "scenario": scenario,
            "turns_kept": index + 1,
            "turns_total": len(turns),
        }

    dropped = 0
    if max_pass is not None:
        passes = [r for r in records if labels[r["trace_id"]] == 0]
        if len(passes) > max_pass:
            keep = set(random.Random(SEED).sample([r["trace_id"] for r in passes], max_pass))
            records = [r for r in records if labels[r["trace_id"]] == 1 or r["trace_id"] in keep]
            dropped = len(passes) - max_pass
            anchors = {tid: a for tid, a in anchors.items() if tid in {r["trace_id"] for r in records}}

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2) + "\n")

    labeled_conversations = sum(
        1 for turns in conversations(source).values() if _anchor(turns, labels) is not None
    )
    fails = sum(1 for r in records if labels[r["trace_id"]] == 1)
    return {
        "mode": mode,
        "path": str(out),
        "records": len(records),
        "labeled_conversations": labeled_conversations,
        "fail": fails,
        "pass": len(records) - fails,
        "truncated": sum(1 for a in anchors.values() if a["turns_kept"] < a["turns_total"]),
        "passes_dropped_to_cap": dropped,
        "skipped": skipped,
        "anchors": anchors,
    }


def check_inputs(mode: str = MODE, path: Path = INPUTS_PATH) -> dict[str, Any]:
    """Verify the saved inputs before anything is spent on a judge run."""
    records = json.loads(path.read_text())
    labels = live_labels(mode)
    ids = [r["trace_id"] for r in records]

    problems: list[str] = []
    if len(ids) != len(set(ids)):
        problems.append("duplicate trace ids in the inputs")
    unlabeled = [i for i in ids if i not in labels]
    if unlabeled:
        problems.append(f"{len(unlabeled)} records have no label: {unlabeled[:3]}")
    for record in records:
        extra = set(record) - RECORD_FIELDS
        if extra:
            problems.append(f"record {record['trace_id']} carries {sorted(extra)}")
            break
        if not record["trace"] or record["trace"][-1].get("role") != "assistant":
            problems.append(f"record {record['trace_id']} does not end on an assistant reply")
            break

    # One record per conversation: duplicate runs of one scenario would show up
    # as two records whose message text is identical.
    texts: dict[str, str] = {}
    for record in records:
        key = json.dumps(record["trace"], sort_keys=True)
        if key in texts:
            problems.append(f"records {texts[key]} and {record['trace_id']} have identical traces")
            break
        texts[key] = record["trace_id"]

    covered = set(ids)
    missing_labels = [t for t in labels if t not in covered]
    fails = sum(1 for i in ids if labels.get(i) == 1)
    return {
        "records": len(records),
        "fail": fails,
        "pass": len(ids) - fails,
        "labeled_traces_not_anchored": len(missing_labels),
        "problems": problems or ["none"],
    }


# ---------------------------------------------------------------------------
# Part B: labels in Homework 5 polarity
# ---------------------------------------------------------------------------


def export_hw5_labels(mode: str = MODE, path: Path = INPUTS_PATH) -> dict[str, Any]:
    """Write ``state/hw5_labels/<mode>.jsonl`` with ``1`` for Pass, ``0`` for Fail.

    Only the anchored traces are exported, so the label file and the judge inputs
    describe the same conversations. The Homework 4 file is not touched.
    """
    records = json.loads(path.read_text())
    labels = live_labels(mode)
    rows = [
        {
            "trace_id": record["trace_id"],
            "label": 1 - labels[record["trace_id"]],  # HW4 Fail=1 -> HW5 Pass=1
            "source": "human",
            "label_id": f"{record['trace_id']}#{mode}",
        }
        for record in records
    ]
    target = _state.state_path("hw5_labels", f"{mode}.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    _state.write_jsonl(target, rows)
    return {
        "path": str(target),
        "rows": len(rows),
        "pass_1": sum(1 for r in rows if r["label"] == 1),
        "fail_0": sum(1 for r in rows if r["label"] == 0),
    }


# ---------------------------------------------------------------------------
# Part B: the split
# ---------------------------------------------------------------------------


def split_data(mode: str = MODE, path: Path = INPUTS_PATH) -> dict[str, Any]:
    """Partition the labels 20/40/40 and report the class counts per split.

    ``split_labels`` partitions each class separately, so every split inherits
    the same Pass/Fail ratio. It writes ``state/splits.json`` under this mode's
    key, leaving other modes alone. Run it once: re-running with different labels
    would move traces between development and test.
    """
    records = json.loads(path.read_text())
    splits = split_labels(
        mode,
        fractions=(0.20, 0.40, 0.40),
        seed=7,
        min_per_class=10,
        eligible_trace_ids=[record["trace_id"] for record in records],
    )
    labels = live_labels(mode)
    counts = {
        name: {
            "n": len(ids),
            "fail": sum(1 for i in ids if labels.get(i) == 1),
            "pass": sum(1 for i in ids if labels.get(i) == 0),
        }
        for name, ids in splits.items()
    }
    return {"mode": mode, **counts}


# ---------------------------------------------------------------------------
# Part C: development runs
# ---------------------------------------------------------------------------


def _existing_judge(mode: str, prompt_text: str) -> str | None:
    """A registered judge for this exact (prompt, model), if one exists.

    A run that dies after ``register_judge`` leaves a version behind with no
    predictions. Reusing it keeps the version numbers meaning "prompt revisions"
    rather than "attempts", and its cached predictions make a resume free.
    """
    from analysis.helpers.tools import _prompt_hash

    wanted = _prompt_hash(prompt_text, JUDGE_MODEL)
    for path in sorted(_state.state_path("judges").glob(f"{mode}-v*.json")):
        judge = json.loads(path.read_text())
        if judge.get("prompt_hash") == wanted:
            return judge["judge_id"]
    return None


def dev_plan(mode: str = MODE, prompt_path: Path | None = None) -> dict[str, Any]:
    """What a development run would cost, without registering or calling anything."""
    prompt_path = prompt_path or PROMPT_DIR / f"{mode}-v0.txt"
    ids = json.loads(_state.state_path("splits.json").read_text())[mode]["dev"]
    store = {t["trace_id"]: t for t in _judge_store()}
    trace_chars = sum(len(store[t]["text"]) for t in ids if t in store)
    prompt_chars = len(prompt_path.read_text())
    return {
        "prompt": str(prompt_path),
        "model": JUDGE_MODEL,
        "traces": len(ids),
        "calls": len(ids),
        "approx_input_tokens": (trace_chars + prompt_chars * len(ids)) // 4,
    }


def run_test(judge_id: str, batch_size: int = 10) -> dict[str, Any]:
    """Freeze one judge version and score the held-out test split, once.

    Freezing is one-way per version: it locks the prompt and unlocks ``test``,
    and a later fix means registering a new version, which re-locks test. That is
    the whole point of the split, so this is the last step that can be run without
    invalidating the number it produces.
    """
    from analysis.helpers import freeze_judge, judge_alignment, run_judge

    load_env()
    judge = freeze_judge(judge_id)
    run_judge(judge_id, split="test", batch_size=batch_size)
    metrics = judge_alignment(judge_id, split="test")

    report = REPORT_DIR / f"test-{judge_id}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"judge_id": judge_id, "mode": judge["mode"],
                                 "model": judge.get("model"),
                                 "frozen_at": judge.get("frozen_at"),
                                 **metrics}, indent=2) + "\n")
    return {"judge_id": judge_id, "report": str(report), **metrics}


def recalc_dev(mode: str = MODE, judge_id: str | None = None) -> dict[str, Any]:
    """Recompute dev metrics after a label was corrected. No model call.

    A label fixed in the review app lands in the Homework 4 file, but the helpers
    read ``state/hw5_labels/`` when it exists, so the export is rewritten first or
    the metrics would still be scored against the old label. Predictions are cached
    per (prompt hash, trace id) and the prompt has not changed, so nothing is sent.
    """
    from analysis.helpers import judge_alignment

    export_hw5_labels(mode)
    judge_id = judge_id or _existing_judge(
        mode, (PROMPT_DIR / f"{mode}-v0.txt").read_text())
    metrics = judge_alignment(judge_id, split="dev")
    report = REPORT_DIR / f"dev-{judge_id}.json"
    report.write_text(json.dumps({"judge_id": judge_id, "mode": mode,
                                 "model": JUDGE_MODEL, **metrics}, indent=2) + "\n")
    return {"judge_id": judge_id, "report": str(report), **metrics}


def run_development(
    mode: str = MODE,
    prompt_path: Path | None = None,
    batch_size: int = 10,
) -> dict[str, Any]:
    """Register the prompt as a new judge version, score dev, save the metrics.

    Each call registers a new version, so the prompt on disk and the judge id in
    the metrics file always describe the same text.
    """
    from analysis.helpers import judge_alignment, register_judge, run_judge

    # _backend() reads os.environ, and the key lives in .env; without this the
    # run registers a version and then fails at the scaling boundary.
    load_env()

    prompt_path = prompt_path or PROMPT_DIR / f"{mode}-v0.txt"
    prompt_text = prompt_path.read_text()
    judge_id = _existing_judge(mode, prompt_text) or register_judge(
        mode=mode,
        prompt_text=prompt_text,
        judge_model=JUDGE_MODEL,
    )["judge_id"]
    run_judge(judge_id, split="dev", batch_size=batch_size)
    metrics = judge_alignment(judge_id, split="dev")

    report = REPORT_DIR / f"dev-{judge_id}.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"judge_id": judge_id, "mode": mode,
                                 "model": JUDGE_MODEL, "prompt": str(prompt_path),
                                 **metrics}, indent=2) + "\n")
    return {"judge_id": judge_id, "report": str(report), **metrics}


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Homework 5 Part B: inputs and splits.")
    parser.add_argument("step", choices=["prepare", "check", "labels", "split", "dev-plan", "dev", "recalc", "test"])
    parser.add_argument("--mode", default=MODE)
    parser.add_argument("--max-pass", type=int, default=None,
                        help="cap the Pass class; every Fail is kept")
    parser.add_argument("--judge", default=None, help="judge id to freeze and test")
    parser.add_argument("--prompt", type=Path, default=None,
                        help="judge prompt file; defaults to <mode>-v0.txt")
    args = parser.parse_args()

    if args.step == "prepare":
        result = prepare_inputs(args.mode, max_pass=args.max_pass)
        anchors = result.pop("anchors")
        print(json.dumps(result, indent=2))
        multi = {k: v for k, v in anchors.items() if v["turns_total"] > 1}
        print(f"\nmulti-turn conversations: {len(multi)}")
        for tid, info in list(multi.items())[:5]:
            print(f"  {info['scenario']}: kept {info['turns_kept']} of {info['turns_total']} turns")
        print(f'\nexport CARTWHEEL_JUDGE_TRACE_SOURCE="{INPUTS_PATH}"')
    elif args.step == "check":
        print(json.dumps(check_inputs(args.mode), indent=2))
    elif args.step == "dev-plan":
        print(json.dumps(dev_plan(args.mode, args.prompt), indent=2))
    elif args.step == "test":
        if not args.judge:
            raise SystemExit("pass --judge <judge_id>; freezing is one-way, so it is not defaulted")
        print(json.dumps(run_test(args.judge), indent=2))
    elif args.step == "recalc":
        print(json.dumps(recalc_dev(args.mode), indent=2))
    elif args.step == "dev":
        print(json.dumps(run_development(args.mode, args.prompt), indent=2))
    elif args.step == "labels":
        print(json.dumps(export_hw5_labels(args.mode), indent=2))
    else:
        print(json.dumps(split_data(args.mode), indent=2))


if __name__ == "__main__":
    main()
