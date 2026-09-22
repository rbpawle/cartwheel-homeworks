# Review app (Homework 4)

Trace review interface for open coding, axial coding, and structured labeling.
Reads the Module 1 traces from Langfuse, groups them into conversations by
`cartwheel.session_id`, and writes annotations, taxonomy, and labels to
`analysis/state/`.

## Run

Start Langfuse first (the app reads traces from it):

```bash
docker compose -f observability/docker-compose.yml up -d
uv run python -m analysis.review_app.server
```

Then open http://127.0.0.1:8020.

The first start pulls every trace from Langfuse (about a minute for 283) and
caches them in `analysis/review_app/.cache/traces.json`, so later starts are
immediate. The Cartwheel server (port 8010) does not need to be running.

### Options

| Flag | Effect |
| --- | --- |
| `--port 8020` | Port to serve on (default 8020). |
| `--refresh` | Re-pull from Langfuse instead of using the cache. Use after a new run. |
| `--offline` | Read `traces/support_traces.json` (the Homework 3 export) instead of Langfuse. |
| `--no-scores` | Save labels to `analysis/state/labels/` only, without writing Langfuse scores. |
| `--limit N` | Cap how many traces to pull. |

## Views

- **Review** — one conversation per session, with tool calls paired to their results.
  Select any text to annotate it; notes appear in the right margin. "No failure observed"
  records a reviewed trace with no failure.
- **Taxonomy** — failure modes: name, binary definition, status, requirement source,
  evaluator type, boundary, positive and close-negative trace ids. A mode counts as final
  once its status is `confirmed`.
- **Labeling** — present/absent per trace for every confirmed mode.
- **Progress** — traces reviewed against the 100 target, batch counts, per-mode
  Fail/Pass counts, and incomplete judgments.
- **Suggestions** — accept/reject queue for agent-proposed annotations, kept separate
  from human notes.

Keyboard: `j` / `k` move between sessions, `e` toggles the expected result.

## What the panels show

- **Expected result** — the answer key from `scenarios/support_scenarios.jsonl`, collapsed
  by default so it does not anchor your reading.
- **Model exchange** — each model call with its request and response. Responses marked
  `reconstructed` were recovered from the next step's request, because the instrumentation
  did not store generation outputs on these runs. The final step's response is `logged`.
- **Tools and model settings** — marked `from code`: neither was recorded on the traces,
  so both come from `agent/agent.py` as it stands now.

## Where state goes

| File | Contents |
| --- | --- |
| `analysis/state/annotations.json` | Free-form notes, one per annotation |
| `analysis/state/patterns.json` | Failure mode taxonomy |
| `analysis/state/labels/<mode>.jsonl` | One human label per trace per mode (1 = failure present) |
| `analysis/state/suggestions.json` | Agent suggestions and accept/reject decisions |
| `analysis/state/sample_manifest.json` | Review batches |

Labels also go to Langfuse as scores named after the mode, unless `--no-scores` is set.

## Troubleshooting

**Startup hangs or fails with `LangfuseNotConfigured`.** Langfuse is not running or the
env is missing. Check `docker compose -f observability/docker-compose.yml ps` and confirm
`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST` are in `.env`. To work
without it: `--offline`.

**"address already in use".** An older instance is still running:
`pkill -f analysis.review_app.server`, or pick another port with `--port`.

**New traces do not appear.** The cache is stale; restart with `--refresh`.

**A label saves but reports a score error.** The local file was written; only the Langfuse
write failed (usually Langfuse being down). Restart it, or run with `--no-scores`.

**Sessions show `scenario:<id>` as the session id.** Those traces predate
`cartwheel.session_id`; grouping falls back to the scenario id, which is equivalent because
the runner opens one session per scenario.

**A trace is missing its expected result.** The join is by scenario id against
`scenarios/support_scenarios.jsonl`. A trace from another run (e.g. a pilot scenario) has no
matching row and shows an empty answer key.
