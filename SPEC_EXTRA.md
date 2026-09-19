# Specification addendum: observability and review-app changes

Changes made during Homework 4 preparation that are not covered by `SPEC.md`. Each
section states why the change exists, what it touches, and how to verify or recreate it.

Sections 1 to 4 and 7 describe the changes; section 5 records defects found and fixed, and
section 6 the state of the work at the time of writing.

The changes:

1. **Model-exchange visibility** — capture (or recover) the request/response traffic between
   the application and the model, which the Module 1 instrumentation did not store.
2. **Review-app favicon** — a small identity change to the Homework 4 review interface.
3. **Batch sampling and saved sample sets in the review app** — draw a review batch by strategy,
   and return to or delete an earlier batch.
4. **Review-app quality-of-life changes** — selection, popover dismissal, and tool-argument display.
5. **Supporting-annotations table** (section 7) — every open code in one table, with mode linking.

---

## 1. Model-exchange visibility

### 1.1 Problem observed

The Module 1 traces record what the application sent to the model but not what came back.
For every `GENERATION` observation in Langfuse:

- `input` holds the full request: system prompt, message history, tool responses.
- `output` is `NULL`.
- `usage_details` has input tokens only (`{'input': 436, 'total': 436}`); no output tokens, no cost.
- `model_parameters` is `{}`.
- The only span attributes are `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`.
  The `tools` parameter is not recorded.

Cause: OpenLLMetry's OpenAI Agents instrumentor records rich attributes for the native
OpenAI client path. The course models other than `gpt-*` are routed through LiteLLM
(`resolve_model` in `agent/agent.py`), and on that path the response is not captured.

Consequence for error analysis: the model's narration before a tool call is invisible, even
though `SYSTEM_PROMPT_TEMPLATE` requires it ("You MUST explain your reasoning in plain text
before every tool call").

### 1.2 Fix A: record the session id (`server/app.py`)

`post_message`'s docstring requires the request span to record the session id, but the
implementation set only role, user id, prompt version, and scenario id. The Homework 3
reference bundle shows `cartwheel.session_id` present on every trace.

Added beside the other attributes inside the `cartwheel.session_message` span:

```python
span.set_attribute("cartwheel.session_id", session_id)
```

Traces recorded before this change have no session id. The 283 Homework 3 final traces were
backfilled with synthetic values, one per scenario, shared by that scenario's turns:

```python
session_id = hashlib.sha256(f"cartwheel-session::{scenario_id}".encode()).hexdigest()[:32]
```

written through `lf.api.ingestion.batch` with a `trace-create` event carrying the existing
trace id and merged metadata (the ingestion path merges; it does not replace). The mapping is
in `analysis/state/session_map.json`, which also records that the values are synthetic. Any
run after this change records the real session id instead.

### 1.3 Fix B: record the model exchange (`observability/instrument.py`, `server/app.py`)

`record_model_exchange(span, agent, result)` is additive: it creates no spans, replaces no
processors, and writes only to the `cartwheel.*` namespace on the request span. Called from
`post_message` immediately after `Runner.run`:

```python
result = await Runner.run(agent, body.message, context=ctx, session=sqlite_session)
record_model_exchange(span, agent, result)
```

It records three attributes:

| Attribute | Contents |
| --- | --- |
| `cartwheel.tools` | One entry per function tool: `name` and sorted parameter names, from `agent.tools`. |
| `cartwheel.model_settings` | `str(agent.model_settings)`, truncated to 4,000 chars. |
| `cartwheel.model_responses` | One entry per `result.raw_responses`: the output items (type, role, status, text, tool name, arguments, call id) plus `usage` with input, output, and total tokens. Truncated to 120,000 chars. |
| `cartwheel.model_steps` | Number of model calls in the turn. |

Constraints that must hold if this is rewritten:

- Never raise. The whole body is wrapped in `try/except`, logging a warning, because
  instrumentation must not break a request.
- Bound every payload, since span attributes travel with each export.
- Leave existing spans and attributes untouched (Homework 4 Part C requires the existing
  OpenTelemetry and Langfuse instrumentation to be preserved).

Verification, with the server restarted and one request sent:

```sql
SELECT JSONExtractString(metadata['attributes'], 'cartwheel.model_responses')
FROM traces WHERE JSONExtractString(metadata['attributes'], 'cartwheel.scenario_id') = '<id>'
```

Observed on a check run: `cartwheel.model_steps = 2`, nine tool schemas, and per-step output
including `"output_tokens": 73` — the token gap closes for runs made after the change.

### 1.4 Fix C: reconstruct outputs for existing traces (`analysis/review_app/steps.py`)

No rerun is needed to see the exchange on the 283 existing traces, because each model call's
request contains the previous call's output:

```
step N+1 request = step N request + [assistant message, tool responses]
```

`build_steps(observations, trace_output)` sorts the `GENERATION` observations by start time and,
for each step, records:

- **request**: messages added since the previous step (the first step drops the system prompt,
  which is shown once per session), marked `provenance: "logged"`.
- **response**: for step N, the assistant message found in step N+1's request, containing the
  narration text and the tool calls with their ids and arguments, marked
  `provenance: "reconstructed"`. For the final step, the trace-level output, marked `"logged"`.

The tool-call id (`toolu_…`) links a call to its `tool_call_response`.

Limits to preserve if rewritten:

- Never present reconstructed content as logged; the provenance field exists for that.
- Text is the SDK's re-serialization of the message as it re-entered the next request, so
  formatting may differ from the raw completion; content does not.
- A step whose output was dropped from later context would be unrecoverable, and shows as a
  response with no text and no tool call.
- Output tokens and cost remain unrecoverable for these runs.

### 1.5 Fix D: tools and settings from code (`analysis/review_app/toolset.py`)

Tool schemas and model settings are on no trace, but both are deterministic. `tool_schemas()`
reads the function tools from `agent/agent.py` (`name`, description, parameters, required,
full JSON schema) and `model_settings(model)` calls `model_settings_for(resolve_model(model))`.
Both are surfaced as `provenance: "from_code"`, never as recorded evidence. They describe the
code as it stands now, so they are only valid while the agent is unchanged.

### 1.6 Interface surface

`analysis/review_app/server.py` attaches `build_steps(...)` to each turn as `exchange` and serves
`GET /api/toolset`. The UI renders, per turn, a collapsed **model exchange** section: the system
prompt once (badged when it differs between steps), then each step with its request, response,
latency, input tokens, and message count, with `logged` / `reconstructed` / `from_code` badges,
plus a footer noting that output tokens were not recorded for these runs. A session-level panel
lists the tool schemas and model settings.

---

## 2. Review-app favicon

`analysis/review_app/ui/favicon.svg`, linked from `index.html` as
`<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">` and served by the existing
`/static/` route (content type from `mimetypes`).

Design: a 32×32 rounded square (`rx=8`) filled `#fdf5f3` with a `#e6c3bb` 1.5px border, and an X
drawn as two 3.4px round-capped lines in `#a4402f` at 85% opacity. The colours are the app's
existing write-tool and Fail-label palette, so the icon reads as "errors" without the intensity
of a saturated red cross.

---

## 3. Batch sampling and saved sample sets (review app)

### 3.1 Problem observed

The sidebar lists all 250 sessions in scenario order. Homework 4 Part B instead requires four
batches drawn by different methods (uniform, cluster representatives, a product dimension, depth
searches), with no trace counted toward more than one batch. Reading in serial order surfaces only
the most common patterns, which is the failure mode the error-discovery skill warns about.

### 3.2 Server: `POST /api/sample`

Body: `{"strategy": "diversity" | "random" | "outlier", "k": 15, "exclude_reviewed": true}`.
A companion route, `POST /api/sample/delete` with `{"batch_name": ...}`, removes a saved batch.

`sample_batch(...)` in `analysis/review_app/server.py`:

1. Reads the existing `batches` from `sample_manifest.json` **before** anything else, because
   `tools.select_traces` rewrites that file in its own shape (`source`, `k`, `strategy`,
   `selected_at`, `picks`). Reading afterwards silently drops earlier batches.
2. Builds the exclusion set: every trace id already in a batch, plus (when `exclude_reviewed`)
   every trace id in an annotated session. This enforces the handout's rule that a trace counts
   toward one batch only.
3. Calls `tools.select_traces(EXPORT_PATH, k=k, strategy=strategy, exclude_ids=[...])`. The source
   is the Homework 3 export, the same 283 traces the app serves, so selection is fast and offline.
4. Maps the returned trace ids to the sessions containing them and stores the batch under
   `sample_manifest.json` → `batches[<strategy>_<k>]` as
   `{"strategy", "k", "selected_at", "sessions": [{"session_id", "scenario_id", "trace_ids", "reason"}]}`.
   A repeated name gains a numeric suffix.

`progress()` reads batch sizes from that structure, tolerating a bare list of session ids.

### 3.3 UI

Below the existing filters: a strategy dropdown, a size box (default 15), **sample**, and **clear**.
Sampling filters the sidebar to the drawn sessions, shows each pick's reason under its row, and
reports the batch name and size. `clear` restores the full list. The sample acts as one more
predicate in `filtered()`, so it composes with the group, role, intent, reviewed and text filters.

Below that, a **saved samples** dropdown lists every batch in the manifest, newest first, labelled
`<name> · <timestamp> · <session count>`. Selecting one applies it as the sidebar filter, so a
reviewer can return to a set from an earlier session; the batch is the single source, and nothing is
kept in a cookie or in browser storage. (An earlier build had a "copy scenario ids" button here; the
dropdown replaced it.)

The **trash button** deletes the selected set after an inline confirmation that names the set and
states the consequence: its traces become available to future draws again, while annotations and
labels are untouched. Confirming calls `POST /api/sample/delete` with `{"batch_name": ...}`, which
removes that key from `batches` and rewrites the manifest.

Storing the sets server-side rather than client-side is deliberate:
`analysis/state/sample_manifest.json` is a required Homework 4 artifact, batch membership is what
keeps draws disjoint, and cookies would cap out around 4KB and stay on one browser.

### 3.4 Behavior worth knowing

- `outlier` returns only as many traces as the IQR flags; asking for 10 returned 2.
- `diversity` is two thirds cluster representatives and one third random, by `_diversity_picks`
  design. For a strict uniform-versus-cluster split, use `random` for the uniform batch.
- Selection runs on the export's structural features (`turn_count`, `tool_call_count`,
  `distinct_tools`, `has_retrieval`, `tokens`), not on scenario metadata such as role or intent.

---

## 4. Review-app quality-of-life changes

Small interaction fixes in `analysis/review_app/ui/index.html`, all reported while reviewing traces.

**Selection stays visible, and is copyable.** Focusing the note textarea drops the browser's
native selection highlight, so the quoted text disappeared while the reviewer was typing. On
selection the range is now wrapped in `<mark class="ann-mark tmp-hl">`, which keeps the same
highlight, and the mark is unwrapped whenever the popover closes (save, cancel, click away, or
Escape). `range.surroundContents` throws when a selection spans elements, so that path is wrapped
in `try/catch` and falls back to the native highlight.

**Copying the quote.** The popover has a `copy` button, and Cmd/Ctrl+C copies the quote while the
popover is open. The keyboard path defers to the default when the reviewer has selected text inside
the textarea itself (`document.activeElement === textarea && selectionStart !== selectionEnd`),
so copying a draft note still works.

**Dismissing the popover.** `mousedown` outside the popover closes it, and Escape closes it; both
call `closePopover()`, which is the single place that clears `S.sel` and unwraps the highlight.
Previously the cancel button was the only exit.

**Tool-call arguments no longer truncate.** `.tool .call` was a nowrap flex row with
`text-overflow: ellipsis`, which cut off longer argument JSON (for example an `issue_refund` reason
string). The row now wraps and `.tool .args` takes a full-width line with `white-space: pre-wrap`
and `overflow-wrap: anywhere`, so the tool name stays on the first line and the arguments are fully
readable.

---

## 5. Defects found and fixed

**View switching did nothing (CSS specificity).** The nav buttons toggled `.active` correctly, but
`#review { display: grid }` is an id selector (specificity 100) and outranked both
`main { display: none }` and `main.active { display: block }`, so the review pane stayed visible
under every view. The other views did render, below a full-height review pane, which read as "the
tabs do nothing". Fixed by moving the layout onto `#review.active` and adding
`main:not(.active) { display: none !important; }` so no later id rule can reintroduce it.

Worth noting for future work: this class of defect is invisible to the checks run here
(`node --check` on the inline script, and curl against the API), because both the markup and the
JavaScript were correct. Only a browser shows it.

**Supporting-annotations view was missing (unmet requirement, not an enhancement).** Homework 4
Part A requires "a view of the current taxonomy and its supporting annotations". The first build
shipped the mode editor only, and its help text pointed at a linking control in the Labeling view
that did not exist, so `annotation_ids` stayed empty on every mode. Fixed in section 7.

**Saved batches were silently dropped.** `tools.select_traces` rewrites `sample_manifest.json` in
its own shape, so reading the existing `batches` *after* calling it returned a manifest that no
longer had them. Fixed by reading before the call; see section 3.2.

---

## 6. State at the time of writing

Review app: live against Langfuse, 250 sessions / 283 traces, expected results joined from
`scenarios/support_scenarios.jsonl`, model exchange reconstructed per turn, tool schemas from code,
batch sampling with saved sets.

Review progress (from `GET /api/progress`): 17 sessions reviewed, 21 traces, 22 annotations,
5 sample batches recorded, no taxonomy modes yet, no labels, no agent suggestions.

Known gaps, in priority order:

1. **No map or cluster visualization.** Selection is available, coverage is not visible; see
   `analysis/report/interface_comparison.md`.
2. **Suggestions plumbing is unused.** The queue, accept/reject, and promotion to annotation all
   work, but no suggestions have been generated.
3. **`outlier` under-returns** (IQR-flagged traces only) and **`diversity` mixes** cluster
   representatives with random picks; there is no pure-cluster strategy.

---

## 7. Supporting-annotations table (review app)

Added under **Taxonomy**, beside the mode editor, to satisfy the Part A requirement quoted in
section 5 and to give axial coding a working surface.

One row per annotation, joined client-side against `/api/sessions`:

| Column | Source |
| --- | --- |
| scenario | `annotation.scenario_id`, linking back to the conversation in the Review view; trace id beneath |
| role / intent | the scenario tuple (`role`, `intent`, `difficulty`) |
| group | `scenario_group`, plus `data_quality_case_id` when set |
| note | the reviewer's open code |
| quote | the highlighted evidence, truncated |
| mode | linked modes as badges with an unlink control, plus a picker to link another |

Filters: free text over note, quote, and scenario id; group; role; and mode, where `unlinked`
isolates annotations not yet attached to any mode — the working queue for axial coding.

Linking writes `annotation_ids` on the mode in `patterns.json`, which is what Homework 4 Part D
means by "the human annotations from which the mode originated". Unlinking removes the id. The
table re-renders after any taxonomy save, so newly created modes appear in the picker immediately.

---

## Files touched

| File | Change |
| --- | --- |
| `server/app.py` | Sets `cartwheel.session_id`; calls `record_model_exchange` after `Runner.run` |
| `observability/instrument.py` | Adds `record_model_exchange` |
| `analysis/review_app/steps.py` | New: per-step exchange reconstruction |
| `analysis/review_app/toolset.py` | New: tool schemas and model settings from code |
| `analysis/review_app/server.py` | Attaches `exchange` per turn; serves `/api/toolset`, `POST /api/sample`, and `POST /api/sample/delete`; batch-aware `progress()` |
| `analysis/review_app/ui/index.html` | Model-exchange and toolset panels; favicon link; sampling controls and saved-samples dropdown; selection, popover, and tool-argument fixes; supporting-annotations table with mode linking; view-switching CSS fix |
| `analysis/review_app/ui/favicon.svg` | New |
| `analysis/state/session_map.json` | Scenario-to-session mapping for the backfilled traces |

Regression checks after these changes: `tests/test_observability.py`, `tests/test_hw_holes.py -k hw2`,
`tests/test_scenario_runner.py`, `tests/test_langfuse_export.py`, `tests/test_normalization_metadata.py`.
