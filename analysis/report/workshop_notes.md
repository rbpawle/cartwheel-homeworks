# Raindrop Workshop notes (Homework 4, Part C)

Nine Cartwheel turns were replayed through a Workshop-instrumented server and inspected at the
execution level. Everything below is a **hypothesis for the reviewer to accept, revise, or reject**,
not a label. Nothing here has been written to the taxonomy.

## Setup

- Capture is opt-in: `CARTWHEEL_RAINDROP=1 uv run uvicorn server.app:app --port 8011`. With the
  variable unset the SDK is never imported and the server behaves exactly as before.
- Existing OpenTelemetry and Langfuse instrumentation was preserved: every replayed turn was
  recorded in Langfuse as well as Workshop.
- Model: `claude-sonnet-5`, the same model as the Module 1 run.
- Scenarios were chosen from ones already annotated, so any state change affects traces already
  reviewed.

## Runs inspected

| Scenario | Workshop run | Role | Tools captured | Model calls |
| --- | --- | --- | --- | --- |
| support-0001 | `fa44dadef626` | shopper | (not captured, see limitation 1) | — |
| support-0028 | `d0875bb761a8` | shopper | (not captured) | — |
| support-0031 | `940327adde87` | shopper | (not captured) | — |
| support-0077 | `97fc0b6ca7ab` | shopper | find_order, search_help_center | 2.7s, 3.6s, 3.0s |
| support-0099 | `afaa111f43d9` | shopper | find_order, search_help_center ×2, get_order | 3.3s, 3.5s, 4.3s |
| support-0012 | `b3ac9cbbe00b` | merchant | search_help_center ×2 | 2.9s, 3.7s |
| support-0017 | `cca39bfe9217` | support | get_order, search_help_center | 2.7s, 2.6s, 3.3s |
| support-0063 | `10d8e01ac6b0` | merchant | get_order | 2.2s, 2.4s |
| support-0184 | `077497b7464e` | merchant | search_products | 2.8s, 3.2s |

## Candidate observations

### C1. Escalation offered where no ESC rule applies (4 of 9 runs)

`support-0017`, `support-0063`, `support-0184`, and `support-0077` each end by offering a human
handoff: "I can escalate this to a human for a closer look", "I can escalate to a human to verify the
payment record". None of these is an ESC-1 to ESC-4 case: they are a shipped-order cancellation, an
already-refunded order, a bad product price, and a post-shipment return question.

Notable in the span tree: **no run actually called `escalate_to_human`.** The offer is text only, so
a code check for the tool would miss every instance.

*Relates to an existing annotation theme rather than adding a new one.*

### C2. Internal identifiers volunteered to shoppers

`support-0001` tells a shopper their order is "order #546 from **store 14**" — an internal store id,
not a store name. `support-0031` and `support-0028` similarly lead with order numbers the user never
supplied.

*Overlaps the reviewer's existing id-leak theme; the store id is a new variant.*

### C3. Answers volunteered beyond the question

`support-0001` was asked where an order was, and the reply adds "Since it's already shipped, I can't
cancel it". `support-0028` adds "that's a mismatch worth…" about a refund the user did not raise.
Nothing in `SPEC.md` forbids this; it is a candidate quality mode rather than a requirement breach.

### C4. Date reasoning without a known current date

`support-0099` says "today's date puts you at about a month out". The agent is never told the current
date (the system prompt has none, and the world is frozen at 2026-07-01). Here it reached the correct
conclusion, and it cross-checked against `refund_eligible`, but the reasoning is unanchored and would
drift if the flag were absent.

*This is the failure mode predicted during Homework 3 scenario design; this is the first observed
instance of the reasoning appearing in a reply.*

### C5. Structural: retrieval before lookup

`support-0099` called `search_help_center` twice and `get_order` after `find_order` — four tool calls
and three model calls for a single return-eligibility question, where the stamped `refund_eligible`
flag from `get_order` answers it directly. Not a correctness failure; a cost and latency observation
that only the span tree makes obvious.

## Case with genuine uncertainty

**`support-0063` — already-refunded order.** The scenario expects `refund_auto_approved`. The replay
found order 9152 already `refunded`, and the agent declined: "This order shows as already refunded —
no duplicate refund is needed here."

Three readings, and I cannot choose between them from the trace alone:

1. **Correct behavior.** Refusing a duplicate refund is right, and `issue_refund` would have returned
   `not_eligible` anyway.
2. **Environment artifact.** The order was refunded by the original Module 1 run, so the replay world
   differs from the one the expected result was written against. The failure, if any, belongs to the
   replay setup, not the agent.
3. **Masked failure.** If the agent would have refunded an eligible order without checking, this run
   cannot show it, because the world no longer permits the write.

Reading 2 is the most likely, and it generalizes: **replays against a mutated database do not test
what the original scenario tested.** A reseed before replaying would isolate the agent's behavior.

## Limitations

1. **The first three runs (support-0001, 0028, 0031) have no span detail.** They were captured before
   the span endpoint was pointed at Workshop, so only the interaction was recorded. Their replies are
   still readable, but tool structure for them comes from Langfuse, not Workshop.
2. **Workshop does not carry tool payloads here.** Spans record names, timings and status; arguments
   and results were read from Langfuse. Structure comes from Workshop, content from Langfuse.
3. **Replayed runs add new Langfuse traces** carrying the same scenario ids as the Module 1 run, with
   new session ids. They appear as additional sessions in the review app after a cache refresh.
4. **Nine runs is a small sample**, deliberately chosen for role and tool coverage rather than
   representativeness. Frequencies here say nothing about rates in the full trace set.

## Decisions

The handout requires a recorded decision for every Workshop suggestion discussed in the final
taxonomy. Pending the reviewer's judgment:

| Observation | Decision | Note |
| --- | --- | --- |
| C1 escalation offers | pending | |
| C2 internal identifiers | pending | |
| C3 volunteered answers | pending | |
| C4 date reasoning | pending | |
| C5 retrieval before lookup | pending | |
