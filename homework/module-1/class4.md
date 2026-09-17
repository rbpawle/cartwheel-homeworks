# Lecture 4

# Review from last time

Generate dimension of the problem. Hypotheticsal but realistic values for each dimension, then make synthetic requests
base don each tuple.

Confusion: around "expected outcome". Better phrase: "extra medatada".


example tuple:

(role = shopper, intent = return, days_since-delivery = 45, return_window_days =30, store_override = none

generated request: "can I return the vase I got a while ago? I never used it"


expected metadata is any extra data that isn't in the request. here, 45 days since deilivery is absent form the 
request. Show the delivery date and the 30 day return policy in the error analysis UI to judge whether the angent
correctly declined to return.

It's basically a way to log extra information. I am confused because it seems like a wholly different concept from
expected outcome.



## Today

Open coding: read traces, write notes
Axial coding: group notes into failure modes
Output: 5-8 categories with counts

Create trace dataset => read and open code traces -> axial code -> re-code traces with refined failure modes (goes
back to read and open code traces sometimes, cycl euntil no new failure modes and no change in re-coding ) -> set of
failure modes.

You iterate this until you have a confident set of 5-8 categories. You've odne it a few times, no new failure modes.
"Qualitative saturation" in the literature, I think, maybe got that wrong

### Live: open coding

error discovery skill. 

She's using a dashboard, I think it was vibe coded. She wants to spend ~15 minutes finding failure modes that a user
would see. Pretend we're a user.

We're looking at the chat window, annotated with the results that the agent created.

Shreya noticed that the chatbot returned a lot of information, maybe too much, more than the user asked for. Hamel
marks this as a strong failure. Put our product hat on; the user asked, is this delivered yet? If agent gives order ID,
that's extraneous. The user is gonna want tracking number and a link to the order page.

Mark as much information as you can; thumbs up, thumbs down, but also all qualitative information. But also don't dwell
on it.

What if you see things that you like? Maybe, it's good for the agent to say "I can open a support ticket"

Hamel says negative notes are more important, but whatever helps you in your mind to form the model. They'll come back
to this.

Hamel tries to find the macro problem about the interaction: what is the most important problem surfaced by this trace,
make a note, move on.

Note that excessive information about reasoning is not helpful for the user. Hamel doesn't really mind though.

Hamel: if you're noticing the same problem every single time, that's ok. Part of the process.

It's a bad user experience to have the agent have a conversation with itself about whether the policy exists or not,
damn just look it up.

Helpful to have tools like "edit" or "delete" in the error analysis tool, good for ergonomics.

Hamel: Read user message, skip to end to find anything really bad.

Hamel: Policy document link would be ideal, rather than regurgitating policy. All of this is a bit subjective and
takes practice.

Always having a follow-up action at the end of the text is a bit annoying. RLHF?

Hamel: Look at real conversation data. Note that real conversations don't have dimensions bc obv they were organically
generated. But you can reverse-engineer the dimensions.

With engineering hat on, we're noticing that there's a lot of tool calls.

Generally, she's externalizing the issues that she has. Not hypothesizing about what the causes are.

She hit a tool call limit; didn't realize that we had one?

Hamel says: this is the most powerful part of doing evals. Look at data! By doing this, you'll understand what the
application is doing better than anyone else. We should already have in our mind some burning problems.

Hamel: A good chatbot would return a UI widgit giving them some ability to manipulate or view their data. Show a 
picture of the product, show a return wizard

Shreya: You can't do the things she likes to do with their traces in Langfuse. That's why she likes to code their 
own. You can use Langfuse to store the data. Langfuse won't render the widget if you have a widget popping up in the
chat window.

She does comment on reasoning; comment on anything you can.

Do we write an open code on each repeated issue? Shreya says, yes, because they can be collated later. By having lots
of different examples, the agent can use them to find more.

Rule of thumb: do it until you hit 100. Generate more than you can annotate, because sometimes they're not able to be
annotated.

Hamel: On one case where the agent was going to escalate to human because of data quality: He does not like to involve
humans if it's not necessary. So reflect on that, is this really an issue? Shreya says: Don't give details on data
quality or internal problems in codebase.

We can also ask the error tool to find all cases where there was a human escalation. Automatic sample generation. 
Instead of looking at all traces, you can select randomly, and then have your agent find more examples for you.

Hamel: In user question about a vague order: Think about what the user would want. A table of all orders would be
ideal for the user.

Note that LLM doesn't have taste about product. Product perspective is necessary.

### Axial coding
Given all failure modes, and all of the notes, look at them.

Record map: creates a graph of records, not sure how sorted.

From here, you ask LLM to create a taxonomy for all the failure modes.

Use LLM AFTER you've looked at the data. Don't use the agent beforehand. But, the agent can help--it can expand what
you've annotated

This tool is all for me to decide what is going on. Just because something doesn't happen a whole lot doesn't mean it's
a bad example.

### Sampling traces from the firehose

* Method 1: uniform random sampling. Literally pick traces at random.
  * simple, unbiased baseline. however, most traces pass, so you have to read a lot to find a few failures
* Method 2: Cluster representatives.
  * For each trace, compute turn count, tool call count, distinct tools used, has retrieval, etc...
  * cluster traces by these features, split budget equally across clusters
  * pro: covers structural variety random cluster
  * con: clusters reflect structure, but not necessarily failure modes.
  * the Skill file has information on clustering!!
* Method 3: Dimension targeted
  * Make clusters based on dimensions
  * Review every trace in that slicde
  * Pro: Finds failures concentrated in one part of the specification
  * Con: Only covers one dimension at a time
* Method 4: Depth first search
  * You have a confirmed failure
  * Find traces with similar text (bad of words/embeddings)
  * Review each candidate, same failure or not?
  * pro: efficiently finds more instances of a known problem
  * con: only finds what you already know

### Error Analysis over time
How often should we do error analysis?
* Do it every week, you'll find more failure modes.
* Don't overcomplicate it. You have existing taxonomy, see if there are new examples of failure modes
Good rule of thumb for taxonomy: nodes are distinct, they cover more than one trace in each failure mode
Merge and rebalance within the existing taxonomy as modes get fixed. Every few months, redo the taxonomy from scratch.
Similar challenges described in Teresa Torres' Opportunity Solution Tree

You can build a table showing progress of failure mode incidence over time

Failure mode | v1 | v2 | v3
==========================
invented return policy | 18% | 12% | 3%|
...

Hamel: Evals will change over time. Challenge to hill-climb towards. Evals will come and go

## Homework 4 and before Lesosn 5
* Build review interface
* Review 100 traces
* Raindrop Workshop: Use agents to discover new failure modes. It doesn't replace human judgment.



# Office Hours

Ankur: parts of error analysis he was confused about. (1) Trail is remarking on reasoning not being revealed to user

Shreya: If reasoning is exposed to the user, shouldn't be too much, or too unnecessary. But even if not exposed, the
pain point has been the cost of these agents, and we'll want to do everything we can to cut the tokens.

Hamel: Reasoning doesn't personally bother him. Taste--what do you want the product to do? He's used to seeing traces,
so maybe for him it's not a big deal. If it's not shown to users, don't scrutinize it. Unless, later on, doing root
cause analysis, trying to tackle/solve problems, maybe reasoning would help.

Ankur continued: Given that we might build in a widget to the app, when do you try to avoid over-engineering?

Hamel: Well, it's a tradeoff--who is it over-engineering for? What is the pain? Example: In a real application, when
a user tries to schedule an appointment. Then, asks user, which time? If those times don't work for the user, then
that's a bad experience to go back and forth with. It would have solved it for the user if there was a calendar 
popup. There can be problems without a widget--tool call failures, etc. Think of automated phone answering when you 
call like, Verizon. Wouldn't it be better if that was a display on your phone and you could choose the menu option
you want? Same energy as that.

Shreya: Working on hypothesis so far, looking at code analysis: we look at examples, and find a good version of that.
One one side, we can do open coding once a week, and other side, golden data set we're evaluating against. Not 
following her thread, but she's saying, there's two different ways to do things, and which is better in terms of
effort-benefit, and does one have diminishing returns.

Hamel: It might be good to not call it golden. Because it's not golden, it's gonna be thrown away. You're gonna 
conquer that challenge. You have goals, you reach them, you throw them away, and have different ones. You're on a 
self-improvement journey. This is how product growth works, and evals give you tools to conquer failure modes. You 
might throw them away, or run them infrequently. It's different from unit tests (which are cheap). You can just keep
running them. Evals are different, in that they aren't usually cheap. LLM as judge is a pain: you have to write the
prompt, and then you have to make sure it's good, and that it's worth it. 

Hamel: If you get to 100% success on an eval, drop it.

Hamel: Use failures as a wedge to make noise/change

Adrian new question: Agentic system--any output it generates gets human review before loaded into system (missed the
last part of his question)

Shreya: You can evaluate how human traces are doing. Based on that, you can either reduce number of traces for users
to review, or build better tools (UIs) for them to review with.

Sean (designer): Pass that handles situation gracefully vs case that doesn't fail. He tends to hone across the things
the agent did. Green passes--what to do with those? Do you ever code passes, and make taxonomy of that? Is it worth
working into the product?

Hamel: He does multiple passes. When he does error analysis for the first time, he learns so much that he will go re-do
it. He doesn't treat passes as annointed gold. It's still open to scrutiny.

Shreya: She doesn't do separate open coding or axial coding for passes. Sometimes she sees something she likes--find
all the things she positively coded, and ask agent to improve the prompts. No taxonomy on this. You have a finite
energy/time, where do you invest. Failure modes are the sweet spot for where to focus.

Karthik: He's anticipating an eval framework and process. Is there an existing workflow product setup today?

Shreya: No setup because it's so straightforward. She just posts opencode interface, and they just keep adding to this.
From there, she has lots of data to build a taxonomy from.

Hamel: Same as Shreya. Because we have AI to build apps, we don't need complicated frameworks. Create the process, and
then build tools around to fit you.

Avin: Building operating system for how things run. Users have no technology acumen. He's creating an agent to figure
out how to run the business. Replacement for Jira. Can he create a tool for users to create the traces and open code?

Hamel: Whenever you can do that, yes, that's great. Always think about ways to have users annotate their data. You
can do it through thoughtful product design--can you bring the user along for the journey? Tune it so that users have
an easy time giving feedback. Instead of judging just on outcomes, you can narrow down to specific uses.

Shreya: It depends on appetite of users. You need users to dogfood.

Catherine: She created the trace viewer for the company's production agent, which is collecting rich data. Process now
is a weekly 45 minute meeting, where PMs, engineers review user feedback I think, and make notes. Problem is, it gets
lost.

Hamel: You need someone to focus on product, what are problems you need to solve, even before getting into evals. Once
you've identified one problem, you have to say no to others. Keep notes in UI

Adrian: What to do when sourcces are in a language that domain experts don't speak?

Shreya: You can't evaluate everything. It has an extremely long tail. It's ok if you can't cover all languages, unless
users start to complain. It's a question of resources.

Alicia: Her company is building an agent, and there are no evals. How do get evals in place?

Hamel: Evals are simpler to implement than people might think. The best way to fix it is just to bring errors up, 
describe problems, and say this is how we are gonna go about fixing them. That's the best way to fix things.

Alicia: Works on Salesforce, building product. They are building an agent, and I think she's saying, the traces are
too much work to analyze, I think.

Hamel: He worked with a company just like Salesforce, and he sat with them and looked at traces with them. If they
aren't looking at traces, they need to start there. Show people what you've found there. Root cause is a different
story, so start with errors!

Accuracy improvement/cost improvement; use a different model for example. Prompt optimization, cut tokens, cut tool
calls. This will be covered in last two lectures. Org might have cost gateway to track cost per person. Every
organization has rolled their own gateway.

Hamel: Evals help with this: hill climb towards different objectives.



































