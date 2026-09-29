# Progress and working notes

Context for the next coding-agent session. Read this after `AGENTS.md` and before the current handout. Last updated 2026-09-29.

## Status

| Homework | Status |
| --- | --- |
| HW1–HW5 | Done |
| HW6 | Done, all parts (A–E) and video. Committed on branch `hw6` (`86b1ee3 HW6 done`). |
| HW7 | Starting, on branch `hw7` (`homework/module-3/hw7.md`). |

## Environment

- Agent model: `CARTWHEEL_MODEL=claude-sonnet-5` (needs `ANTHROPIC_API_KEY`). Not persisted: each new terminal needs `export CARTWHEEL_MODEL="claude-sonnet-5"`, or Harbor fails every trial with `CartwheelAgent requires a model`.
- Keys live in `.env` locally and as GitHub Actions secrets (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) plus the `CARTWHEEL_MODEL` repository variable.
- Repo is a fork: `origin` = `rbpawle/cartwheel-homeworks`, `upstream` = the course repo. `gh repo set-default` points at the fork. Pull course updates with `git fetch upstream && git merge upstream/main`.
- Harbor 0.23.0 is a `uv tool` (own Python 3.14 env), not a project dependency. PyCharm resolves its imports via an added interpreter path.

## HW4 / HW5 artifacts

- HW4 failure modes (`analysis/state/patterns.json`): `do_not_cite_policy_id`, `internal_identifier_volunteered`, `escalation_without_basis`, `unsupported_capability_or_speculation`.
- Human labels in `analysis/state/labels/<mode>.jsonl` use **1 = failure present** (skip rows with `superseded_by`). HW5 exports in `hw5_labels/` use Pass = 1.
- Trace ID → scenario ID: `analysis/review_app/.cache/traces.json` (`meta.scenario_id`). The review app's ID filter accepts both.
- Frozen judges: `escalation_without_basis-v1` (the HW5 judge, `gpt-4o-mini`) and the course-supplied `unsupported_policy_claim-v3` (Claude). The adapter loads the frozen JSON in `analysis/state/judges/`, not `analysis/prompts/*.txt`.
- The escalation judge prompt embeds scenarios `support-0168` (legal advice) and `support-0008` (small claims) as examples; don't use them as cases scored by that judge.
- `created_from` was back-filled from `annotation_ids`; see `analysis/report/hw4_followups.md`.

## HW6 setup worth knowing

- 12 cases in `eval_cases/cases.jsonl` (IDs are scenario IDs): 5 `escalation_without_basis` (judge-scored), 7 `internal_identifier_volunteered` (code checks, `reply_not_contains` on the order/product IDs). One regression case, `support-0098`; the rest are capability.
- `cases.jsonl` must be one JSON object per line. It is often edited in multi-line form for readability, so convert before exporting or running `load_cases`.
- Baseline and Part E jobs are in `.harbor/jobs/` (not committed); the Part E result is `eval_results/support-0225-15.json`.
- Harbor runs locally: use `-n 2 --verifier-timeout-multiplier 3` (the default 300 s verifier timeout was hit while it downloaded dependencies). The exporter deletes and rewrites its output folder on every export, so parallel sessions need separate `--output` folders.
- Changes made to supplied code during HW6:
  - `replay/rollout.py`: new check kind `tool_called_any` (`names` list).
  - `harbor_adapter/summary.py`, `analysis.py`: read per-trial `result.json` when the job's `result.json` has no `trial_results` (Harbor 0.23 behavior).
  - `agent/tools.py`: `find_order` rewritten to the updated HW1 contract (`db.list_order_search_candidates`, newest first, match then truncate to 5).
  - `tests/test_hw_holes.py`: `test_m2_failure_report_matches_artifact_l_schema` skips only its demo-state prevalence checks when `unsupported_policy_claim` is absent.

## CI

- `.github/workflows/evals.yml`: `offline-checks` (free, every push) and `complete-evaluations` (paid Harbor run, pull requests only; ~60 agent runs and 25 judge calls per run).
- On `hw7`, `on:` is set to `workflow_dispatch` only, so pushes run nothing. Restore `push:` / `pull_request:` when CI is wanted again.
- Open issue: `tests/test_cli.py::test_non_openai_direct_run_does_not_export[ollama_chat/local-model-False]` fails only on GitHub runners (passes locally, including a clean checkout without `.env`). The warning comes from an SDK exporter outside the test fixture. Not caused by course work; unresolved.

## Working preferences

- Answer only what was asked; no trailing explanations or side notes.
- Show the model, tasks, agent runs, and judge calls before any paid run.
