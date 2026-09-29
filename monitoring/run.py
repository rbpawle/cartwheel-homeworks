"""Homework 7: sample and judge one monitoring period.

    uv run python -m monitoring.run --period before
    uv run python -m monitoring.run --period after [--yes]
    uv run python -m monitoring.run --last-hours 24   # the scheduled job

One period is a UTC time window from ``monitoring/config.json`` that must hold
one complete run of the 50 scenarios in ``scenarios/monitoring_scenarios.jsonl``
on the configured Cartwheel model. A Langfuse trace is one user turn, so the
traces are grouped by scenario into 50 conversation records. Each record is
identified by its final trace id so Langfuse can attach the score to it.

The random sample and the risk groups are judged together once, but their
verdicts are saved separately: only the random verdicts estimate prevalence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analysis.helpers.normalization import _flatten, normalize_trace
from analysis.run_judges import _name_tools
from monitoring.chart import prevalence_chart
from monitoring.correct import corrected_mode_prevalence
from monitoring.sample import DEFAULT_RISK_GROUPS, select_traces
from monitoring.write_scores import build_score_records, post_scores
from observability.instrument import load_env

REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "monitoring" / "config.json"
SCENARIOS_PATH = REPO / "scenarios" / "monitoring_scenarios.jsonl"
OUTPUT_DIR = REPO / "monitoring" / "output"
HISTORY_PATH = REPO / "monitoring" / "history.jsonl"
CHART_PATH = REPO / "monitoring" / "prevalence.svg"


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_period(config: dict[str, Any], label: str) -> dict[str, Any]:
    for period in config["periods"]:
        if period["label"] == label:
            return period
    raise ValueError(f"no period labeled {label!r} in {CONFIG_PATH.name}")


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp {value!r} needs an explicit UTC offset")
    return parsed


def monitoring_scenario_ids(path: Path = SCENARIOS_PATH) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {json.loads(line)["id"] for line in lines if line.strip()}


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


def fetch_window(start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Every Langfuse trace in [start, end], fully fetched and normalized."""
    from analysis.helpers import langfuse_io

    lf = langfuse_io._client()
    summaries: list[Any] = []
    page = 1
    while True:
        response = lf.api.trace.list(
            page=page, limit=100, from_timestamp=start, to_timestamp=end
        )
        batch = list(response.data or [])
        summaries.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    # List responses omit observations, so fetch each full trace.
    return [normalize_trace(lf.api.trace.get(summary.id)) for summary in summaries]


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------


def _tool_names(messages: list[dict[str, Any]]) -> list[str]:
    names = [m.get("name") for m in messages if m.get("role") == "tool_call"]
    return list(dict.fromkeys(str(name) for name in names if name))


def build_conversations(
    traces: list[dict[str, Any]], scenario_ids: set[str], model: str
) -> list[dict[str, Any]]:
    """Group one period's traces into one record per monitoring scenario.

    Rejects the period when a scenario is missing, an eligible trace used a
    different model, or a scenario spans several sessions (separate retries).
    """
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        scenario = trace["meta"].get("scenario_id")
        if scenario in scenario_ids:
            by_scenario[scenario].append(trace)

    missing = sorted(scenario_ids - set(by_scenario))
    if missing:
        raise ValueError(f"period is missing {len(missing)} scenario ids: {missing[:5]}")
    _check_model(by_scenario, model)
    retried = sorted(
        scenario
        for scenario, group in by_scenario.items()
        if len({trace["meta"].get("session_id") for trace in group}) != 1
    )
    if retried:
        raise ValueError(f"scenarios span several sessions (retries?): {retried[:5]}")
    return [
        _conversation(by_scenario[scenario], scenario_id=scenario)
        for scenario in sorted(by_scenario)
    ]


def build_session_conversations(
    traces: list[dict[str, Any]], model: str
) -> list[dict[str, Any]]:
    """Group a rolling window's traces into one record per Cartwheel session.

    Traces without a session id are not conversations and are skipped.
    """
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        session = trace["meta"].get("session_id")
        if session:
            by_session[session].append(trace)
    _check_model(by_session, model)
    return [
        _conversation(by_session[session], session_id=session)
        for session in sorted(by_session)
    ]


def _check_model(groups: dict[str, list[dict[str, Any]]], model: str) -> None:
    wrong_model = sorted(
        trace["trace_id"]
        for group in groups.values()
        for trace in group
        if trace["models"] != [model]
    )
    if wrong_model:
        raise ValueError(f"traces not on {model}: {wrong_model[:5]}")


def _conversation(traces: list[dict[str, Any]], **keys: str) -> dict[str, Any]:
    """One conversation record, identified by its final trace id."""
    group = sorted(traces, key=lambda t: t.get("timestamp") or "")
    messages = [m for trace in group for m in trace["trace"]]
    # Same rendering as the Homework 5 judge inputs: tool names folded
    # into their payloads, then flattened. No labels or scenario metadata.
    text = _flatten([m for trace in group for m in _name_tools(trace["trace"])])
    return {
        "id": group[-1]["trace_id"],
        **keys,
        "trace_ids": [trace["trace_id"] for trace in group],
        "tools": _tool_names(messages),
        "turn_count": sum(m.get("role") == "user" for m in messages),
        "text": text,
    }


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def _confirm(prompt: str) -> bool:
    # A scheduled job has no terminal to answer; the counts are still printed.
    if not sys.stdin.isatty():
        return True
    return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}


def _save_output(result: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{result['label']}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"  saved {out_path.relative_to(REPO)}")
    return out_path


def run_period(label: str, assume_yes: bool = False) -> dict[str, Any] | None:
    config = load_config()
    period = find_period(config, label)
    start, end = _utc(period["from"]), _utc(period["to"])

    traces = fetch_window(start, end)
    conversations = build_conversations(
        traces, monitoring_scenario_ids(), config["model"]
    )
    eligible = sum(
        1 for trace in traces if trace["meta"].get("scenario_id") in monitoring_scenario_ids()
    )
    print(f"period {label}: {start.isoformat()} to {end.isoformat()}")
    result = monitor(config, label, period["from"], period["to"], eligible, conversations, assume_yes)
    if result is not None:
        write_history(history_record(result))
        write_chart(config)
    return result


def run_last_hours(hours: float, assume_yes: bool = False) -> dict[str, Any] | None:
    """Monitor the rolling window that ends now, grouped by session."""
    config = load_config()
    end = datetime.now(timezone.utc).replace(microsecond=0)
    start = end - timedelta(hours=hours)
    label = f"last{hours:g}h-{end:%Y-%m-%dT%H%MZ}"

    traces = fetch_window(start, end)
    conversations = build_session_conversations(traces, config["model"])
    eligible = sum(len(c["trace_ids"]) for c in conversations)
    print(f"window {label}: {start.isoformat()} to {end.isoformat()}")
    if not conversations:
        print("  no eligible conversations; judge not called")
        _save_output(
            {
                "label": label,
                "from": start.isoformat(),
                "to": end.isoformat(),
                "judge_id": config["judge_id"],
                "model": config["model"],
                "counts": {"langfuse_traces": len(traces), "conversations": 0},
            }
        )
        return None
    return monitor(
        config, label, start.isoformat(), end.isoformat(), eligible, conversations, assume_yes
    )


def monitor(
    config: dict[str, Any],
    label: str,
    start: str,
    end: str,
    eligible: int,
    conversations: list[dict[str, Any]],
    assume_yes: bool,
) -> dict[str, Any] | None:
    """Sample, judge, correct, and score one batch of conversations."""
    unknown = set(config["risk_groups"]) - set(DEFAULT_RISK_GROUPS)
    if unknown:
        raise ValueError(f"unknown risk groups: {sorted(unknown)}")
    risk_groups = {name: DEFAULT_RISK_GROUPS[name] for name in config["risk_groups"]}
    plan = select_traces(conversations, config["random_rate"], risk_groups)

    print(f"  Langfuse traces: {eligible}, conversations: {len(conversations)}")
    print(f"  random sample: {len(plan['random'])}")
    for name, group in plan["risk_groups"].items():
        print(f"  risk group {name}: {len(group)}")
    print(f"  judge: {config['judge_id']}, judge calls: {len(plan['to_judge'])}")
    if not assume_yes and not _confirm("Run the judge?"):
        print("stopped before judging")
        return None

    from monitoring.run_judges import judge_sample, judge_test_data

    verdicts = judge_sample(config["judge_id"], plan["to_judge"])
    random_verdicts = {t["id"]: verdicts[t["id"]] for t in plan["random"]}
    risk_ids = dict.fromkeys(
        t["id"] for group in plan["risk_groups"].values() for t in group
    )
    risk_verdicts = {trace_id: verdicts[trace_id] for trace_id in risk_ids}

    # Only the random verdicts estimate prevalence; the risk groups are biased.
    test_labels, test_preds = judge_test_data(config["judge_id"])
    estimate = corrected_mode_prevalence(
        list(random_verdicts.values()), test_labels, test_preds
    )

    result = {
        "label": label,
        "from": start,
        "to": end,
        "judge_id": config["judge_id"],
        "judge_mode": config["judge_mode"],
        "model": config["model"],
        "counts": {
            "langfuse_traces": eligible,
            "conversations": len(conversations),
            "random_sample": len(plan["random"]),
            "risk_sample": len(risk_verdicts),
            "judge_calls": len(plan["to_judge"]),
        },
        "conversation_by_trace": {
            c["id"]: c.get("scenario_id") or c.get("session_id") for c in conversations
        },
        "risk_groups": {
            name: [t["id"] for t in group] for name, group in plan["risk_groups"].items()
        },
        "random_verdicts": random_verdicts,
        "risk_verdicts": risk_verdicts,
        "estimate": estimate,
    }
    print(f"  random flagged: {sum(random_verdicts.values())}/{len(random_verdicts)}")
    print(f"  risk flagged: {sum(risk_verdicts.values())}/{len(risk_verdicts)}")
    print(
        f"  raw {estimate['raw']}, corrected {estimate['corrected']} "
        f"(95% CI {estimate['ci_low']}-{estimate['ci_high']})"
    )
    _save_output(result)

    records = build_score_records(
        config["judge_mode"], random_verdicts, risk_verdicts, estimate, label
    )
    for record in records:
        if record["trace_id"] is None:
            record["session_id"] = f"monitor-{label}"
    print(f"  wrote {post_scores(records)} Langfuse scores")
    return result


# ---------------------------------------------------------------------------
# history and chart
# ---------------------------------------------------------------------------


def history_record(result: dict[str, Any]) -> dict[str, Any]:
    counts, estimate = result["counts"], result["estimate"]
    return {
        "label": result["label"],
        "from": result["from"],
        "to": result["to"],
        "judge_id": result["judge_id"],
        "model": result["model"],
        "langfuse_traces": counts["langfuse_traces"],
        "conversations": counts["conversations"],
        "random_sample": counts["random_sample"],
        "risk_sample": counts["risk_sample"],
        "raw": estimate["raw"],
        "corrected": estimate["corrected"],
        "ci_low": estimate["ci_low"],
        "ci_high": estimate["ci_high"],
        "confidence": estimate["confidence"],
        "failure_sensitivity": estimate["failure_sensitivity"],
        "pass_specificity": estimate["pass_specificity"],
    }


def read_history(path: Path = HISTORY_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def write_history(record: dict[str, Any], path: Path = HISTORY_PATH) -> None:
    """Keep one line per period: a rerun replaces that period's line."""
    rows = [row for row in read_history(path) if row["label"] != record["label"]]
    rows.append(record)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    print(f"  updated {path.relative_to(REPO)}")


def write_chart(config: dict[str, Any], path: Path = CHART_PATH) -> None:
    """Chart every recorded period, configured periods first, in config order."""
    order = {period["label"]: i for i, period in enumerate(config["periods"])}
    rows = sorted(read_history(), key=lambda row: (order.get(row["label"], len(order)), row["from"]))
    svg = prevalence_chart(rows, threshold=config["threshold"], mode=config["judge_mode"])
    path.write_text(svg, encoding="utf-8")
    print(f"  updated {path.relative_to(REPO)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Homework 7: monitor one period.")
    window = parser.add_mutually_exclusive_group(required=True)
    window.add_argument("--period", help="a period label from config.json")
    window.add_argument("--last-hours", type=float, help="monitor the window ending now")
    parser.add_argument("--yes", action="store_true", help="skip the judge confirmation")
    args = parser.parse_args()
    load_env()
    if args.period:
        run_period(args.period, assume_yes=args.yes)
    else:
        run_last_hours(args.last_hours, assume_yes=args.yes)


if __name__ == "__main__":
    main()
