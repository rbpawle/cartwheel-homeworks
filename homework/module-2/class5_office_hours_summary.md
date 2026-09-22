# Class 5 office hours summary

Q&A following the LLM-judge lecture, one section per exchange, in the order they were asked.
Answers are from Shreya and Hamel. Names come from the transcript and are sometimes garbled by the
transcription, so treat them as approximate; a few askers are unidentified.

---

## 1. Bert — what are the confidence intervals actually measuring?

**Q.** The lecture showed confidence intervals, but over what? An average, a median? And why did
they stay wide across iterations?

- One interval over **TPR** and a separate one over **TNR**. Not an average of anything.
- **Widen/narrow lever: more labelled traces**, added to train and dev. That is the primary fix.
- If it still will not narrow enough, **split the criterion** into smaller ones: narrower scope
  means less variance across traces.

### Follow-on: what do you do with many judges?

- Aim for roughly **one judge per axial code**; do not put every problem into one judge.
- Managing the resulting sprawl:
  - Be **parsimonious** about creating judges at all.
  - Group them **thematically** and report composites.
  - Hamel's default composite: **"did this trace pass every judge?"** Harsh, but interpretable.
  - "Please don't over-engineer that kind of stuff."

### Follow-on: leadership wants one number, "is it good enough to release?"

- A single eval score is a **moving target**: judges get retired and redefined, so this month's
  number is not comparable with last month's.
- **Anchor stable reporting on product metrics** — churn, monthly actives, satisfaction. Evals are
  what you hill-climb to move those.
- On readiness: there are **no guarantees, only risk reduction**. Tell the narrative — what you
  examined, what you measure, where it fails, what you did about it.
- "Perfection has infinite cost."

---

## 2. Unnamed — what TPR/TNR should we target, and what if they stop improving?

**Q.** You suggested aiming above roughly 75% TPR and 90% TNR. What if it is stuck at 40/40?

In order:

1. **Add more labelled traces** to train and dev, so the coding agent has more examples of the
   failure mode. Keep going until progress stalls.
2. **Split the criterion.** It is probably too vague or doing too much.
3. **Try a stronger model**, though in Shreya's experience this is rarely the cause — these failure
   modes usually do not need frontier intelligence, and cheap judges are the point.

**Hamel's addition:** do **error analysis on the judge itself**. Look at the disagreements. If you
find them genuinely ambiguous, that is a smell that the scope is too large, or that the open coding
never pinned down where the line is.

---

## 3. Unnamed — must-have criteria versus weighted preferences

**Q.** I have a "tidy up my transcript" prompt. Some criteria are gates (content present, grounded,
no hallucination) and some are preferences (bullet points, concise) that I would weight and pass at
a 0.8 threshold. How should I decompose that?

- **Keep every eval binary.** Your **decision-making should be downstream of the evals**: weight
  them, gate on some, ignore others, combine into a score — all fine.
- The anti-pattern is **one-shotting a weighted score** from a single LLM call, which many people do.
- Verdict on the asker's design: reasonable as described.

---

## 4. Unnamed — can you write a judge from a framework before seeing failures?

**Q.** I have conversation-design rules (much like Grice's maxims) written long before the product
had traces. Does a judge ever start from a framework rather than from observed failures? And who
owns evals — whoever owns product voice?

- **No: never build a judge for a failure mode you have not seen in the data.** Shreya: "I feel very
  passionate about this." You would have to go hunt for examples anyway, so start from the data.
- **Do not build a judge for every axial code, either.** Errors fixable by a bug fix or a prompt
  line do not need a judge; judges are for fuzzy things you must measure at scale over time.
- **Sequence, end to end:** open and axial coding first → check the open codes with teammates →
  have a **domain expert** help phrase the criterion → only then build the judge.
- By the time you build it, you should be convinced the mode is real, recurring, and agreed on.

---

## 5. Karthik — should I stop open coding to fix a bug I just found?

**Q.** Mid-review I can see the tool is not returning the tracking link. Do I stop, fix the tool,
rerun, then come back?

- **Yes, go fix it.** "You've already won because you found a real error."
- That kind of low-hanging fruit does not need an eval at all.
- Error analysis is valuable in its own right, not only as input to automated evals.

---

## 6. Tara — every fix breaks something I already fixed

**Q.** I build the product, a teammate runs evals, and each fix seems to regress an earlier one. Is
this a coding-agent problem (Copilot, Opus 5, GPT 5.6)?

- **Expose your evals to the coding agent**, and instruct it to run the offline evals as part of the
  test suite, not just unit tests. This is the "harness engineering" idea: give the agent access to
  metrics, not only specs and unit tests.
- Be deliberate about **when** the eval loop runs, since it costs time; it varies by workflow.
- **Always inspect the artifacts yourself.** Shreya checks the judge prompt and the TPR/TNR each
  round: "otherwise you don't know — maybe one day you'll find something strange with it."
- Asker's plan, endorsed: put the rubric in the PR so teammates can review the intent.

---

## 7. Ben — how does an eval program work over months?

**Q.** I do open coding, log bugs, and they may not be fixed for months. Next round my axial codes
have changed, or another PM brings their own. How do you merge all that over time?

- Mostly a **product-management problem**: someone sits on top of the signals (error analysis,
  leadership, customer interviews) and prioritizes. "The hardest part is saying no."
- **Theoretical saturation:** as you review more, new failures appear less often, but never hit
  zero. Complacency — "we solved the errors, stop looking" — is the bad outcome.
- Your **intuition compounds**: you start to smell where errors will be, and open coding shifts
  toward testing hypotheses.
- Whatever you do has to stay **in sync with the decision-making authority** in your organization.

---

## 8. Vladimir — evals for trajectories, not outputs

**Q.** My agents replicate quantitative-research papers. I want to compare two agents on whether one
goes deep enough, is faster, or is cheaper. When do you build judges for trajectories rather than
outputs?

- Cost and latency are **deterministic checks** — just compute them.
- For depth and long tool-calling runs, do **data analysis over the trajectory**. Look up the
  **transition failure matrix** (in the earlier course reader, being updated).
- Find the **most upstream step whose fix has the most payoff**, then zoom in on that step or
  component. Long trajectories are overwhelming if you evaluate them whole.

### Follow-on: the agent stops following instructions as runs get longer

- Many patterns exist — side agents, verifier agents, different tool loops, up to fine-tuning.
- **Start simple and escalate only when simple fails.** Diagnose what is actually breaking: context
  management, retrieval, or tool choice.

### Follow-on: does the pass/fail split have to be 50/50?

- No. Do your best; imbalance mainly **widens the confidence intervals**. You need enough of each
  class to be confident about that class's rate.

### Follow-on: my domain is financially risky, I cannot wait to observe the failure

- **Guardrails and human-in-the-loop**, e.g. the agent proposes a trade and a human approves.
- **Simulation environments become the product** — building a good one is its own major project.
- Back-tests may not generalize.

**Shreya's meta point here:** evals are not software engineering. Do not enumerate every hypothetical
failure and pre-build architecture for it. Try something simple, do error analysis, build a judge for
the failure you actually saw.

---

## 9. Unnamed — how often does the judge run, and does it go stale?

**Q.** Is the judge run daily over production traces? And as traffic changes, a judge that was good
last month may not be good now. How do I stay on top of that?

- **Cadence gets a dedicated lecture**, so that half was deferred.
- **Error analysis never stops.** No golden rule for frequency, but refresh after any major product
  change, market change, or shift in user behavior.
- **Review what the judge flags in production**; drift there is your signal that the judge needs
  updating, and the same traces feed the next round of error analysis.
- Sampling strategies from the lecture are how you find *new* errors, not just re-measure old ones.
- This is a reason to be selective: only build judges for things genuinely worth tracking.

### Follow-on: isn't "manual" review contradicting the coding-agent workflow?

- It is **hybrid, with the human driving**. The agent builds the dashboard and groups codes; the
  human decides the open codes, the criteria, and the labels.
- "The agent is not creating any novel information from this whole process."
- Lectures skew toward the human parts because that is where the craft is.

---

## 10. Unnamed — when do we hill-climb the agent itself, and how do we track experiments?

**Q.** Today we only hill-climbed the judge prompt. When do we improve the agent? And should we use
a tool for experiment tracking?

- **Improving the agent comes in a later lecture** — "that's where everything culminates" — and you
  cannot skip ahead, because you need evals first.
- **Experiment tracking**: Langfuse, MLflow and similar all offer roughly the same thing: versioning
  and metrics. Not a focus of the course.
- Hamel: **do it without a tool while learning.** Tools give you tunnel vision and you end up
  following the tool's model rather than thinking about what you actually need.

---

## 11. Unnamed — platform team: should we standardize evals across agent teams?

**Q.** We provide an internal evals platform; other teams own their agents and evals. Should we
standardize on the metrics and the error-analysis process?

- **Generic metrics make people turn their brains off.** A dashboard of coherence/groundedness
  scores is the number-one thing Hamel sees entering a consulting engagement, and it almost always
  means nobody has looked at their data.
- **Standardize error analysis as a process, not as a platform.** Every data set needs its own
  rendering, search and annotation. (Next week: Isaac on OCR annotation, a very different interface
  from chat.)
- Strip out customized analysis and customized metrics and "you're kind of left with a database."
- Advice for platform teams: **serve one use case really well first**, and be honest about whether
  the use cases are actually the same. Standardization pays off less than it used to, because
  building bespoke tooling is now cheap.
- If teams work on the *same* agent, aligning them is worth it; different agents may simply not be
  comparable.

---

## 12. Psalm — is the problem the eval, or the prompt?

**Q.** When something is wrong, how do I tell whether to fix the judge, the prompt, or the skill?
There are so many dimensions that it goes in circles.

- **Bias hard toward fixing the product.** The class is about making the product better; evals
  sometimes help and sometimes do not.
- What matters is **error discovery**: if you do not know what is wrong, you cannot fix anything.
- It is normal to **do error analysis for months with no evals** when what you keep finding is
  low-hanging bugs. Hamel does this with clients.

---

## 13. Rahim — traces and evals for structured data

**Q.** How does this differ for time-series or structured numeric data, e.g. anomaly detection in
data entry? Would you use an LLM at all?

- **Traces are just logs**, a sequence of events; how you render them is a separate question per
  data type.
- Anomaly detection is **classic ML classification**, not LLM-judge territory: use code and
  statistics, and measure precision and recall.
- The hard part is **sampling**: deliberately find tricky, borderline negatives, for example where
  classifier confidence is low. "If they're too easy… you'll just get 100% on the eval, then who
  cares?"
- Build the eval data set regardless of whether an LLM is involved.

---

## 14. Unnamed — have you ever had to rethink the whole product?

**Q.** Have you hit a case where the thing you knew you had to do did not help at all?

- "All the time." A recurring pattern: you start evaluating and discover **the product itself is not
  helping the user**, and the reason it is hard to evaluate is that it is **hard to verify** — for
  the user too. How does the lawyer trust the brief? The doctor trust the report?
- The fix is **product redesign for verifiability**, not more eval machinery. Hamel has a blog post
  on this that he shared in chat.

---

## Topics to explore

- Transition failure matrix, for trajectory-level analysis (earlier course reader).
- Theoretical saturation as a stopping heuristic for review.
- Composite scoring across judges: "passes all" and thematic groupings.
- Precision and recall framing for classifier-style problems.
- Hamel's writing on verifiable product design.
- Harness engineering: giving coding agents access to eval metrics, not just tests.

## How this lands on my own work

- **My biggest annotation groups are cheap fixes, not judge material.** Policy identifiers and
  internal order ids in replies are exactly the "just fix it" category (sections 4 and 5). The judge
  should target a fuzzier mode, such as unnecessary escalation or offering actions the agent cannot
  perform.
- **Labelling is the bottleneck.** With 22 annotations, the answer to both wide intervals and stuck
  TPR/TNR is the same: label more traces (sections 1 and 2).
- **Keep judgments binary**, and do any weighting across modes later, when deciding what to fix
  (section 3).
- **Do not judge what I have not observed.** The product-search rule is a spec revision first, and a
  judge only if traces show it recurring (section 4).
- **Expose the evals to the coding agent** once modes exist, so later agent changes cannot silently
  regress them (section 6).
