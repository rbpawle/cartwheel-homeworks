# Specification addendum: observability and review-app changes

Behavior not covered by `SPEC.md`: the observability changes to the Cartwheel application and the
full specification of the trace review app. Together with `SPEC.md`, the reference interface
(`analysis/server.py`, `analysis/ui/index.html`), and the Module 2 helpers under
`analysis/helpers/`, this document is meant to be enough to rebuild the review app from scratch.

Each section states why the behavior exists, what it touches, and how to verify it. Section 5
records defects to avoid reintroducing.

The changes:

1. **Model-exchange visibility** — capture (or recover) the request/response traffic between
   the application and the model, which the Module 1 instrumentation did not store, plus the
   opt-in Raindrop Workshop capture (1.7).
2. **Review-app favicon.**
3. **Batch sampling, filtering, and saved batches in the review app** — draw a batch by strategy or
   stratified across a dimension, filter by pasted scenario ids, save the current view as a batch,
   and rename, reapply, or delete a saved one.
4. **Review-app quality-of-life changes** — selection, popover dismissal, tool-argument display,
   keyboard saving, and editable annotations.
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

### 1.7 Optional Raindrop Workshop capture (`observability/raindrop_trace.py`)

Homework 4 Part C inspects runs in Raindrop Workshop, a local trace debugger, while requiring the
existing OpenTelemetry and Langfuse instrumentation to be preserved.

**Opt-in by environment variable**, because `uvicorn` passes no flags to the app:

```bash
uv run uvicorn server.app:app --port 8010                       # unchanged
CARTWHEEL_RAINDROP=1 uv run uvicorn server.app:app --port 8010  # captured
```

`enabled()` reads `CARTWHEEL_RAINDROP`; when unset, `raindrop.analytics` is never imported, `capture()`
yields `None`, and `finish()` is a no-op. The cost when off is one call and a dict literal per turn.

**Call site.** `post_message` wraps `Runner.run` in `raindrop_trace.capture(...)`, passing the user
message as input, the reply as output, and role, store id, scenario id, prompt version, and session id
as properties. The context manager finishes the interaction on the way out, including on an exception,
so failed turns appear in Workshop rather than vanishing.

**Init settings that matter:**

| Setting | Why |
| --- | --- |
| `endpoint=<local workshop url>` | **Span export has its own endpoint.** Without it, interaction events reach local Workshop while spans go to the Raindrop cloud API and fail `401 Unauthorized` — tool spans silently disappear while runs still appear. |
| `local_workshop_url=<same url>` | Event endpoint. `RAINDROP_LOCAL_DEBUGGER`, default `http://localhost:5899/v1/`. |
| `tracing_enabled=True` | `Interaction.track_tool` and span helpers return early without it, so no tool spans. |
| `auto_instrument=False` | OpenLLMetry keeps ownership of agent/LLM/tool instrumentation. |

No write key is needed for local capture; a placeholder is passed.

**Do not also record tools by hand.** With tracing on, Raindrop attaches a span processor to the
existing provider, so the OpenLLMetry spans (`cartwheel.session_message`, `Agent Workflow`, the
generations, and each tool) reach Workshop as well. An earlier build additionally called
`track_tool` from `record_tool_result`, which produced every tool twice (`find_order` and
`find_order.tool`). The manual path was removed.

**Verified:** a captured turn shows the full tree — request span, agent, generations, and tool calls
with durations and status — and the same turn still lands in Langfuse, so the two sinks coexist.

**Limitation:** Workshop's spans carry names, types, timings, and status, but not payloads
(`input_chars` is 0 on tool spans), so tool arguments and results must be read from Langfuse.

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

Two pseudo-batches head the list whenever any batch exists:

- **all batches** — the union of every batch's sessions. Each row's reason is prefixed with the batch
  it came from (`role_30: stratified by role = support`), so membership stays visible while scrolling.
- **not in any batch** — the remainder, for finding material no batch has claimed.

Both are computed in `applyBatch()` from the manifest rather than stored, and both compose with the
other filters: *all batches* plus `needs labels` in the Labeling view is the labeling queue.

The **trash button** deletes the selected set after an inline confirmation that names the set and
states the consequence: its traces become available to future draws again, while annotations and
labels are untouched. Confirming calls `POST /api/sample/delete` with `{"batch_name": ...}`, which
removes that key from `batches` and rewrites the manifest.

Storing the sets server-side rather than client-side is deliberate:
`analysis/state/sample_manifest.json` is a required Homework 4 artifact, batch membership is what
keeps draws disjoint, and cookies would cap out around 4KB and stay on one browser.

### 3.4 Stratified batches (`GET /api/dimensions`, `POST /api/sample/stratified`)

Homework 4 Part B asks for "one product dimension before looking at the outcomes, e.g., user role,
then add 30 traces distributed across its values". Neither `select_traces` strategy does that, so
this is a separate draw.

`GET /api/dimensions` returns, for each dimension, every value with `available` and `total` session
counts. `available` excludes sessions already committed to a batch and (by default) already
annotated, so the table reflects what a new batch could still draw. The dimensions come from the
scenario tuple: `role`, `intent`, `difficulty`, `applicable_policy`, `record_state`, `user_style`,
`scenario_group`, and `turn_count` bucketed as `1 turn` / `2+ turns`.

`POST /api/sample/stratified` takes `{"dimension": "role", "per_value": {"shopper": 10, …}}`. It
samples within each value with a fixed seed, caps each request at what is available and reports the
difference in `shortfalls` rather than failing, and saves the batch in the usual shape with
`strategy: "stratified:<dimension>"`, the `dimension`, the requested `plan`, and a per-session
`reason` of `stratified by <dimension> = <value>`.

UI: a dimension dropdown; on selection, a table of values with `available / total` and an editable
draw count per value, pre-filled with an even split (`floor(30 / number of values)`, capped at
availability); then a button labelled with the running total that draws, saves, applies the batch as
the sidebar filter, and refreshes availability.

The preview shows counts only — no expected results, no annotations, no failure counts — so the
dimension is chosen before outcomes are seen, and the manifest records the dimension, plan, and
timestamp as evidence of that order.

### 3.5 Filtering by scenario id, saving a view as a batch, renaming

**Id filter.** A textarea in the filter section accepts scenario ids separated by commas, tabs,
semicolons, spaces, or newlines, so a column pasted from a spreadsheet works. Bare numbers are
padded (`42` becomes `support-0042`). A note under the box reports how many matched and names the
first few that did not, so typos are visible rather than silent.

**Save what is showing as a batch** (`POST /api/sample/save`). Part B's third batch is a *depth
search*, not a sample: the reviewer retrieves traces with a query (ids, text, dimension) and keeps
the result. `save_manual_batch(name, session_ids, note)` records those sessions with
`strategy: "manual"` and a `note` describing how the view was filtered
(`role: shopper · text:escalate`), so the manifest documents the retrieval instead of implying a
random draw.

**Rename** (`POST /api/sample/rename`). Batches are auto-named from their strategy and size
(`<strategy>_<k>`, `<dimension>_<k>`), which does not survive contact with a real review plan. Rename works from the sidebar and from the
Progress view's batch table; the endpoint rejects an empty name and refuses to overwrite an existing
one, rather than silently merging two batches.

### 3.6 Sidebar layout

Three labelled sections, because the controls do three different jobs:

| Section | Contents | Default |
| --- | --- | --- |
| **Sessions** | attribute filters, text search, id paste, active-filter chips | open |
| **Draw a batch** | by strategy, by dimension, from what is showing now | collapsed |
| **Saved batches** | batch dropdown, rename, delete | collapsed |

The header carries a live `showing N of 250` count. Each active filter appears as a **chip** that
clears itself on click, with a `clear all` when more than one is active; this replaced a `clear`
button that was easy to miss, and it makes an applied batch visible rather than mysterious.

### 3.7 Behavior worth knowing

- `outlier` returns only as many traces as the IQR flags; asking for 10 returned 2.
- `diversity` is two thirds cluster representatives and one third random, by `_diversity_picks`
  design. For a strict uniform-versus-cluster split, use `random` for the uniform batch.
- Selection runs on the export's structural features (`turn_count`, `tool_call_count`,
  `distinct_tools`, `has_retrieval`, `tokens`), not on scenario metadata such as role or intent.
  The stratified draw is the opposite: it works entirely from scenario metadata.
- Even splits are deliberate for stratified draws. Proportional allocation would mirror the
  dataset (145 shopper / 60 merchant / 45 support sessions) and add little over a random sample.

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

**Saving a note with the keyboard.** Enter saves in the annotation popover; Shift+Enter inserts a
newline. Escape and click-away still cancel.

**Editing a saved note.** Each margin note has an `edit` control that swaps the text for a textarea
preloaded with the current note (cursor at the end), with the same key bindings. Saving POSTs the
annotation back with its existing `annotation_id`, so `_save_annotation` replaces the record rather
than appending a second one; `quote`, `trace_id`, and `block_index` are preserved, and the sidebar,
annotations table, and progress counts all refresh. Previously a note could only be deleted and
rewritten, which lost its anchor.

---

## 5. Defects to avoid reintroducing

Each of these was hit during development; the rule after it is what prevents a repeat.

**View switching did nothing (CSS specificity).** The nav buttons toggled `.active` correctly, but
`#review { display: grid }` is an id selector (specificity 100) and outranked both
`main { display: none }` and `main.active { display: block }`, so the review pane stayed visible
under every view. The other views did render, below a full-height review pane, which read as "the
tabs do nothing". The layout belongs on `#review.active`, with
`main:not(.active) { display: none !important; }` so no later id rule can reintroduce it.

**Rule:** `#review` may set `display` only under `.active`. This class of defect passes both
`node --check` on the inline script and any API check, because the markup and the JavaScript are
both correct; only a browser reveals it.

**Taxonomy without its supporting annotations.** Homework 4 Part A requires "a view of the current
taxonomy and its supporting annotations". A mode editor alone does not satisfy it: without a linking
control, `annotation_ids` stays empty on every mode. **Rule:** ship section 7 with the taxonomy view,
and do not describe a control that does not exist.

**A removed element takes the whole page down.** A top-level reference to an element that no longer
exists (`$("#gone").onclick = …`) throws a `TypeError` during script evaluation, so **everything
below it never runs**: nav bindings, `boot()`, every data load. The symptoms look unrelated to the
cause — dead tabs and empty dropdowns.

**Rules:** wrap `boot()` in a `catch` that logs and shows `load failed — see console` in the
sidebar header, so a failure degrades visibly; and after any UI edit, extract every `$("#id")` in
the script and compare against the ids present in the markup and in the render functions. Every
referenced id must exist.

**A save wiped other cards' unsaved edits.** `savePatterns()` re-renders the whole taxonomy from
saved state, so pressing **update mode** on one card discarded in-progress typing in every other
card and greyed out their buttons. **Rule:** any control that re-renders a list of editable cards
must stage unsaved field values outside the DOM and restore them after the render, together with
their dirty state; alternatively, label the control so it clearly saves everything at once.

**A fix placed behind a disabled control.** Trace-id-to-annotation reconciliation was first called
only from the **update mode** click handler. A card whose trace ids were already saved is clean, so
its button is disabled and the reconcile could never run for exactly the state that needed it; the
saved file showed `example_trace_ids` populated with `annotation_ids` empty, and reloading did not
help. **Rule:** when a behavior repairs or derives state, run it where state is written (and once at
startup), not only from a control that may be disabled in the state that needs repairing.

**A field missing from the list payload broke the sidebar.** `labelProgress` read
`session.trace_ids`, which `GET /api/sessions` omitted from its per-row summary. The call threw only
once labels existed to iterate, so the view worked until the first label was recorded and then
stopped: rows stopped responding to clicks (the handlers are bound at the end of `renderRows`, after
the throw) and counters froze. The symptom, "clicking is broken", pointed nowhere near the cause.
**Rules:** a render helper used by the list must only touch fields the list payload actually carries,
and must tolerate a missing field rather than throwing; when a whole pane stops responding, suspect an
exception in its render function before its event wiring.

**Saved batches silently dropped.** `tools.select_traces` rewrites `sample_manifest.json` in its
own shape, so reading the existing `batches` *after* calling it returns a manifest that no longer
has them. **Rule:** read the batches before calling it; see section 3.2.

---

## 6. Deliberately not implemented

- **Map or cluster visualization.** The reference interface has a 2D projection view backed by
  `/api/graph` and `graph.json`. This app has no projection and no map; batch selection covers the
  sampling need, but coverage is not visualizable.
- **Pure-cluster sampling strategy.** `diversity` mixes cluster representatives with random picks
  (see 3.7); no strategy returns representatives only.
- **Agent suggestion generation.** The queue, accept/reject, and promotion to annotation are
  implemented; nothing generates suggestions. They are written to `suggestions.json` by an external
  process or by hand.

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

### 7.1 Taxonomy editor

Modes are edited in the Taxonomy view, above the annotations table. Each mode is a collapsed
`<details>` card whose summary carries `name · status · N positive · N close neg · N notes`, plus an
amber badge naming what Part D still requires (missing definition, missing requirement source, fewer
than three positives). Open cards are remembered across re-renders, so saving one does not collapse
the rest.

Card fields map to the Part D list: name, status (`draft` / `confirmed` / `frozen`), binary
definition, requirement source, evaluator type (`judge` / `code`), boundary, positive trace ids,
close negative trace ids, and a read-only line listing the linked annotations.

Three controls, none of which save silently:

- **create mode** — a name field plus a button. Enter submits, whitespace becomes underscores,
  duplicate names are refused, and the new card opens ready to edit.
- **update mode** — edits are staged, not written per keystroke. Any change enables the button and
  shows `unsaved changes`; clicking it collects that card's fields into the mode and PUTs the whole
  taxonomy. Trace-id fields split on commas, semicolons, or whitespace.
  Saving re-renders every card, so unsaved edits are staged in `S.pending`, keyed by the mode's
  saved name, and written back into the inputs afterwards: the other cards keep their text, stay
  open, keep their enabled button and their `unsaved changes` note. The saved card clears its own
  staging; deleting a mode clears it too, so stale text cannot reappear on a mode that later takes
  the same name.
- **remove mode** — replaces the action row with an inline confirmation naming the mode and stating
  that its annotations survive, with delete and cancel.

### 7.2 Linking annotations to modes

The `mode` column in the annotations table lists every mode twice, as `<name> — positive` and
`<name> — close negative`. One selection records both halves Part D asks for: it appends the
annotation to the mode's `annotation_ids` and the annotation's `trace_id` to either
`example_trace_ids` or `close_negative_trace_ids`, removing it from the opposite list so a trace
cannot sit on both sides. The badge shows which side was recorded; its `×` removes the annotation
and its trace id from both lists.

Trace ids are shown in full and are click-to-copy, in the annotations table (under the scenario
link) and in each turn header in the Review pane; clicking copies the id and flashes `copied`. A
single delegated handler serves every view, so any element carrying `data-copy` works. Ids are
per turn, and an annotation carries the id of the turn it was written on — the same id the mode
card's positive and close-negative fields expect. Copying needs a secure context, which `localhost`
satisfies; the text stays selectable regardless.

**Both directions stay in step.** The dropdown writes the annotation link and the trace id at once.
The reverse is `reconcileAnnotationLinks(mode)`: every trace id in the positive or close-negative
box links *all* annotations written on that trace, and any linked annotation whose trace id is in
neither box is unlinked, so deleting an id from a box also clears the badge in the table. Trace ids
with no annotation are left untouched, because those fields are also meant for traces that were
never annotated.

Reconcile must not be tied to the **update mode** click. It runs over every mode inside
`savePatterns()`, and once at startup after annotations and the taxonomy have loaded, saving only
when something changed. The reason is in section 5: a card whose ids are already saved is clean, so
its button is disabled and the click path is unreachable.

Because the unit is the trace, a trace carrying several notes links all of them. That is usually
correct — they are evidence about the same trace — but the supporting-annotations line can grow
faster than the positive count. Linking a single note out of several is only possible from the
dropdown.

Consequence: close negatives are linked through annotations, so a trace used as a close negative
needs a note on it. That matches the handout's treatment of close negatives as reviewed evidence.
The trace-id fields on the card remain editable for traces that were never annotated.

### 7.3 Addressable state: view and conversation in the URL

The URL names both the active view and the open conversation, so a refresh or a copied link returns
to the same place:

```
/                                       review, first session
/?scenario=support-0123                 review, that conversation
/?view=taxonomy&scenario=support-0123   taxonomy, that conversation still in context
/?view=progress                         progress
```

One function, `syncUrl()`, writes the address bar via `history.replaceState`; it is called when the
view changes and when a session is selected. `review` is the default and is omitted from the query.

On load the app **restores the session first, then the view**, so Labeling and Taxonomy come back
with the right conversation in context rather than the first in the list. An unknown `view` value
falls back to Review; an unknown or absent `scenario` falls back to the first session.

The scenario id in the annotations table is a real link, `/?scenario=<id>` with `target="_blank"`,
so evidence opens in a second tab while the taxonomy stays open in the first.

The server needs no route for any of this: it strips the query string when routing, so
`/?view=taxonomy&scenario=support-0123` serves the same page as `/`.

---

## 8. Labeling view (review app)

Homework 4 Part E needs one present/absent judgment per trace **and** per final mode, which means
reading the conversation while labeling. An earlier build showed only a metadata table for whichever
session the Review view happened to have selected; it could not work through a set.

**Review and Labeling share one workspace.** `show(view)` maps both to the same pane, so there is a
single session list, a single `renderRows`, and a single conversation renderer. What differs:

| | Review | Labeling |
| --- | --- | --- |
| Right rail | margin notes, text-selection annotation | Fail/Pass per trace × mode |
| Default filter | as set by the reviewer | as set by the reviewer |
| Sidebar marker | `●` reviewed / `○` not | `done/total` chip, grey → amber → green |
| Text selection | opens the annotation popover | inactive, so text can be selected freely |

Switching to Labeling does **not** change the filter: a session that reaches `4/4` stays in the list,
the way an annotated session stays in Review. `needs labels` (`done < total`) is available in the
reviewed filter for both views when hiding finished sessions is wanted.

The sidebar marker is a chip rather than a bare count: grey at `0/total`, amber part-way, green when
complete, with tabular figures so the column does not shift as counts fill in.

`renderRail()` dispatches on `S.view` to `renderNotes()` or `renderLabelRail()`; `bindSelection()`
is skipped while labeling. Keep this dispatch rather than duplicating the pane: the duplicate-view
version drifted immediately.

**The rail** renders one block per trace in the session: the trace id (click to copy) and a Fail/Pass
pair per confirmed mode. Only modes with status `confirmed` or `frozen` appear, via the shared
`finalModes()`. The reviewer's own annotations for the session sit below in a collapsed `<details>`,
because the open code is the evidence the judgment rests on. A click writes the label immediately —
local `labels/<mode>.jsonl` plus a Langfuse score — then refreshes the rail, the sidebar counts and
the progress view.

**`labelProgress(session)`** counts recorded judgments against `modes × turns`; it drives both the
sidebar marker and the `needs labels` filter (`done < total`). `needs labels` is offered in Review
too. It therefore needs `trace_ids` on the **list** payload from `GET /api/sessions`, not only on the
per-session response, and it must tolerate missing fields (see section 5).

**Scoring is asynchronous.** `save_label` writes `labels/<mode>.jsonl` synchronously — that file is
the source of truth — and sends the Langfuse score from a worker thread. A synchronous score cost
about one second per click, which is unusable for per-trace-per-mode labeling; the local write is
about 9 ms. Score failures are printed to the server log instead of surfacing in the UI, which is
the deliberate tradeoff for not blocking.

**The expected result stays collapsed behind `e` in both views.** During open coding it would anchor
the reading; during labeling the judgment should follow the mode's definition, not the Homework 3
answer key.

**Not implemented:** digit-key shortcuts for fast labeling. With several traces per session it is
ambiguous which trace a digit should apply to.

---

## Files touched

| File | Change |
| --- | --- |
| `server/app.py` | Sets `cartwheel.session_id`; calls `record_model_exchange` after `Runner.run`; wraps the run in `raindrop_trace.capture` |
| `observability/instrument.py` | Adds `record_model_exchange` |
| `observability/raindrop_trace.py` | New: opt-in Raindrop Workshop capture |
| `pyproject.toml` / `uv.lock` | Adds `raindrop-ai` |
| `analysis/review_app/steps.py` | New: per-step exchange reconstruction |
| `analysis/review_app/toolset.py` | New: tool schemas and model settings from code |
| `analysis/review_app/server.py` | Attaches `exchange` per turn; serves `/api/toolset`, `/api/dimensions`, `POST /api/sample`, `/api/sample/stratified`, `/api/sample/save`, `/api/sample/rename`, and `/api/sample/delete`; batch-aware `progress()` |
| `analysis/review_app/ui/index.html` | Model-exchange and toolset panels; favicon link; three-section sidebar (filters with id paste and chips, draw-a-batch, saved batches); stratified-draw table; selection, popover, and tool-argument fixes; Enter-to-save and editable annotations; supporting-annotations table with mode linking; view-switching CSS fix |
| `analysis/review_app/ui/favicon.svg` | New |
| `analysis/state/session_map.json` | Scenario-to-session mapping for the backfilled traces |

Regression checks after these changes: `tests/test_observability.py`, `tests/test_hw_holes.py -k hw2`,
`tests/test_scenario_runner.py`, `tests/test_langfuse_export.py`, `tests/test_normalization_metadata.py`.
