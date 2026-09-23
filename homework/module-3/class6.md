Class 6 Notes - CI/CD

Summary of last time. Created LLM judge, hill climb from dev set results. Note that we don't have time to make LLM judges for everything. the worst thing to do is to have an slop LLM judge.

Today: Talk a bit about RAG, specifically retrieval. How do we know we're retrieving the right things? We'll choose a set of metrics to make sure we're retrieving the right things.

News and developments on evals. Blog post from yesterday. https://www.lennysnewsletter.com/p/advanced-evals-how-to-find-and-fix

RAG: Retrieval Augmented Generation
1. Retrieve documents
2. Feed docs to the agent to make the decision

RAG can get complicated itself. How to do retrieval?

Basic two step pipeline. Agent does (1) above, or some retrieval modoel does it. Many ways to do one.

Sometimes we have rerankers to "clean up" the ranked documents

When we're doing RAG, what we can control is retrieval of the documents (step 1). Agent will definitely hallucinate.

Retrieval of documents is the most important part of the process. It can be done more deterministically with different metrics.

Example: Imagine we have a ground-truth ranking of documents. Retrieving docs relevant to a return query. Example Ground Truth documents:

1. Default return policy
2. Specific store override
0. Irrelevant document
0. Irrelevant document
0. Irrelevant document

Imagine retrieval model returns:

* #1, #3, #2, #4, #4

What can be a document? Anything! Anything that can be retrieved.

Recall@k: Given k retrieved documents, what fraction of ground truths are in top K?

\# relevant docs in top K / # relevant docs 
 In example: 2 relevant docs in top k / 2 relevant docs

There's always gonna be a question: What is K? That depends on product

High K is not necessarily great. If K was 10,000, for example, the LLM will get overwhelmed and get confused, and won't be very specific.

Precision@k: Given all the documents returned by the retrieval step, how many are actually relevant?

\# of relevant in top k / k

In example: 2 relevant docs in top k / k = 5

Recall has to be as close to 1 as possible, otherwise agent is not getting the relevant stuff. However you don't want to have to search through a lot of stuff.

There's a precision-recall tradeoff. There's a tension here. You have to trade one for the other. If you wanted perfect recall, you'd look at all of them and be like cool, we got 100%. Precision is like, you can't recall all the documents, so you gotta choose the right ones.

Mean reciprocal rank (MRR) across Q queries:

(1/Q)*sum_i(1/r-i)

Where r_i = rank of doc i

Intuition: How far down the list do you need to go to find the relevant doc?

Normalized Discounted Cumulative Gain: When you have varying relevance, a finer-grained version of MRR (certain docs are more relevant than other). This is super important in RAG, not super important in search settings.

Github book on metrics: https://github.com/NannyML/The-Little-Book-of-ML-Metrics

## Building test cases for agent

Shreya came up with a failure taxonomy from lecture 4. Pretty 

# Our failure taxonomy from lecture 4

| Failure mode | Count | Eval?          |
|---|---:|----------------|
| Reply includes fields or policy the user did not ask about | 69% | LLM            |
| Reply exposes internal document ID (e.g., cw-refunds) | 38% | code           |
| Refund or cancellation executed without user confirmation | 18% | code           |
| Reply says refund is complete but tool returned queued | 12% | code           |
| Reply contradicts the tool result (e.g., wrong amount) | 9% | code           |
| Redundant policy lookups before answering | 15% | fix the prompt |
| Forgot budget or preference from earlier turn | 6% | fix the prompt |
| Ceramics store returned for a jam query | 3% | fix retrieval  |
| Product listing without photos | 3% | fix the prompt |
| "I completely understand your frustration" on a neutral question | 3% | fix the prompt |


jakartian similarity--used for Reply contradicts the tool result

If you can't fix the prompt in an hour or so, move on and create an eval.

So, Why the hell do we have fix the prompt as an option? Because we don't want to get so eval-pilled in the wrong direction. Everything is a judgment call, and you have limited time/resources. Everything is cost-benefit tradeoff.

## Components of an Eval

Evals have one component: a task

- **Tasks**: seed each task from a failing trace
  - Each task has an input, an initial database state, and a rubric
  - Around 5 tasks per failure mode
  - **Regression task:** agent already passes, guard against breakage
  - **Capability task:** agent sometimes fails, track improvement over time
- Rubric: How do you check whether the agent passed
  - Programmatic verifier, e.g. string match, database query, tool call check
  - LLM judge

If evals are all passing, something is wrong. Just like if all students are acing a class, then there's no good test going on. You don't want to feel good, unlike software engineering where the tests all pass when you merge a PR. If everything is passing, think bigger. Maybe the product can do more.

Recent benchmarks like automation bench. They have a lot of things in the rubric--like 100, which is crazy. If you have too many, you aren't doing a good job axial coding.

## Tasks in Harbor format

Harbor: an open source framework for defining and running agent evals. [docs.harborframework.com](https://docs.harborframework.com)

```
eval_cases/
  e-001-unconfirmed-write/
    task.toml
    instruction.md
    test.py
  e-002-internal-doc-cited/
    task.toml
    instruction.md
    test.py
  e-003-verbose-reply/
    task.toml
    instruction.md
    test.py
  ...
```

- Each eval case is a directory with three files
   - task.toml
   - instruction.md
   - test.py

## Walkthrough: instruction and rubric

### instruction.md

```
I ordered a Bluetooth speaker from Cascade Audio a little while ago and I'm wondering if it's been shipped yet?
```

### test.py

```python
def test(trace, db):
    result = run_judge(
        "verbose_reply_v2",
        trace
    )
    assert result["passes_mode"], result["evidence"]
```

### What run_judge does

```
## Task
Decide whether the last reply gives the user the information needed, without unnecessary detail.

## Fail rules
- Dumps order fields the user did not ask about
- Exposes internal system state
- Cites internal doc IDs like (cw-refunds)
- Compares platform and store policy when only one applies

## Output
Write a critique, then "Pass" or "Fail".
```

*Simplified for the slide. The real prompt has examples, boundary cases, and an output format.*

**High TNR is critical (otherwise false alarms block every merge)**

With Harbor, you don't want to run this in an ... automated way? It'll make mistakes I guess

## Metrics for running evals

Agent is nondeterministic. Same in put can passon one run and fail on the next

- The agent is nondeterministic: the same input can pass on one run and fail on the next
- **pass@k**: probability that at least one of k runs passes
  - `pass@k = 1 - C(n-c, k) / C(n, k)` (n runs observed, c pass)
  - For capability tasks: the agent can handle the case, but not reliably yet
- **pass^k**: probability that all k runs pass
  - `pass^k = C(c, k) / C(n, k)`
  - For regression tasks: the agent must handle the case every time

# Example: tau-bench

[Yao et al., 2024]

## Chart: 6 of 8 runs pass (n=8, c=6)

| k | pass@k | pass^k |
|---|---:|---:|
| 1 | 0.75 | 0.75 |
| 2 | 0.96 | 0.54 |
| 3 | 1.00 | 0.36 |

## tau-bench, airline domain

| Model | pass^1 | pass^2 | pass^3 | pass^4 |
|---|---:|---:|---:|---:|
| Claude 3.5 Sonnet | 0.46 | 0.33 | 0.26 | 0.23 |
| GPT-4o | 0.37 | 0.24 | 0.18 | 0.14 |

*Even the best models drop from 46% to 23% when every run must pass*

The point here is, pass-k gets oversaturated

## Continuous integration

- A suite of ~30 eval tasks that run on every pull request
- Mix of regression tasks (pass^k) and capability tasks (pass@k)
- Cover the failure modes discovered in axial coding
- Continuously add new tasks and retire old ones as the agent changes
- **The suite should never be 100% passing**

---

- Run locally with `harbor run -p eval_cases/`
- Run in CI with GitHub Actions (on every PR)
- Each run starts from a clean database state (Modal sandboxes)

About once a week, shifting evals around. Hamel likes to see 30-50% failures. Shreya 20-30%. No hard and fast numbers.

























