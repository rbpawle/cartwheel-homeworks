## Lecture 2 notes

#### Etc
Loom: create videos

#### Questions


#### Highlights

Data quality is the biggest issue
Trace tool spans are most helpful things to diagnose problems
Take a look at OpenTelemetry GenAI attribute checklist

### Traces

example failure: going through an example where there's an issue with how the agent responded to customer. let's say
the agent isn't proactive about data issues. how to have the agent handle data quality issues.

data quality issues are one of the biggest issues with agents.

to understand failure, do a trace.

Hamel's blog post on traces, what is a trace. so many different terms for the same things.

request: one customer message and work needed to respond.

Trace: collection of spans
root span has child spans
span has context. it has attributes. attributes are metadata. span has start/end times.
tool arguments and outputs

Take a look at OpenTelemetry GenAI attribute checklist

application-specific attributes are very helpful and important to use. When looking at trace, or trace viewer,
having what was the prompt, and what was the code version that created something, is super helpful.

Question from class chat: how to instrument? Coding agents help instrument app.

Trace: all spans associated with user/request. root span is confusing, so they use trace as shorthand

OpenInference: I think this is a layer on top of traces

do we collect all traces? Partial trace is not super useful, so they capture all. Log 100% of every single trace.
if you can only do a sample, that's ok.

Hamel's note: You might be thinking you don't want dependencies like OpenTelemetry. But, it's easy to forget to log 
something. Since we're using OpenAI SDK, there are many paved paths towards instrumentation.

Log everything, and you can subset what gets analyzed by LLMs.

Be careful about logging PII. Redact before storing traces. Presidio can help, open-source from microsoft.

Use Langfuse to view traces. Homework will have us instrument traces, then we'll view traces in Langfuse.
Langfuse is a service which provides a UI for observability. Langfuse is open source. In our project, the agent
will guide use through the usage.
Langfuse UI is kind of annoying, you have to dive into each trace. It's hard to line up one model span against another.
You can't really see if the model responded to the tool output correctly at the highest level; might have to dive into
the spans.

The tool will not solve the evals problem. Do not get fixated on the tool.
It's not our job to roll our own tools, existing frameworks get you pretty far.

Trace viewing is just hard, there's no great tool. Hamel puts his own trace viewer on top. he creates his own annotation
interfaces.

They want us to build our own trace viewer. the prompt they gave us is meant to have the agent build the simplest thing.
i.e. tell the agent not to do too much.

Traces vs Evals. Evals are metrics-driven systematic analyses of agentic systems. Traces are the data that underpin this
analysis.

If you never need synthetic traces, more power to ya. It's difficult to have real data bc we are building agents from
scratch. Other times, you can't look at real users' requests.

Is trace iinherently multi-turn or single-turn? (I don't understand this question.)
A trace can be literally user-message, one span. Doesn't have to be long, multi-span.

OpenAI Codex


## Office Hours

Dude who runs a manufacturing plant. He has lots of different production reports, and different agents.

When to use a spec?
* If you're the only developer, maybe you don't need it. It helps with collaboration.
* If you expect the agent to change over time. It's easier to adjust the spec than the agent prompt.

Hamel recommends building his own trace viewer for every project, every agent. LLms are good at basic
applications like this. There are skills for building this.

Existing observability providers for sharing one trace.

Dude has been building agents for quantitative trading. Agent to replicate papers written by other researchers,
and the agent sees if the research can be replicated.
He's having a challenge with adjusting strategy. After 20 turns, these things start to pop up.
He's going back to specs. He gives the agent a scope of work, and the agent writes the spec, not him.
He's noticed that the spec we're working with is human-written. His question is, when does the human write
the spec, and when does the agent write it? When do you break it up into smaller specs?

Hamel: In this domain, there might be a lot of craft that goes into the agent application. So, design the application
so that it can be evaluated more easily. Try to break it into intermediate steps.

Hamel's example: from blog post on eval smell, client wanted one-shot analysis of a very complex
medical evaluation. Doctor wouldn't sign off on a large result; they would want to understand the facts/data.
So in Hamel's example, they refactored the application to be more like research. His question is, think
about product design. Make it more modular parts.

As far as agent vs human written spec: Spec is a starting point. He tries to iteratively update it. In the 
beginning, it's the spec that constrains the system. Over time, it's the evals that constrains it.

Shreya says: it's important to keep the spec up-to-date. Some prefer application evals in working on the
agent product, and others prefer the spec. Over time, people might interact with the codebase via agent, and
via evals, more. So different organizations will do this differently.

Catherine Alvarado: works on conversational agents. Had asked about bloating trace logs. They capture lots of data in
user feedback, and they also capture traces. Evals have come towards the end, after prototype. She's curious about 
specific approach.

Hamel: Iterating and tuning a judge. You want to iterate on developing, and you start with some notion of whether
the judge is good enough. So you need it to be quantitative, whether it's good enough or not.

Shreya: Single LLM call (for judge? for eval?) can get confused. A naive dump of trace (everything associated with
root span). So this might involve some custom pre-processing. Secondly, you'll want to instruct your judges to focus
on relevant portions of the trace. e.g. if failure around particular tool call, you can tune the prompt to pay attention
to that. The arguments, the tone, etc, anything you want to tell the judge to pay attention to. A lot of this pre-
processing stuff/prompt engineering can help. For every failure mode, there will be different parts of the trace.

Catherine's question on search evals. Very well-studied. Information retrieval is a huge field for a while. At a high
level, take a user query, find a list of matches.

Catherine on hiring AI engineers. How important are evals in interviews? Hamel says, all top AI companies are using
evals. He's done analysis on jobs data. There is some data on jobs posting, evals are on the rise.

Ankur: He is a technical data scientist, long time in tech. How to be a little better around prompt iteration.
Do you use tools, etc?

Hamel: He likes to version prompts in Git. Not perfect, lots of commits, lots of intermediate things. He likes to
lean on evals to see what prompts are good. So we'll learn to measure things properly, lots of data science tools.

BrainTrust: you can view prompts side by side. While this is good for playing around (there are lots of eval tools
that allow you to analyze prompts side-by-side), these tools don't have access to your code. Prompts in isolation
don't make sense. It's complicated. So Hamel likes using Jupyter notebooks.

Iqbal is building something that will analyze things that are said about companies (or people?). He's having trouble
with parsing language; descriptions coming out are bad. When he limits the output, it's too dense with word salad.
Generally having trouble getting the agent to have good output.

Shreya: General design pattern: Basic prompt: You are an expert at X. Your job is to do X. So, she doesn't have do's/
don't's. She has LLM judge that decides whether the output works, and then re-prompt. The reason for this is that
models are getting better at responding to bare-bones prompts. 
Rule for document processing: extract as much structure as possible. Run deterministic algorithms on top of that, 
rather than running embeddings on top of them (She named a few--teece-knee?? ah, it's t-SNE)

Bert: Product manager, engineering background. He was brought in, assigned to project without product manager. They
were ready to release, and he wanted to know how did this evaluate. They said well UAT is up, and he said great. But
how did LLM do. So organization is not mature on evaluation thing. Bert did a usefulness study on it that didn't go
well. From that, they decided to buy a third party because they are bought in. Evaluations are built into the third-
party tool. So, how do you manage vendor lock-in, trust-and-verify. He's trying to get evaluation into the loop. He's
facing an eng team that just wants to build use cases, just get to production. He wants to get them to build evals
into SLDC.

Hamel's response: Seen this many times. He often hears people just want to outsource evals to a vendor. Evals = vendor,
vendor solves evals problem. (Bert says third party will help with that, so they're gonna help in their domain.)
Hamel says the process is really important. He also says the domain experts will drive what the user experience is
gonna be like. Not common for third-parties to do this well, so you gotta watch out for that. So, how do you sell it?
Best place is to start with error analysis. This is basically the foundation upon which you build evals--how do you
find real problems to work on. So, to influence people in an organization, don't start with evals. Start with data, and
data-driven progress. Such as bug fixes. People will ask, how does that happen. So you have a foundation for selling
evals.

Atendra: Lead data scientist at a ___ company. Different modalities in chatbot. Multi-agent setup with orchestrator
and sub-agents. Lots of things to build. Like many organizations, they want to release features and do evals after
that. Nobody knows how to do it. Trouble going on is lots of developers doing lots of different things. A lot of
changes, and a lot of features breaking. He's curious about top-down, bottom-up stuff. What is the starting point?
Known scenarios, top-down? Or bottom-up (not sure the difference).

Shreya: Always with bottom-up. Top-down is really hard to productionize. How do you productionize "hallucinations"?
People can't really say how hallucinations materialize. What does hallucination mean, what are customer experiences,
how do we fix it? However with bottom-up, if you look at lots of traces, you analyze each one. It's true that
different agents will have the same problems, it's just better this way.

Hamel's response: Lots of boondoggles with top-down. You can waste your time really fast. If you're at expert-level
with evals, you can maybe mix. But in this course, we'll be guided with bottom-up. Use top-down to go bottom-up.

Atendra response again: Bottom-up is time-consuming. Also, devs might want have test cases they want to do (with regards
to orchestration, e.g.), some kind of thing to investigate. Shreya: This isn't necessarily bad even if it's top-down. People
might have something specific that they've discovered, which is worth diving into.

Hamel: If you don't have a hypothesis, randomly sample until you have it. Or talk to users. But you should do some 
random exploration of data. However if someone comes to you with a hypothesis, go for it, find the data, find the 
evidence.

Atendra: lots of developers. So, how to scale? When you build a feature, should it have an eval built-in?

Hamel: Usually you don't want a dedicated evals team, and you shouldn't have the developer do their own evals. It should
be part of the SDLC. Don't put the evals team in the ivory tower. It may start there but it should change. Shreya has
also never seen it work successfully. So, be skeptical of evals. Don't say that the PM is responsible for one thing,
devs responsible for another. PMs should have access to the tool.

Jasmeet, building EHR search engine, they are in beta. The issue they are having is that there are a lot of traces.
They did eval beforehand, and at every point. The challenge is doing evals in production, where traces are huge. The 
___ chart is huge. They're doing some feedback with nurses I think. 

Shreya: It's better for people to look at fewer samples, but all the data. Better for someone to look at only 5 traces
if you only look at each piece of data in there. As for when search is too large for human to review: you can build a
special tool to have people look at the data. Ask them, what criteria is important, and create an LLM to extract that.
This involves lots of careful iteration with the stakeholder. Do not vibe-code this, because it will miss important
stuff in the chart. She's asked like, legal people, what are the most important clauses.

Hamel: Design applications with an eye to reviewability. As to how to do this in production, we will cover how to
think about sampling. You can't score every trace, so use sampling. It depends on how expensive the evals are. Some are
cheap, some are more expensive. When we go into error analysis, which will happen after generating synthetic data, how
do you look at traces intelligently considering it's time consuming? The best way to go about it is to use agent to 
help you explore intelligent. You want to be selective with what you look at. There's a way to read a trace so that you
don't get overwhelmed. Create trace viewer in a way that promotes progressive disclosure. Drill down into things later.

SOM's question: ah I don't really know.

Hamel: Blog post by OpenAI on harness engineering, leveraging Codex in an agent-first world. Hamel also has a blog post
about this. OpenAI created internal tools by letting agents swarm for months at a time. Harness engineering is
constraining so that things can be successful. Claude Code is a harness; something wrapped so it can work well. People
focus on unit tests/specs when building software, which are important. But important to keep in mind. Logs, metrics, 
traces are exposed to Codex via a local observability stack. In addition to code etc to the agent, you're giving agent
access to evals, traces, logs, metrics. You can expose traces to swarm in a way to be even better. Swarm can jail-break
the traces if they aren't being watched. So treat it with some amount of skepticism.

SOM's question: When defining spec, does he need to specify requirements, acceptance criteria? Does he need to operate
at that level, or does he need to limit that, and spend effort elsewhere?

Hamel's response: There's no best answer. It depends on how much you know up-front, do you need to know all the
requirements. So, sometimes the answer is yes, sometimes no. Faster you can get these into tests, the better. You can
also tell the agent not to change the tests. I don't know why this is relevant, I spaced out and swiped on bumble for 
a minute. Similar to skills. Markdown files become part of your prompt.

Adrian: He is processing documents, up to 500 at a time. Rules are verified by human, sometimes learned. At times they
go over the context window. Chunking not the best solution anymore. They are losing critical data because there's so 
much.

Hamel: If you're running out of context, running sub-agents is a legit idea. You're gonna want to set up some evals
about which cases are breaking and iterate on that.

