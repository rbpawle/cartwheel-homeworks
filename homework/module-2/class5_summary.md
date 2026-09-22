# Class 5 summary: LLM judges (automated evaluators)

Speakers: Shreya (main demo), Hamel (commentary). Follows class 4's open and axial coding.

## What the class covered

- Given a failure mode from error analysis, build an automated evaluator for it.
- Write a judge prompt, measure how well it agrees with your human labels, then let a
  coding agent hill-climb the prompt against those measurements.
- The metrics that make a judge trustworthy, and the ones that fool people.

## Two kinds of evaluator

- **Code-based**: deterministic checks, e.g. "output under 100 words". Prefer these.
  - Hamel: "Try to use a code based eval if you can." Easier to build and maintain, no validation
    problem.
- **LLM judge**: for fuzzy criteria that resist code, e.g. "gives enough information without
  unnecessary detail".
  - Cost: you must validate the judge itself ("a meta eval"). You cannot ask an LLM "is this good?"
    and walk away.

## Writing the criterion

- Phrase it as **one sentence that evaluates to true or false** for a given output — a rubric item.
- Class example: "The final message includes all the information the user needs for their next
  decision, but doesn't have any irrelevant or excessive detail."
- Grice's four maxims (1975) as a frame for what "informative" means:
  - **Quantity** — include what is needed, no more.
  - **Quality** — say what is true and supported.
  - **Relation** — stay relevant to the request.
  - **Manner** — avoid ambiguity, be precise, order information logically.
- Worked failure example (cookbook return): reply said "it might be routed for human approval".
  Problems: refund amount missing; "higher value" is ambiguous; "might" is not definitive; no reason
  given for the routing.

## Judge design rules

- **Binary output only: pass or fail.** Not a score.
  - Scores need calibration and detailed rubrics, cost grows fast, and they hide decisions.
  - Binary is also what makes the alignment metrics computable.
- **Scope each judge to one axial code**, not a catch-all.
  - A catch-all failure is not actionable, and is much harder to align and debug.
  - If a judge will not align, **split the criterion into smaller ones** and build a judge per piece.
- **Prompt contents**: the criterion, pass and fail definitions (a fuller rubric), few-shot examples
  drawn only from the training split, and a structured output format with a binary verdict plus a
  rationale.
- **Model choice barely matters** — do not get stuck here.
  - Shreya starts small (GPT-4o-mini); Hamel starts with a frontier model then walks down to cheaper
    ones, watching the metrics.
  - Using the same model as the agent is fine: judging is a different task, and you measure it anyway.

## Treat it as a classifier

- The judge is a binary classifier; validate it like one.
- **Split labelled traces into train / dev / test, roughly 20 / 40 / 40.**
  - Flipped from usual ML: training only supplies few-shot examples, so dev and test deserve more.
  - **Train**: examples allowed in the prompt.
  - **Dev**: what you hill-climb on.
  - **Test**: held out, run once, checks generalization.
- **Leakage is the classic failure.** Do not evaluate on traces used as few-shot examples.
  - Hamel: 25 years in ML, "any company I've been in, I have found leakage."
- Label counts: at least **20 pass and 20 fail**; 50/50 is convenient, not required. Perfect balance
  is unnecessary.

## The metrics

Confusion matrix, human label versus judge label:

|              | judge: pass  | judge: fail  |
| ------------ | ------------ | ------------ |
| human: pass  | true pass    | false fail   |
| human: fail  | false pass   | true fail    |

- **TPR (true pass rate)** = true pass / (true pass + false fail) — of traces the human passed, how
  many did the judge pass?
- **TNR (true failure rate)** = true fail / (true fail + false pass) — of traces the human failed,
  how many did the judge fail?
- **Agreement (accuracy)** = fraction where judge and human matched. **Do not rely on it.**

### Why agreement lies

- The "squirrel judge": 100 traces, 5 human-labelled failures, a judge that always says pass.
- Agreement = 95%. TPR = 100%, TNR = 0%. Useless judge, great-looking number.
- Hamel: hearing "my judge has 95% agreement" is a smell that nobody validated the judge.

### Reading the two error types

- **False pass** (judge passes what the human failed): the judge is **missing real failures**.
- **False fail** (judge fails what the human passed): the judge is **crying wolf** → alert fatigue,
  wasted human review, and people stop trusting it.
- Which to prioritize is domain-dependent (criminal sentencing vs cancer screening), but in practice
  Shreya optimizes **TNR first**, so that anything the judge flags can be trusted.
- Targets mentioned: 85%+ on both is the goal; "my dream is like 70%, 90%" for TPR/TNR in the demo.

### Confidence intervals

- Metrics are computed on a small sample, so report an interval, not a point.
- Reading: if you repeated the sampling and labelling many times, 95% of such intervals would contain
  the true rate.
- Demo intervals were very wide (e.g. 25–74%), which means the sample is too small to conclude much.
- **The fix is more labelled traces.** More labels → tighter intervals.
- An interval that includes 0 means you know nothing yet.
- Formula lives in the course reader; let the agent compute it.

## The demo loop

1. Skill **`write-judge-prompt`** drafts v0 from the criterion and the training-split open codes.
2. Run it on the **dev** split; report TPR, TNR, agreement, each with a confidence interval.
3. Ask the coding agent to improve TPR/TNR; it writes v1, v2, v3 and re-runs.
4. Stop when the metrics satisfy you, then run **once** on the test split.

Demo results: v0 was TPR 50% / TNR 68% / agreement 62%. v1 traded TPR down for TNR up, which Shreya
preferred. v2 improved TNR again. v3 produced no change — her read was that the next move is *more
labelled data*, not more prompt tweaking.

## Things to watch for

- **Prompts drifting toward overfitting.** Weird, hyper-specific edge-case rules are a smell that the
  agent is gaming the dev set rather than generalizing.
- **Agents peeking at the test set.** Tell the agent not to; if you do not trust it, move the test
  split outside the working directory.
- **Prompts get longer every iteration.** Watch that the growth is rules, not memorized cases.
- **High TPR with low TNR shipped to production** is the common mistake — that is the squirrel judge.

## Topics worth exploring

- Grice's maxims (1975) as a rubric source for "informative" criteria.
- Confusion matrices, precision/recall, and why class imbalance breaks accuracy. Hamel's advice:
  build a spreadsheet, try 95 pass / 5 fail, and watch agreement stay high while TNR collapses.
- Wilson (or similar) confidence intervals for proportions.
- Train/dev/test discipline and leakage detection.
- Code-based checks: cheaper, and enough for anything expressible as a rule.

## How this lands on my own work

- My most frequent open code is **policy identifiers surfaced to users**, plus **internal order ids
  in replies**. Shreya's demo criterion covers nearly the same ground ("no internal IDs", "dumps
  fields the user didn't ask about"), so it is a good model for my own judge prompt.
- Those two groups are mostly **code-checkable** (does the reply contain `cw-*` or a bare order id?),
  which the class says to prefer over a judge.
- The fuzzier ones — unnecessary escalation, offering things the agent cannot do — are the real
  LLM-judge candidates.
- I currently have 22 annotations. HW5 needs **at least 20 pass and 20 fail for the chosen mode**, so
  more labelling is the prerequisite, and it is also what tightens the confidence intervals.

## Homework 5 preview

- Pick **one** failure mode from HW4.
- Split labelled traces into train / dev / test.
- Use `write-judge-prompt` to draft the judge, and `validate-evaluator` to measure and hill-climb
  TPR/TNR.
- Report the final metrics. More criteria are optional; using your own product instead of Cartwheel
  is allowed.

## Loose ends to follow up

- Slides were promised to be posted; they include extra material on false pass / false fail intuition
  that was skipped for time.
- Questions are better asked in Discord (tag the instructors) than left unanswered.
