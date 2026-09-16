# HW3 progress note

Working note for the Homework 3 walkthrough (`homework/module-1/hw3.md`). Not a deliverable.

## Working agreement

- The student drives: every command, file change, or generation step waits for an explicit "go".
- Student: dimension design, record selection and expected results (SQL, policy docs), pilot and final review decisions, video.
- Coding agent: writes JSONL and boilerplate from the student's decisions, explains errors, keeps this note current.
- Model for every run: `claude-sonnet-5` (`CARTWHEEL_MODEL` in `.env`; pass `--model claude-sonnet-5` to the runner). Not a course-configured model: routed through LiteLLM as-is, verified by the smoke check. Pilot and final must use the same model. Fallback if the pilot has fewer than 5 failures: a smaller Anthropic model (test on one scenario first).
- Known limitation: Claude generations in Langfuse record input tokens only (no output tokens), so the Part E report undercounts tokens and cost.

## Deliverables ("Files to commit")

- [ ] `scenarios/pilot_scenarios.jsonl`
- [ ] `scenarios/pilot-results.jsonl`
- [ ] `scenarios/pilot_review.jsonl`
- [ ] `scenarios/support_scenarios.jsonl`
- [ ] `scenarios/support_review.jsonl`
- [ ] `scenarios/monitoring_scenarios.jsonl`
- [ ] `scenarios/final-results.jsonl`
- [ ] `reports/smoke-output.txt`
- [ ] `traces/support_traces.json`
- [ ] Video, 5 minutes or less (student)

## Required checks

- [ ] `uv run python -m scenarios.validate scenarios/pilot_scenarios.jsonl` passes
- [ ] Pilot review: at least 10 reviewed, at least 5 confirmed failures
- [ ] Final review: 15 scenarios covering both groups, all 3 roles, every intent; revisions applied, rejects replaced
- [ ] `uv run python -m scenarios.validate scenarios/support_scenarios.jsonl --final` passes (175 coverage / 75 challenge, 5 per damaged record, new IDs)
- [ ] Monitoring set: 50 scenarios, both groups, all 3 roles
- [ ] Final run: all 250 `completed`
- [ ] Export succeeds with 250 unique `cartwheel_scenario_id` values
- [ ] Three exported traces checked (one challenge, one multi-turn)

## Review gates (student decides)

- [x] Dimension plan approved (Part A)
- [ ] Pilot conversation sample accepted before running
- [ ] Pilot review (Part B)
- [ ] Final 15-scenario review (Part C)

## Approved dimension plan (Part A)

Approved by the student as written.

| # | Dimension | Values | Why (source) |
| --- | --- | --- | --- |
| 1 | `role` | shopper, merchant, support | AUTH-1: access differs by role |
| 2 | `intent` | order_status, refund, cancellation, return_eligibility, policy_question, product_search, dispute, account_change, out_of_scope | SCOPE-1/2 tool paths; account_change and dispute escalate (ESC-2, ESC-3); out_of_scope refuses (legal advice, payment cards, non-Cartwheel) |
| 3 | `record_state` | order_placed, order_shipped, order_delivered_in_window_under_100, order_delivered_in_window_over_100, order_delivered_past_window, order_refunded, order_cancelled, order_outside_caller_scope, order_data_quality, product, product_data_quality, policy_page, none | Record state decides the answer: only `placed` cancels, only in-window `delivered` refunds (`seed/eligibility.py`), over $100 queues |
| 4 | `applicable_policy` | platform_default, store_override_stricter, store_override_looser, store_restocking_fee, none | `facts.yaml` store-over-platform precedence. Stricter: Juniper 14, Saltbox 7, Meridian 21. Looser: Northwind 45. Restocking fee: Cascade Audio, Second Stitch Apparel |
| 5 | `tools_needed` | none, one_lookup, several_calls | Execution path length |
| 6 | `difficulty` | well_specified, ambiguous, missing_information, boundary, correction_across_turns, authorization_boundary | Changes correct behavior (RESP-3). Boundaries: day 30 inclusive (13 delivered orders exactly on day 30); exactly $100 auto-approves, above queues |
| 7 | `user_style` | validator's 8 values | RESP-5: behavior must not change with tone |

Recorded but not sampled: `turn_count` (1 + followups), `data_quality_case_id`, and `expected.source.type` (`sql`, `eligibility_function`, `policy_document`, `data_quality_table`, or `specification` for human judgment).

Groups: **coverage** uses ordinary values (well-specified, platform default, every role and intent). **Challenge** uses damaged records, boundaries, store overrides, authorization edges, corrections, and missing information. Report the two separately.

Key facts: world "today" is 2026-07-01 (`WORLD_ASOF`). Damaged records: orders 8001 (reversed dates), 8002 (missing delivery date), 8003 (store mismatch); products 2 (duplicate title), 3 (missing title), 4 (negative price). Scenario users must be authorized to see the damaged record.

## Status

### Done

- Setup check (read-only): HW1 and HW2 committed, no HW2 placeholders remain; `.env` has the keys and `CARTWHEEL_MODEL=gpt-5.5`; Docker daemon was not running; no HW3 files yet.
- Existing `data/cartwheel.db` was seeded Sep 14 but has 2 non-seed refunds on order 4455 from earlier agent runs; reseed before the pilot.
- Part A: `data_quality_cases` reviewed; dimensions proposed and approved.
- Preparation: reseeded 2026-09-15 (18 policy docs validated; stray refunds gone).
- Preparation: Langfuse up (6 containers running, health endpoint 200 at localhost:3000).
- Preparation: `.env` switched to `claude-sonnet-5`; server started after the edit (port 8010).
- Preparation: smoke check passed (live model). Scenario `smoke-0001` (scratchpad only, not committed), shopper user 1, "What's the status of my last order?" Completed in 5.6 s; reply matched order 4455 in SQL; trace has the conversation, `claude-sonnet-5` generations, the `list_my_orders` tool call, and `cartwheel.scenario_id`. Student confirmed in the Langfuse UI. The query was read-only, so no reseed needed.

### Next

Part B: propose a 30-tuple pilot spread; student selects records via SQL and derives expected results; coding agent writes `scenarios/pilot_scenarios.jsonl`.
