# HW3 progress note

Working note for the Homework 3 walkthrough (`homework/module-1/hw3.md`). Not a deliverable.

## Working agreement

- The student drives: every command, file change, or generation step waits for an explicit "go".
- Student: dimension design, record selection and expected results (SQL, policy docs), pilot and final review decisions, video.
- Coding agent: writes JSONL and boilerplate from the student's decisions, explains errors, keeps this note current.
- Model for every run: `claude-sonnet-5` (`CARTWHEEL_MODEL` in `.env`; pass `--model claude-sonnet-5` to the runner). Not a course-configured model: routed through LiteLLM as-is, verified by the smoke check. Pilot and final must use the same model. Fallback if the pilot has fewer than 5 failures: a smaller Anthropic model (test on one scenario first).
- Known limitation: Claude generations in Langfuse record input tokens only (no output tokens), so the Part E report undercounts tokens and cost.

## Deliverables ("Files to commit")

- [x] `scenarios/pilot_scenarios.jsonl`
- [x] `scenarios/pilot-results.jsonl`
- [x] `scenarios/pilot_review.jsonl`
- [x] `scenarios/support_scenarios.jsonl`
- [x] `scenarios/support_review.jsonl`
- [x] `scenarios/monitoring_scenarios.jsonl`
- [x] `scenarios/final-results.jsonl`
- [x] `reports/smoke-output.txt`
- [x] `traces/support_traces.json`
- [ ] Video, 5 minutes or less (student)

## Required checks

- [x] `uv run python -m scenarios.validate scenarios/pilot_scenarios.jsonl` passes
- [x] Pilot review: at least 10 reviewed, at least 5 confirmed failures
- [x] Final review: 15 scenarios covering both groups, all 3 roles, every intent; revisions applied, rejects replaced
- [x] `uv run python -m scenarios.validate scenarios/support_scenarios.jsonl --final` passes (175 coverage / 75 challenge, 5 per damaged record, new IDs)
- [x] Monitoring set: 50 scenarios, both groups, all 3 roles
- [x] Final run: all 250 `completed`
- [x] Export succeeds with 250 unique `cartwheel_scenario_id` values
- [ ] Three exported traces checked (one challenge, one multi-turn)

## Review gates (student decides)

- [x] Dimension plan approved (Part A)
- [x] Pilot conversation sample accepted before running
- [x] Pilot review (Part B)
- [x] Final 15-scenario review (Part C)

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

## Open spec gaps

- **Partial refunds (found during the pilot-022 review).** The implementation permits them: `issue_refund` takes any amount up to the order total (`agent/agent.py:236`), and the threshold applies to the refund amount (`:254`). But `SPEC.md` and the policy docs never authorize them. pilot-022's expected result relied on this, so the student marked it invalid. Don't edit `SPEC.md` during HW3: it doesn't change the running agent and would shift the rules the scenarios are graded against. For the final set, use boundary cases the spec covers (no order totals exactly $100.00; eligible orders at $99.75 and $100.25 bracket the threshold). The $100 partial refund in the pilot also set order 9962's whole status to `refunded`. Candidate for a spec update in a later module.

## Status

### Done

- Setup check (read-only): HW1 and HW2 committed, no HW2 placeholders remain; `.env` has the keys and `CARTWHEEL_MODEL=gpt-5.5`; Docker daemon was not running; no HW3 files yet.
- Existing `data/cartwheel.db` was seeded Sep 14 but has 2 non-seed refunds on order 4455 from earlier agent runs; reseed before the pilot.
- Part A: `data_quality_cases` reviewed; dimensions proposed and approved.
- Preparation: reseeded 2026-09-15 (18 policy docs validated; stray refunds gone).
- Preparation: Langfuse up (6 containers running, health endpoint 200 at localhost:3000).
- Preparation: `.env` switched to `claude-sonnet-5`; server started after the edit (port 8010).
- Preparation: smoke check passed (live model). Scenario `smoke-0001` (scratchpad only, not committed), shopper user 1, "What's the status of my last order?" Completed in 5.6 s; reply matched order 4455 in SQL; trace has the conversation, `claude-sonnet-5` generations, the `list_my_orders` tool call, and `cartwheel.scenario_id`. Student confirmed in the Langfuse UI. The query was read-only, so no reseed needed.

- Part B: `scenarios/pilot_scenarios.jsonl` written (30 scenarios, 18 coverage / 12 challenge, 4 damaged-record cases). pilot-019 and pilot-020 were hand-built by the student; the other 28 have records chosen by SQL and expected results from eligibility, SQL, policy docs, or the DQ table. Messages came from one `claude-sonnet-5` call per conversation (4 workers, generator never saw expected results), then a critic pass, which changed nothing. Scripts and log are in the session scratchpad (`pilot_plan.py`, `generate_pilot.py`, `pilot_generation_log.json`). `scenarios.validate` passes (offline).
- `record_state` vocabulary: student renamed `order_delivered_past_window` to `order_delivered_outside_window`.

- Part B: student accepted the pilot sample and ran the pilot (`scenarios/pilot-results.jsonl`, 30/30 completed, live model `claude-sonnet-5`). Student reviewed 12 in Langfuse: `scenarios/pilot_review.jsonl` (valid JSONL) has 5 confirmed failures on valid scenarios (005, 019, 020, 026, 027); 022 invalid (partial-refund spec gap). Revisions to carry into Part C: 021 add a refund reason to the message; 022 replace with full-refund threshold cases ($99.75 / $100.25); 029 expected reason is wrong (store 1 has four "Heavy-Duty Vase" listings: ids 2, 16, 19, 1).
- Student's review standard: offering escalation is out of spec (failure); when the DQ handling says escalate, asking "want me to escalate?" is a failure.

- Part C: student approved the final mix. Coverage 175: shopper 95, merchant 45, support 35; intents order_status 30, refund 30, policy_question 25, cancellation 20, return_eligibility 20, product_search 20, dispute 10, account_change 10, out_of_scope 10; styles about even; about 15% multi-turn. Challenge 75: DQ 30 (5 x 6), store overrides 12, boundaries 8 (incl. $99.75 / $100.25 full refunds), authorization boundary 8, missing information / ambiguous 10, correction across turns 7. Carry the 29 pilot scenarios (all but 022) under new ids with the 021 and 029 fixes.
- Part C: reseeded 2026-09-17 before record selection (pilot changes gone: 0 non-seed refunds or tickets; order 180 placed, 9962 delivered).

- Part C: 250 plans built offline (`final_plan.py` → `final_plans.json` in the session scratchpad; no model calls). Mix matches the approved targets exactly; 29 carried from the pilot (021 marked for message regeneration, 029 reason fixed), 222 messages still to generate. Checks: every user has the tuple's role; access matches `authorization_boundary`; state-changing orders are distinct; eligibility recomputed with `seed/eligibility.py` equals the stored flag for every order; `validate_scenarios(final=True)` passes on the skeletons. Sparse cases adjusted: no order sits on Northwind day 45 (used 43–47), Juniper day 14 widened to 13–15, Saltbox 8–9, platform 31–32.

- Part C: `scenarios/support_scenarios.jsonl` written (250). Messages for 222 came from one `claude-sonnet-5` generator call plus one critic call per conversation (6 workers; the critic rewrote 18); 28 carried pilot conversations kept as-is (021 regenerated with a refund reason). Script: `generate_final.py` in the scratchpad. `validate --final` passes (offline): 175 / 75, 30 damaged-record scenarios, 250 unique ids, no pilot ids. Suggested 15-scenario review sample: support-0024, 0059, 0088, 0092, 0123, 0149, 0150, 0166, 0175, 0245, 0249, 0201, 0247, 0250, 0221 (both groups, 3 roles, all 9 intents).

- Part C: student reviewed the 15-scenario sample; all accepted (0088 first rejected, then accepted: the caller is support staff, who would have the order number). Student noted that correction scenarios pair unrelated items (e.g. 0247), which is unrealistic, and chose not to regenerate. Wrote `scenarios/support_review.jsonl` (15 accepts, no changes to apply) and `scenarios/monitoring_scenarios.jsonl` (50: 35 coverage / 15 challenge; shopper 25, merchant 15, support 10; all 9 intents; one scenario per damaged record). All scenario files validate (offline).
- The IDE reformats JSONL files into multi-line JSON when they are opened or saved. It happened to `pilot_scenarios.jsonl`, `pilot-results.jsonl`, and `support_scenarios.jsonl`; all three were restored to one record per line. Check `wc -l` before committing (30 / 30 / 250 / 12 / 15 / 50).

- Part D: final run completed 250/250 on `claude-sonnet-5`. A credit outage at 17:44 on 2026-09-17 failed scenarios support-0206..0250 (HTTP 500 from the provider); the student topped up and resumed, and all 250 completed.
- HW2 gap found during HW4 prep: `post_message` never set `cartwheel.session_id`, although its docstring requires it and the HW3 reference bundle has it. Fixed at `server/app.py:193` for future runs. The 283 existing final traces were backfilled with synthetic ids (sha256("cartwheel-session::<scenario_id>")[:32], one per scenario, shared across turns) via the Langfuse ingestion API, which merges rather than replaces. Mapping in `analysis/state/session_map.json`.
- The 45 output-less traces from the outage were deleted from Langfuse (ids recorded in the session scratchpad, `deleted_traces.json`). Remaining: 283 traces, one per user turn, 250 scenarios, all with session ids.
- Part E: `reports/smoke-output.txt` written (traces per scenario, per role: shopper 203 / merchant 80 / support 56; tool errors: get_order 5, search_help_center 2, list_my_orders 1, escalate_to_human 1; 31 escalations). `traces/support_traces.json` exported: 283 traces, 250 scenarios, 0 missing, 9.7 MB.

### Next

- HW3: student checks three exported traces (one challenge, one multi-turn) and records the video.
- HW4 Part A: review-interface proposal pending the student's answers (trace source, scope, expected-result visibility, Langfuse scores, agent suggestions).

### Earlier next steps (done)

- Part D: reseed (`uv run python -m seed.generate`), confirm the server still has `CARTWHEEL_MODEL=claude-sonnet-5`, then run `uv run python -m scenarios.runner scenarios/support_scenarios.jsonl --model claude-sonnet-5 --output scenarios/final-results.jsonl` (about 35+ minutes unattended, live model).

### Earlier next steps (done)

- Student reviews 15 final scenarios → `scenarios/support_review.jsonl`; apply revisions and replace rejects; pick 50 for `monitoring_scenarios.jsonl`.
- Part C: final 250 scenarios (175 coverage / 75 challenge, 5 per damaged record, new `support-` ids), 15-scenario review, 50 monitoring scenarios.

### Earlier (done)

- Review gate: student reviews the pilot conversation sample before any run. Open items: pilot-020 outcome `refund_approved` contradicts its reason (queued for approval); pilot-004 message says "hasn't shipped"; pilot-026 user guesses a delivery time.
- Then: reseed, run the pilot with `--model claude-sonnet-5`, review at least 10 results in Langfuse, write `pilot_review.jsonl`.

Part B (original plan): propose a 30-tuple pilot spread; student selects records via SQL and derives expected results; coding agent writes `scenarios/pilot_scenarios.jsonl`.
