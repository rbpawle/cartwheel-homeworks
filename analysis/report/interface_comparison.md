# Interface comparison

The review interface for Homework 4 is `analysis/review_app/` (server, `steps.py`, `toolset.py`,
`ui/index.html`). The reference interface is `analysis/server.py` with `analysis/ui/index.html`.

> **Pending, for the student to complete.** The handout's Part A asks the reviewer to read 5 to 10
> traces in the standard Langfuse annotation view first and record what makes review slower there.
> That step has not been done, so this file records only what can be substantiated from the code and
> from the traces themselves. The "kept" and "changed" entries below were decided by the coding
> agent from the observed trace structure; the reviewer should confirm or replace them, and add the
> Langfuse-view observations.

## One design kept from the reference interface

**Text-selection annotation with margin notes, and agent suggestions kept visually separate.**

The reference renders each message as an `annotatable` block; selecting text opens a popover, and the
saved note appears in a right-hand column, with agent suggestions styled differently and carrying
accept/dismiss controls. The review app keeps that model unchanged: selection popover, margin notes at
~280px, human notes with a solid left border, suggestions with a dashed border, a muted tint, an
"agent suggestion" tag, and accept/reject buttons.

The reason to keep it: an open code has to be anchored to the exact evidence that produced it ("per
cw-refunds", a tool result line), and the separation of suggestion from annotation is what keeps the
taxonomy human-driven, as the error-discovery skill requires.

The storage design was kept too: a stdlib `ThreadingHTTPServer` with JSON files under
`analysis/state/`, in the formats the Module 2 helpers already read.

## One design changed after inspecting the traces

**Conversations are assembled per session, with each tool call joined to its result and the model
exchange reconstructed underneath.**

What the traces showed:

- Cartwheel records **one trace per user turn**. The 250 final scenarios produced 283 traces: 178
  single-turn, 66 with 2 turns, 6 with 3. Rendering a trace on its own, as the reference does, splits
  72 conversations and hides the tool calls from the earlier turn.
- `tool_call` and `tool_result` arrive as **separate messages**, so the reference's flat message list
  puts the arguments and the result apart, exactly the comparison a reviewer needs for a
  claimed-success failure.
- The **generation spans have no output**: `observations.output` is NULL on every one, because the
  Claude calls route through LiteLLM. The model's narration before a tool call, which the system
  prompt requires, is therefore invisible in both Langfuse and the reference interface.

What changed as a result:

1. **Grouping by `cartwheel.session_id`**, turns in chronological order, each turn labelled with its
   own trace id. (The attribute was missing from the Module 1 runs; `server/app.py` now records it and
   the existing traces were backfilled. See `SPEC_EXTRA.md`.)
2. **Tool call and result in one bordered container**, with a one-line status (`auto_approved`,
   `permission_denied`) and the JSON collapsed, and a heavier border for the three write tools.
3. **A collapsed model exchange per turn**, reconstructing each step's response from the next step's
   request, with `logged` / `reconstructed` / `from_code` provenance badges.
4. **The Homework 3 expected result joined in per scenario**, collapsed behind a keypress so it does
   not anchor the reading.

## One limitation that remains

**No map view: sampling is available, but its result cannot be seen as a shape.**

The reference interface has a map view backed by `/api/graph` and a `graph.json` projection: a 2D
scatter, coloured by cluster, where annotated items stand out and clicking a point opens that trace.
The review app has no projection and no map.

Batch *selection* is covered: a strategy dropdown (diversity, random, outlier) calls
`analysis.helpers.tools.select_traces`, filters the sidebar to the drawn sessions with each pick's
reason, records the batch in `analysis/state/sample_manifest.json`, and excludes traces already drawn
or already annotated so batches stay disjoint. A copy button exports the scenario ids in view.

What is missing is the *visual* part: there is no way to see which regions of the collection have been
covered, which clusters remain untouched, or where an annotated trace sits relative to its neighbours.
A reviewer must infer coverage from the batch counts in the Progress view. Two further gaps in the
same area: `outlier` returns only as many traces as the IQR flags (2 when 10 were requested), and
`diversity` mixes cluster representatives with random picks rather than offering a pure-cluster batch,
so a strict uniform-versus-cluster split needs `random` for the uniform half.

Smaller limitations worth recording:

- **Reconstructed responses are not raw completions.** They are the SDK's re-serialization of the
  assistant message as it re-entered the next request; content matches, formatting may not.
- **Output tokens and cost are missing** for every Module 1 trace and cannot be recovered. Runs made
  after the instrumentation change record them.
- **Tool schemas and model settings are read from the current code**, not from the traces, so they are
  valid only while `agent/agent.py` is unchanged.
- **Labels are per trace, per the handout**, while review happens per session, so a multi-turn
  conversation needs a judgment for each of its traces.
