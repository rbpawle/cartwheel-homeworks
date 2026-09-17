# HW3 notes: pilot scenario plan (30 tuples)

Draft plan for `scenarios/pilot_scenarios.jsonl`. Dimensions come from the approved plan in
[hw3-progress.md](hw3-progress.md). All ages count from the world's fixed today, **2026-07-01**.

Still to fill in per row: the real record (order/product/policy id), the acting `user_id`,
the expected outcome with its source, and the user-visible facts for message generation.

## Coverage (18)

| id | role | intent | record_state | policy | tools | difficulty | style | turns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pilot-001 | shopper | order_status | order_shipped | none | one_lookup | well_specified | terse_fragmentary | 1 |
| pilot-002 | shopper | refund | in_window_under_100 | platform_default | several_calls | well_specified | neutral_conversational | 1 |
| pilot-003 | shopper | refund | in_window_over_100 | platform_default | several_calls | well_specified | frustrated_impatient | 1 |
| pilot-004 | shopper | cancellation | order_placed | platform_default | several_calls | well_specified | neutral_conversational | 1 |
| pilot-005 | shopper | return_eligibility | past_window | platform_default | several_calls | well_specified | confused_rambling | 1 |
| pilot-006 | shopper | policy_question | policy_page (shipping) | platform_default | one_lookup | well_specified | requests_short_plain_answer | 1 |
| pilot-007 | shopper | product_search | product | none | one_lookup | well_specified | typo_heavy | 1 |
| pilot-008 | shopper | out_of_scope (legal advice) | none | none | none | well_specified | neutral_conversational | 1 |
| pilot-009 | shopper | account_change | none | platform_default | one_lookup | well_specified | repetitive_pressuring | 2 |
| pilot-010 | merchant | order_status | order_shipped (own store) | none | one_lookup | well_specified | operational_shorthand | 1 |
| pilot-011 | merchant | refund | in_window_under_100 (own store) | platform_default | several_calls | well_specified | operational_shorthand | 1 |
| pilot-012 | merchant | policy_question | policy_page (payouts) | platform_default | one_lookup | well_specified | neutral_conversational | 1 |
| pilot-013 | merchant | product_search | product (own store) | none | one_lookup | well_specified | terse_fragmentary | 1 |
| pilot-014 | merchant | out_of_scope (payment card) | none | none | none | well_specified | frustrated_impatient | 1 |
| pilot-015 | support | order_status | order_cancelled | none | one_lookup | well_specified | operational_shorthand | 1 |
| pilot-016 | support | dispute | delivered, inside 60-day dispute window | platform_default | several_calls | well_specified | neutral_conversational | 1 |
| pilot-017 | support | cancellation | order_shipped (not eligible) | platform_default | several_calls | well_specified | operational_shorthand | 1 |
| pilot-018 | support | order_status | order_refunded | none | one_lookup | well_specified | requests_short_plain_answer | 1 |

## Challenge (12)

| id | role | intent | record_state | policy | tools | difficulty | style | turns | DQ case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pilot-019 | shopper | refund | delivered ~18 days ago, Juniper (store 2) | store_override_stricter (14 days) | several_calls | well_specified | confused_rambling | 1 | |
| pilot-020 | shopper | return_eligibility | delivered ~40 days ago, Northwind (store 7) | store_override_looser (45 days) | several_calls | well_specified | neutral_conversational | 1 | |
| pilot-021 | shopper | refund | delivered exactly 30 days ago | platform_default | several_calls | boundary | terse_fragmentary | 1 | |
| pilot-022 | support | refund | in_window_over_100, refund exactly $100 | platform_default | several_calls | boundary | operational_shorthand | 1 | |
| pilot-023 | shopper | refund | in_window_under_100, no order number given | platform_default | several_calls | correction_across_turns | typo_heavy | 2 | |
| pilot-024 | merchant | order_status | order_outside_caller_scope | none | one_lookup | authorization_boundary | repetitive_pressuring | 2 | |
| pilot-025 | support | refund | none given | platform_default | none | missing_information | frustrated_impatient | 1 | |
| pilot-026 | shopper (user 392) | return_eligibility | order_data_quality (order 8002) | platform_default | one_lookup | missing_information | confused_rambling | 1 | dq-order-missing-delivery-date |
| pilot-027 | support | order_status | order_data_quality (order 8001) | none | several_calls | well_specified | neutral_conversational | 1 | dq-order-reversed-dates |
| pilot-028 | merchant (9001, store 1) | product_search | product_data_quality (product 4) | none | one_lookup | well_specified | operational_shorthand | 1 | dq-product-invalid-price |
| pilot-029 | shopper | product_search | product_data_quality (product 2) | none | one_lookup | ambiguous | neutral_conversational | 1 | dq-product-duplicate-title |
| pilot-030 | merchant (Cascade Audio, store 5) | refund | in_window_under_100, opened item | store_restocking_fee | several_calls | well_specified | frustrated_impatient | 1 | |

## Notes

- Mix: 18 coverage / 12 challenge. Roles: 15 shopper, 8 merchant, 7 support. All 9 intents, all 8 styles.
- The challenge share is higher than the final set's (75/250) to make the required 5 confirmed failures likely.
- Not covered in the pilot: `dq-order-store-mismatch` (order 8003) and `dq-product-missing-title` (product 3).
  The final set needs 5 scenarios for each of the six cases.
- Damaged records are reachable by their assigned users: order 8002 belongs to shopper 392, order 8001 is
  visible to any support user, products 2 and 4 are in store 1 (merchant 9001).
- State-changing rows (refund, cancellation) must target distinct orders so one run cannot invalidate another.


{
  "id": "pilot-019",
  "scenario_group": "challenge",
  "data_quality_case_id": null,
  "tuple": {
    "role": "shopper",
    "user_id": 333,
    "intent": "refund",
    "record_state": "order_delivered_outside_window",
    "applicable_policy": "store_override_stricter",
    "tools_needed": "several_calls",
    "difficulty": "well_specified",
    "user_style": "confused_rambling",
    "turn_count": 1,
    "order_id": 569
  },
  "opening_message": "I need to return the dinner plates that I bought a few weeks ago can you do that it is really important I need to get my money back",
  "followups": [],
  "expected": {
    "evaluation": "objective",
    "outcome": "refund_denied_store_window",
    "reason": "Order 569 delivered 2026-06-06, 25 days before 2026-07-01. Juniper Home Goods' 14-day override applies (the platform's 30 days would allow it); refund_eligible=0. No refund issued; cite store-juniper-home-goods-policy.",
    "source": {
      "type": "eligibility_function",
      "reference": "seed/eligibility.py:is_refund_eligible; orders.id=569 refund_eligible=0"
    }
  }
}

{
  "id": "pilot-020",
  "scenario_group": "challenge",
  "data_quality_case_id": null,
  "tuple": {
    "role": "shopper",
    "user_id": 204,
    "intent": "refund",
    "record_state": "order_delivered_in_window_over_100",
    "applicable_policy": "store_override_looser",
    "tools_needed": "several_calls",
    "difficulty": "well_specified",
    "user_style": "terse_fragmentary",
    "turn_count": 1,
    "order_id": 1082
  },
  "opening_message": "can I return order for everyday atlas",
  "followups": [],
  "expected": {
    "evaluation": "objective",
    "outcome": "refund_approved",
    "reason": "Order 1082 delivered 2026-05-21, 41 days before 2026-07-01. Northwind Books' 45-day override applies (the platform's 30 days would deny it); refund_eligible=1. $104.25 exceeds the $100 threshold, so issue_refund queues it for human approval (ESC-1); the agent must not say the refund is complete. Cite store-northwind-books-policy.",
    "source": {
      "type": "eligibility_function",
      "reference": "seed/eligibility.py:is_refund_eligible; orders.id=1082 refund_eligible=1"
    }
  }
}
