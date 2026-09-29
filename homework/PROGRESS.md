# Progress and working notes

Context for the next coding-agent session. Read this after `AGENTS.md` and before the current handout. Last updated 2026-09-29.

## Status

| Homework | Status |
| --- | --- |
| HW1–HW5 | Done |
| HW6 | Done, all parts (A–E) and video. Committed on branch `hw6` (`86b1ee3 HW6 done`). |
| HW7 | In progress on branch `hw7` (`homework/module-3/hw7.md`). Parts A–C done. Part D code written; workflow disabled and not yet run; dashboard not built. Part E (`monitoring/README.md`) and video not started. Nothing committed yet. |

## Environment

- Agent model: `CARTWHEEL_MODEL=claude-sonnet-5` (needs `ANTHROPIC_API_KEY`). Not persisted: each new terminal needs `export CARTWHEEL_MODEL="claude-sonnet-5"`, or Harbor fails every trial with `CartwheelAgent requires a model`.
- Keys live in `.env` locally and as GitHub Actions secrets (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) plus the `CARTWHEEL_MODEL` repository variable.
- Repo is a fork: `origin` = `rbpawle/cartwheel-homeworks`, `upstream` = the course repo. `gh repo set-default` points at the fork. Pull course updates with `git fetch upstream && git merge upstream/main`.
- Local Langfuse: `docker compose -f observability/docker-compose.yml up -d`. After the upstream switch to the Chainguard MinIO image (runs as UID 65532), the MinIO volume was re-owned: `docker run --rm -v observability_langfuse_minio_data:/data alpine chown -R 65532:65532 /data`. Undo with `chown -R 0:0`.
- `gh` defaults to the upstream repo for some commands; pass `-R rbpawle/cartwheel-homeworks`.
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

## HW7 setup worth knowing

- `monitoring/config.json`: judge `escalation_without_basis-v1` (`gpt-4o-mini`), model `claude-sonnet-5`, random rate 0.2, risk group `policy_lookup`, threshold 0.20 (chosen before seeing results).
- Periods (UTC): `before` = HW3 final run, `2026-09-17T17:16:00Z`–`18:23:00Z`. That run was split by a credit outage (17:16–17:44, resumed 18:15–18:22 for support-0206..0250); no scenario appears twice, and the student accepted it as one period. `after` = new run `2026-09-29T15:49:00Z`–`15:58:00Z`, results in `scenarios/hw7-after-results.jsonl` (50/50 completed). Both periods: 54 traces, 50 conversations.
- The agent's `prompt_version` differs between periods (`ad4c0c95989c` → `37468eb59f05`).
- Results (`monitoring/history.jsonl`): before raw 0.40, corrected 0.4565, CI 0.0–1.0; after raw 0.30, corrected 0.2935, CI 0.0–0.8805. Se 0.7333, Sp 0.88 (40 held-out traces). Risk group flagged 5/26 before, 10/27 after.
- 7 of the 50 monitoring scenarios are in the escalation judge's test split; `support-0008` (embedded in the judge prompt) is a monitoring scenario but was not selected for judging in `before`.
- `monitoring/run.py`: `--period <label>` (writes output, scores, history, chart) and `--last-hours N` (groups by `meta.session_id`, writes output and scores only; zero conversations → zero-count output, no judge call). The judge prompt auto-confirms when stdin is not a TTY. Local output in `monitoring/output/` (gitignored). Judge text reproduces the HW5 inputs exactly (verified on 24 shared traces).
- DocETL caches judge responses, so reruns cost $0.00 and return identical verdicts.
- Langfuse scores: 10+10 `_verdict`, 26+27 `_risk_verdict`, 2 `_corrected_prevalence`. Reruns update by stable score ID (verified on `before`). The handout's second `after` rerun check is still to do.
- Change to supplied code: `monitoring/write_scores.py` `post_scores` sends `session_id` when a record has no `trace_id` (Langfuse 3.225.7 rejects scores without trace/session/dataset run). `run.py` sets `session_id = monitor-<label>` on the prevalence record.
- `.github/workflows/monitor.yml`: `workflow_dispatch` only (`schedule` commented out), `runs-on: self-hosted`. Not yet done: self-hosted runner, `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` secrets and `LANGFUSE_HOST` variable on the fork, merge hw7 into main (schedule and dispatch need the file on main), one manual run, Langfuse dashboard.

## CI

- `.github/workflows/evals.yml`: `offline-checks` (free, every push) and `complete-evaluations` (paid Harbor run, pull requests only; ~60 agent runs and 25 judge calls per run).
- On `hw7`, `on:` is set to `workflow_dispatch` only, so pushes run nothing. Restore `push:` / `pull_request:` when CI is wanted again.
- Open issue: `tests/test_cli.py::test_non_openai_direct_run_does_not_export[ollama_chat/local-model-False]` fails only on GitHub runners (passes locally, including a clean checkout without `.env`). The warning comes from an SDK exporter outside the test fixture. Not caused by course work; unresolved.

## Working preferences

- Answer only what was asked; no trailing explanations or side notes.
- Show the model, tasks, agent runs, and judge calls before any paid run.
