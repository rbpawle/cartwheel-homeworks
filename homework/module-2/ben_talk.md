Ben Hylak
Hamel Hussain

Hamel: He likes Raindrop, they do things in a way that is aligned. Ben has been invited in order to give more color on evals. Raindrop is well-designed.

Ben: Worked at Apple, cofounded Raindrop. Raindrop is meant to find critical issues in production agents. It is a local agent debugger.

About a year ago, everything was a chatbot. Now, everything is agents. In chatbot era, what we thought as "eval" (~1 year ago) is that you have prompt, it goes to model, you have some output, and there's some pre-defined validation.

Now, agents are pretty sprawled out. Instead of chat input, you have skills, you have tools, etc. Even changing the input type, or a field type, to a tool, changes how the agent behaves. A lot of these things are outside of the repo/context.

Agents are all intertwined with the world. MCP servers, github, postgres, slack, etc. So that complicates the eval situation. Simple input-output pairing starts to fall apart. Most of what your agent does and what goes wrong goes wrong.

More is more stopped working. 4000 evals means 28 days runtime. So you have to figure out which ones to run.

Agent issues don't throw exceptions. Harnesses can change evals. Changing harness can fail evals. Even some of the best eval companies have had their evals break.

Production monitoring, unsupervised real-time issue detection. You have in your codebase intents/prompts. You have baseline, which drifts, that is interesting. You have feedback on the issues we (? who's we?) send you.

Ben has figured out how to do deviations not just on error rates, but on semantics, unusual ways that agent fails.

Have tools that show traces, don't get drowned in AI slop. Their interface highlights finding the right trace and understanding it.

So, how do we *prevent* issues that happen? (US intercepted chinese vessel based on bad AI, for example) How do we do it without being fragile?

Ask, what would OpenAI do? They have a pretty good, stable product, so what would they do? OpenAI has a recent paper on Codex--the answer is simulation. Every time they have a change to a model, they have a whole rig that lets them simulate past traffic on codex, and ask, how would new model change codex directories (if I got that right.. what are directories in Codex?)

The idea is to replay real traffic against the change. What will my change.. change?

Example: deleting a tool. What you can do is find traces--use real questions and see if the answer changes. If they do, then flag those, they are the ones you want to review.

Q from Hamel: How do you deal with multiple turns in the replay?

Ben: Single turn/Multi-turn is confused language. Single turn is, I guess, one question in a 20-line conversation treated as one interaction. Multi-turn is using the whole conversation. The former is really hard to analyze, I don't know why.

Let's say you simulate the entire world around the agent: all the services, etc. That lets you test historical traces in a harness-agnostic way. Naive way of doing this is, you have the old trace, use those as cached results. If you do that in practice, the agent will call your bluff and realize it's in a simulation. Simulation awareness is something they measure.

Q from Hamel: Simulating tool calls--like an agent mock? I think?

In a trace, every tool call is a window into the world for the agent. If you're replaying a trace from a week ago, the world has changed since then. Even if you could plug your agent into current DBs, you won't want to, because state has changed. (missed something here.) Eval quality of responses and awareness of agent being simulated (you can do this by having the agent determine between two traces which is real and which is not). If agent realizes it's being evaluated, it says, I should probably do something in a certain way. You want to convince the agent that it's in the real world. What has changed is that models realize that they are in evals. The extreme example is the HuggingFace incident. In this case, they were just doing evals. They were trying to find answer key.

Agent will say something like, oh, I see why this isn't working, it's because I'm in an eval. At that point you've lost the point of the eval. Agent realizes it should be courteous in its tone, for example.

Think of all the tools the agent has. Github, etc. It will realize it's in a fresh environment, it will realize that everything is fake, evals become a lot less useful.

Hamel's Q: Do you create all the code, all the scaffolding, all the infra? Ben says, sorta. As much as he can use the code to find what the agent did, they do that. Push the boundary as far as possible, out to network calls, and simulate that. You want to see actual, real, agent traces. You want to see the code for agent ran.

You don't need thousands of simulations for every change. It's a factor of what kind of change you're making. Changing a tool needs 5-10 simulations. Rewriting the entire harness, or how critical the change is, you'd want more. Simulations have to use the tool that has been changed.

Some things you're looking for in new traces: Is the final response different, are there new tool errors, are tools being used differently, is the step count changed, changed trajectory, cost and latency differences.

One thing they think about: diffs vs evals. Both run on top of simulations. I think I said use scores not binary but not sure I heard that right.

Simulations are infrastructure. On top of that you have anomaly detection, evals are pure functions run over traces.

People used to talk about input/output pairs, but it doesn't scale well. Today, it's about judges, scores--something that takes an input (trace), and decides based on that. Verbosity, for example--no rambling responses, etc. Ben prefers binary checks. An eval can be: within 20% of length of response, or 20% of cost, or whatever, some threshold. Is the answer the same, is it more concise--have an LLM decide. With input/output pairs, any eval can run over any arbitrary trace. Versus something accumulating input/output pairs. Your organization is being aligned around a definition of good or bad.

Hamel: Codifying why is a trace good? Ben: It can be, but say you want to rerun trace, you want to simulate it. It doesn't have to be something you know is good. It can be about within 20% of what you had before (length, cost, etc). As long as that holds, you're good, you'll ship. Or eval is more verbose, yes/no. So it can be good traces, but it doesn't necessarily have to. Hamel: one thing you want to check is consistency. Ben: Yeah exactly. If you want to ask, is the answer the same, run 1000 traces, look at ones that are not the same. Is the answer the same? Can be done really easily with Jev.

It could be bad traces. You push a fix, you re-simulate, you're essentially looking at the same bad traces, and seeing if it has the same output as the judge from before, then you can see that the fix didn't work. Consistency thing is super important.

Hamel: This is soehting ppl want ot know when they change models. You can compute metrics via an LLM, which are inexpensive but highly valuable.

Ben: other side of spectrum: "Is the writing good?" Really hard to define, hence models are bad at it. Start with as deterministically as possible, go from there.

Hamel: RE: classifiers. Have you tried Jev?

Ben: Yeah, they posted a blog about classifiers. They've been evaluating Jev--it's really good. They did evals on his pipeline. He wants to be really up-front with themselves on how they would do evals. Historical data--does it agree with what they've labelled before, have another classifier decide what's right and wrong. Only have to have Opus decide on ... (missed it).

Hamel: You want to be sample-efficient when you learn about evals. This is one of the kind of things you want to surface to people, this is one of the things you want to look at. What are the ones you should look at?

Tool count after model switch: Easy evals to define and run. Verbosity judging--Human alignment matters now.

Development loop: log, detect, simulate, ship.

Foot guns: replaying against live suystems, serving cached tool responses, only replaying failures, forgetting non-determinism, averaging over something, missed the last one.

Hamel: How do we know the simulation is faithfully simulating the thing? Lots of surface area.

Ben: yeah, not trivial. Pretty hard. Customers connected to github. Checking their stuff out to sandboxes. If their agents have sandboxes, they're spinning out sandboxes for them. Whole alignment flow/smoke test--take prod traces, rerun them, they should equal main.

Shadowing deployments: very expensive to deploy double the agents.

# Transcript

Hamel Husain: Hello, everybody. We're gonna get started probably in, like.
 Hamel Husain: A little bit past 5 minutes, so just… thank you for your patience. Gonna wait for a guest speaker to come in, and I have to set them up a little bit.
 Hamel Husain: And then we'll come right back to it. So,
 Hamel Husain: Just letting you know that we're here, we're gonna do it, but just hold on a minute, and
 Hamel Husain: We'll… we'll get to it.
 Hamel Husain: Sometimes guest speakers, we kind of start a little bit after the hour.
 Hamel Husain: Because people have back-to-back meetings.
 Hamel Husain: Hello!
 Hamel Husain: Pretty good. Okay, so… You probably just want to mute this one?
 Hamel Husain: Mute Riverside, because their audio will go through Zoom. This is just for video.
 Hamel Husain: There you go.
 Hamel Husain: And then you can join Zoom.
 Hamel Husain: I'm gonna mute my audio, too, so you won't be able to hear me here.
 Hamel Husain: I'm gonna make you a, there you go, I found you on Zoom.
 Hamel Husain: Ben?
 Hamel Husain: Can you hear me?
 Ben Hylak: Yes, I can.
 Hamel Husain: Okay, cool. You might wanna, you wanna enable your video on Zoom.
 Ben Hylak: Sounds like when. There you go.
 Hamel Husain: There you go.
 Hamel Husain: All right, amazing. Okay, so we have some people here already. Let me do a quick introduction, and we can kick it off.
 Hamel Husain: Okay, so, like, we've been running this evals course for a while now, and every so often, we have… we bring people in who are working on evals. And there's a lot of different vendors in this space, and I have used every single vendor, or most of the vendors out there.
 Hamel Husain: And I try not to have, like, pick favorites, but I really do like Raindrop. You know, I like their philosophy, like, how they go about things.
 Hamel Husain: They tend to do things that are very aligned with the way that we teach in this class, and so I think it's really helpful, for you to see different aspects and things of evals.
 Hamel Husain: And so, I invited Ben to this class. You've already seen a little bit about Raindrop, we talked a little bit about it in lecture, like, it's like an optional thing you could use for the homework.
 Hamel Husain: We thought, okay, let's invite Ben to give, like, more color around the way that he thinks about evals, what he's working on, etc. I think it would be really beneficial for y'all. And so, yeah,
 Hamel Husain: I'll just go ahead and kick it off to Ben. Ben is a really talented person, by the way. He has an impressive background. He was working at Apple, before this, before founding Raindrop, before co-founding Raindrop.
 Hamel Husain: One of my favorite parts about Raindrop, it has, like, excellent design.
 Hamel Husain: And so, it's just, like, everything is thoughtfully designed, easy to find, and I've asked Ben about this, before, and he's like, well, that's just, like, a really, like, a skill that you, sort of pick up through…
 Hamel Husain: Running the gauntlet.
 Hamel Husain: And so, anyways, that was on the side, but I'll go ahead and kick it off to Ben, so he can kick it off, so you can…
 Hamel Husain: Go from here.
 Ben Hylak: Sounds like a plan. And then I should, screen share through, Zoom, just to be sure.
 Hamel Husain: Yes.
 Ben Hylak: Alright, just give me one second to set that up here… Hello.
 Ben Hylak: Perfect! You guys can see that okay here?
 Hamel Husain: Yeah, I can see it.
 Ben Hylak: Awesome. Let me just make sure that…
 Ben Hylak: Zoom is in the right spot, and that I can see.
 Ben Hylak: All the… all the right stuff here.
 Ben Hylak: Trying to make sure I can see the… Boom.
 Ben Hylak: Okay, let's see, trying to… okay, you guys.
 Hamel Husain: Oh, you're doing the fancy thing.
 Ben Hylak: Doing the thing, doing the thing.
 Ben Hylak: Cool, awesome. So, there'll be some time at the end for, any questions as well, but also feel free to just drop them in the chat as, as time goes on, and, and then we'll jump right into it from there.
 Ben Hylak: So, talk today is called Getting Started with Simulations, and so, this is both a product that we recently launched, also something that just, in general, everyone in the space is starting to do, labs are really starting to do, writing papers about, and, it's not not evals, we'll get into it in just a little bit.
 Ben Hylak: So, first of all, again, Hamel kind of introduced as well, but I'm the CTO and co-founder of Raindrop.
 Ben Hylak: And our whole company is about finding critical issues in production agents. So, we find those issues in real time, like, minutes after they start, verify those fixes actually work without side effects, and then now, we simulate those changes before they land.
 Ben Hylak: in production. We're used by some really amazing AI companies, everyone from, like, Vercel, Speak Framer, Clay, Legora, DoorDash, and many others. So, some really awesome customers here.
 Ben Hylak: We also have this, really cool, open source tool, which, honestly, like, especially if you're ever hacking on your own thing, it's a really nice, like, starting, point. I use it even in, like, a lot of my own, like, side projects. I'll just be like, hey, take this UI, like, either use it, change it, whatever you want, but it's kind of cool. Of course, the tool that, like, our Fortune 100, Fortune 500 customers use is, like, is what we call Raindrop.
 Ben Hylak: And we also make this really cool guide, very, very Hamel-inspired, called, like, howtoeval.com, and, probably due for an update even, even though we just, published it, like, what, like, 2 or 3 months ago or something like that, but, the space moves fast, everything's changing, which is why these, these courses matter.
 Hamel Husain: Amazing.
 Ben Hylak: So…
 Ben Hylak: like, I think it was, like, probably a year… I mean, maybe a little over a year ago, that, like, essentially everything was a chatbot.
 Ben Hylak: Right? Like, maybe, like, maybe a little over a year ago now.
 Ben Hylak: But, like, everything has changed to agents. And, this isn't just, like, a word changing, it's actually, like, it's actually kind of a big… it's a big deal, and I'll kind of explain why.
 Ben Hylak: So, like, in this kind of chatbot era, the way that we would think about evals, and again, the word eval is very overloaded, so I don't mean to say that, like, oh, eval… I'm gonna try to say evals are dead, or something like that, but just, like, what we used to consider an e… the way to eval has changed a lot, is the right way to put it. What we used to consider an eval, like, maybe a little over a year ago, was, like.
 Ben Hylak: You have a prompt, it goes to the model.
 Ben Hylak: you have a, you know, you have some sort of response that comes out, and then you have some sort of, like, predefined way, probably, for that given input, to know that that output is correct. Like, a very contrived example, but an example that you'll still see on, like, vendors' websites, even now, is like, you know, what is the capital of, like, the United States? And then it's like, oh, well, it's Washington, D.C, so it's like.
 Ben Hylak: Input, output, validator.
 Ben Hylak: The thing, though, is that, like, things have changed a lot since then.
 Ben Hylak: Things have changed a lot.
 Ben Hylak: One is that, like, agents are a lot more spoiled out, right? So it's not… no longer that you have this, like, nice, clean, like, oh, well, you just have to, you know, you change your prompt.
 Ben Hylak: and then you rerun, and you see what happened. So it's like, well, now it's like, you have skills, you have the tool definitions themselves, like, just adding or removing a tool can completely change the agent's behavior. Even if you didn't… even just changing the input type to a tool.
 Ben Hylak: can change…
 Ben Hylak: or even, like, the field name to a tool can change how the agent behaves, right? So it's like, clearly it's a lot bigger than the prompt now.
 Ben Hylak: You have, you know, users connecting MCPs, you have, of course, you can change the model, etc, but then now you also have memory, you have sub-agents, and then the prompts for those sub-agents, and a lot of these also, increasingly, are also outside of the repo, right? So you don't… you no longer have all the context, even in just the repo, which is really interesting.
 Ben Hylak: And the other thing, and kind of, like, which is related to that last point, is, like.
 Ben Hylak: Agents are very intertwined with the world now, right? Like, they have all their little, fingers and arms out, touching the real world.
 Ben Hylak: whether that's your own, sort of, internal production databases, whether that's other services, and again, no longer is all the state and all the context. Like, the emails that the agent goes and reads, are now part of the con… like, that's part of the context that's influencing the agent's behavior and what it's gonna do next. And so again, there's really those two big things that, you know, when I think about chatbots versus agents, it's like.
 Ben Hylak: They're really… the definition is sprawled out, and they're very intertwined with the world around them, and that makes them a lot harder to eval. And also.
 Ben Hylak: they've become more and more capable, more and more complex, and what that means is that sort of, like, single input-to-output pairing really starts falling apart. Because, most of what your agent is gonna do is, and most of where it's gonna go wrong.
 Ben Hylak: Truthfully, in practice, are going to be things that you haven't really thought about yet, and that's what makes it really hard.
 Ben Hylak: And so I think we've got… Hey, Ben.
 Ben Hylak: Sorry.
 Hamel Husain: People really love the slides. They want to know, is there a way for you to…
 Hamel Husain: Get out of the way of the slide somehow.
 Ben Hylak: Oh, I see, I see, I see, yeah, yeah, as long as I can figure out the Zoom setting, here, let's, let's see. Okay, you guys can vote. You guys might not want to see my face at all. Is this better, or should I just get myself out?
 Hamel Husain: I like seeing you, honestly.
 Ben Hylak: Oh, yeah.
 Hamel Husain: This is, like,
 Ben Hylak: You wanna do this one?
 Hamel Husain: Yeah, let's try that. I like seeing you.
 Ben Hylak: Yeah, give me feedback live if it's not working. And so I think that there was this, like, for some time in the evals world.
 Ben Hylak: There was this, like, more is more strategy with evals, which is, like, the more evals you have, like, you have 4,000, 5,000, 6,000 evals, and then that is gonna, like… that's your mode as a company, that's gonna be the thing. It's like, well, like, you know…
 Ben Hylak: There can be valid cases for that, like, if you're planning on training your own, like, frontier model, or your own… like, there are cases, and we can go into more details in Q&A, like, where that really does matter, but I think, largely, it's actually more about your strategy around evals than, like, the number of input and output pairs.
 Ben Hylak: You can collect, because, again, capabilities are increasing, so essentially, like, your agent can do more things faster than you can make evals, and the other problem is that, like.
 Ben Hylak: you start running into this problem where it's like, okay, so now I have 4,000 evals, let's say.
 Ben Hylak: If I add a tool.
 Ben Hylak: Am I… let's say I add some sort of tool. Like, am I actually gonna run 4,000 evals in that PR? Like, probably not, right? So it's like, well, how many are you gonna run? How do you find the right ones?
 Ben Hylak: And so…
 Ben Hylak: I think this is why, like, as a company, like, we actually, like, kind of stayed away from evals for a really long time. We were kind of like, you know, like.
 Ben Hylak: We focus on the real world, because
 Ben Hylak: that felt like the best agent thing to do. Like, it let us catch issues you were never expecting. It let us, like, have a lot of signal around those issues. It's not like… so, for example, one thing we saw with evals was that the harness would change and the evals would break. Like, the evals were expecting a specific tool to be called, but then you switched to a different harness, and now everything breaks. So, like, the reality today, even some of the
 Ben Hylak: best companies in the world, AI-wise, barely have functioning evals, and I've seen this time and time again, I won't call anyone out, but, like, even some of the poster child of evals, company-wise, it's… you talk to them, and they're like, yeah, well, like, all our evals broke when we switched.
 Ben Hylak: to, like, you know, quad code as, like, the harness underneath, or something like that. Like, so it's actually really, really interesting. And so we really focused on, again, we really focused on production monitoring, and we did that, essentially, we think of it, and, like, we call it unsupervised real-time issue detection, right? So it's, like.
 Ben Hylak: There's 3 ingredients that go into that production monitoring.
 Ben Hylak: The first is, like, your codebase, your prompts, right? So it's, like, we can sort of understand, like, based on how you've prompted your agent, based on the codebase, like, what should be happening, right? So, like, like, that kind of gives you, like, one, one data point.
 Ben Hylak: The next is, like, the baseline of behavior. So something like, you make a change and it… it drifts.
 Ben Hylak: Like, that's an interesting signal.
 Ben Hylak: And the last thing is, like, your feedback on the production data. So, like, looking at traces, I know Hamel, like, emphasizes this a lot, like, look at your traces. Like, we'll send issues, we'll send summaries, we'll send, like, alerts, and, and based on how you interact with that, we can learn, like, what you care about and what you don't care about. So again, this is sort of, like, how we've…
 Ben Hylak: Figured out how to,
 Ben Hylak: do that eval, but in production, right? Like, how to, like, really, really high signal, where when our… almost every single issue we send a team, they react to, they open, they do something with now, which is something we're incredibly proud of, and I think when you use other tools and you're just getting inundated by, like, random digests and summaries, it's like, well, that's not useful, right?
 Ben Hylak: But, I'd say this is just sort of, like, again, we do these deviations on… we've figured out as a company how to do these deviations on not just, like, you know, error rates and things, but things that are, like, very semantic, like, understanding, you know, unusual patterns of, the way that the agent's responding, the trajectories it's taking, etc.
 Ben Hylak: Kind of forgot about… forgot about these slides.
 Ben Hylak: this is what an issue looks like in RingShop as well, not to hammer this home too much, but, one thing that also I think teams really get wrong, somewhat of a tangent here, with, like, issues, this sort of thing, is, like, just show the traces, find… have tools that show you your traces, like, do not drown in, like, AI slop summaries of what your agent's actually doing. Like, so for example, here is, like, we show these, like, little annotations, these comments on the
 Ben Hylak: a trace that kind of helps you jump to the right point, which is important, especially now that traces can be tens of minutes, if not hours, if not days. But just, like, don't get lost in the sauce of, like, AI summaries of what happened, of what went wrong. Just, like, have ways that accelerate finding the right traces and help you understand the trace that you're looking at.
 Ben Hylak: Cool, let's go back. So, I think, though, like, again, I just talked a lot about production, but the thing is that, like, that is nice, but it doesn't prevent issues from happening.
 Ben Hylak: Like, it's good to catch an issue as soon as you can, it's good to know that your change actually did something well in the real world, and certainly the real world is, like, a really powerful arbiter of truth.
 Ben Hylak: Right? Like, it's, again, it's not like, oh, your harness broke something, and then your old eval you defined stopped working. It's like, no, like, people are complaining, people are mad, or, like, no, it's really working. Look, you can see people have, like, you know, recognized the difference somehow.
 Ben Hylak: But again, it doesn't prevent issues from happening, and especially as we have, like, Fortune 100 customers, as we have, like, you know, even, like, defense, you know, increasingly, you know, there was a story recently about, you know, the U.S. misidentified a Chinese vessel as carrying, nuclear, you know, nuclear weapons of some sort, and, like, intercepted it based on the
 Ben Hylak: bad information from, from an AI, we don't know which one. But, like, so clearly, like, this is, like, getting higher and higher stakes, right, as we go into, like, healthcare, defense, finance, etc.
 Ben Hylak: And so, as a company, we're like, how do we actually prevent these things from happening in a way that is not, you know, ridiculously fragile as well?
 Ben Hylak: And I think whenever you're faced with this, sort of question, it's really useful to take a little bit of a step back and say, like, what would OpenAI do? Like, OpenAI, you know, or, like, insert Foundation Lab here, but, like,
 Ben Hylak: you know, like, they're, like, a big company, they have a lot of users, they have a pretty good product that's, like, you know, pretty stable, and, and so, like, it's worth… like, Codex, for example, I think is, like, one of the best AI products that exist in the world, so it's, like, worth asking yourself, like, well, what do they do, right? And,
 Ben Hylak: And this is, one paper, from, recently, on Codex. They've had a few around simulations, and
 Ben Hylak: Essentially, the answer, I kind of gave it away, actually, is the answer to simulations. And so, every time they make a change to a model, they have a whole rig that lets them simulate the past traffic on codecs and say, like, well, like, how would this new model change the previous codecs trajectories?
 Ben Hylak: And so, the really powerful thing about this is that,
 Ben Hylak: You're now sort of answering the question of, like, What would my change change?
 Ben Hylak: Right? Like, and I think that's, like, a lot of times the rut that we see teams get stuck in, is that, like, they have, like, a lot of times the fixes, and getting to the point where you have a fix to some sort of problem with your agent, or add some sort of capability.
 Ben Hylak: I think getting to that point is actually getting faster than ever, but then there's this whole, like, consequence of making that change, and that's the thing where… that really starts slowing teams down. So really simply, again, simulations are you replay real traffic.
 Ben Hylak: There's real historical traffic against your new change, and you see what's different.
 Ben Hylak: So that change can be anything, right? That could be a new model, it could be a new tool, it could be removing a tool, it could be changing the prompt, it could be, like, you know, you switched from AI SDK to Pi. It could really be, you know, as big as you want here. And so you're sort of, like, again, you have the old traces that you've collected, and you find a way to just rerun your agent on those exact traces.
 Ben Hylak: So again, what will my change change? Does it actually fix it? Does it cause other issues, is kind of what you're asking.
 Ben Hylak: Let's just take, like, one very specific example. It's like, let's say you delete a tool.
 Ben Hylak: So, what you can do is, like, find traces where, before you made that change, that tool was call. Like, real user events where that tool was used.
 Ben Hylak: to answer their question. And then replay those.
 Ben Hylak: and then say, does the answer change, right? And then if the answer changes, you know, like, flag those, and those are the ones you want to review, right? So this, again, becomes a way that is, like, one, extremely targeted to whatever change you're making to your PR,
 Ben Hylak: Or, like, whatever change you're making in your PR.
 Ben Hylak: And, like, again, it really, really helps to answer this question, like, what does my change change?
 Hamel Husain: Can I ask you a question, and feel free to tell me you're gonna get to it, because…
 Ben Hylak: Defining.
 Hamel Husain: That's the nature of questions.
 Hamel Husain: So when you replay traces from production.
 Hamel Husain: if, let's say, you know, your agent is, like, has some multi-turn stuff going on, users asking follow-up questions, how do you deal with that? You know, like, yeah.
 Ben Hylak: This is a very, very good question. So, we, and this is, I think, one of the things that's actually very powerful, as opposed to, ev… like, the way that most people think about evals. A lot of times we see teams do, like, these, like, single-turn evals, and
 Ben Hylak: I think the single turn versus multi-turn is actually a very, like, somewhat, convoluted term right now. So, like, there's multi-turn as in, you're, like, 20 messages into a conversation, and then you ask the next question. And then there's multi-turn as in, you see the output, and then do another question, see the output, do not.
 Ben Hylak: I think the former of those
 Ben Hylak: doesn't really work right now, just to be, like, 100% honest. Like, I think that there's people trying to work on user simulations, like, like, as in, it's more like user prediction, and I think that's a really hard problem, because, you know, you take something as simple as, like.
 Ben Hylak: a user looks at the UI, and they're like, oh, this… you know, I don't like this design, right? It's like, well, like, how would you… it starts becoming a pretty hard thing to simulate.
 Hamel Husain: Yeah, it feels like, like, AGI.
 Ben Hylak: It's just… it's like, yeah.
 Hamel Husain: a whole U.
 Ben Hylak: Yeah, exactly, exactly, and we need to clone Hamel in order for that to work. So, what we're talking about here is a little bit different.
 Ben Hylak: So it's like, how do you take… you know, we talked about earlier that agents really spread out, the agent's really intertwined. It's intertwined with all these production databases, all these services, it's like, you know, it can talk to Slack, it can talk to GitHub, it can talk, you know, all these internal databases.
 Ben Hylak: How do we say, like, you know, you add a new tool, or you move towards your change of partners, like.
 Ben Hylak: We simulate that entire world around the agent that, as best as we can, that existed when that agent ran in the past.
 Ben Hylak: all those services, and we'll… there's an illustration in a second that'll explain how it works. But that lets you test
 Ben Hylak: those historical traces in a harness-agnostic way, and in a way that's not, like… I think the sort of, naive way of trying to do this is, like, well, you have the old trace, why don't you try, like, cache it, almost using those as, like, cached
 Ben Hylak: results, right? So when the agent… when you rerun it, the agent calls a tool, and you just kind of give it the same results. Like, well, actually, if you try to do that in practice, the agent will instantly call your bluff. It'll… it literally, like, you can try this,
 Ben Hylak: it'll just be like, I'm in a simulation, this isn't right. And, and so, simulation awareness is one of the things we measure here.
 Ben Hylak: Does that answer your question? We'll talk a little bit more in detail on how.
 Hamel Husain: Yeah, so what you're describing with, like, simulating the tool calls and stuff like that? Is a good way to think about that, like, some kind of Agentic mocks?
 Ben Hylak: Yes.
 Hamel Husain: Like, is there, like, an LM behind, like, trying to simulate the data that's coming back? Like, that's really interesting.
 Ben Hylak: Yes, exactly. So, we think about it in a few steps. The OpenAI paper is also a good read here, and we can send it after. But there's really, like, two or three steps. So, the first is that, like, actually, why don't I just… why don't we just do this?
 Ben Hylak: So that's sort of a silly illustration here. But what we think about is that, it's a little bit like Swiss cheese, okay? So, like, in the original trace.
 Ben Hylak: there are tool calls, and those tools had results, right? Every tool call is almost like a little window from the agent into the… into the state of the world at that time.
 Ben Hylak: One thing that's really important to remember here is that the world from… let's say I'm replaying a trace from a week ago.
 Ben Hylak: The world has changed since then, right? So I actually can't just, like… even if I could just connect my agent to, you know, the current production and, like, use all those databases.
 Ben Hylak: Don't do that, first of all. But second of all, even if I could do that, you wouldn't want to, because the state has changed. Take something as simple as a customer support, you know, bot for a delivery app. It's like, if the user asks, well, like, what… how far away is my order? And it says, like, well, 15 minutes or something.
 Ben Hylak: If I try re-simulating that, and it was hooked up to the current production database, it would give a different answer, or no answer, because nothing is pending. And so you really do have to understand the world. So we kind of take a two-pronged approach. One is that we try to, up front.
 Ben Hylak: sim… like, generate, both using the previous tool called results, and any sort of transformation we have to do for the current harness, and, like.
 Ben Hylak: you sort of want to pad those holes, right, so that if it's, like, you know, if it's, like, slightly off or, like, round, like, it'll get the right results. And also, at the same time, we're evaluating the quality of those responses and the agent's awareness that it's being simulated.
 Ben Hylak: And, and you can also do that once it's complete. The Opening AI paper talks how they will essentially take the original trace and the new trace, and then ask the agent which one is, like, most likely to have been simulated, and if you do that at population level, you can sort of, detect it that way.
 Ben Hylak: And so, essentially, it's kind of a nice hybrid between, like, having enough data up front where you're not, like, slowing everything down, but also you have an LM that's always there to spit out the correct data when possible.
 Hamel Husain: Can you tell me a little bit more about the simulation awareness? So, are you saying, like, if there's a situation where…
 Hamel Husain: your agent will just refuse, like, it'll just say, hey, like, I think we're in a simulation, like, haha, nice try.
 Ben Hylak: So, refusing is one, but there's more, which is, like, the agent can be, like, and I think one of the insidious ones is, like, and to be clear, this applies to all sorts of evals, right? Like, I think eval awareness in general is a very, like, big topic right now, because if you're, like, imagine you're doing, like, safety evals, like.
 Ben Hylak: And if the agent realizes it's being evaled, it's like, oh, well, like, I'm being evalued, like, I should probably, like, not do this, or I probably should do this, or I should probably, like, behave in this way. And it'll learn to do that. And so there's a similar thing with simulations, which is, like, you want to make sure that the agent does not understand, does not… believes that it is in the real world, and that there's nothing, like, really differentiating in that way.
 Ben Hylak: And that shows you how good of a job you did simulating. And so, I think in general, that's something that…
 Ben Hylak: that, now that, like, this is something that has changed a lot in, like, the last year or two, is that, like, you know, like, models now are trained to understand what evals are, how to do them, how to detect them, how to write them, like, all these sort of things, which also means they're, like, self-aware and better at finding out when they're being evaluated, when they're being tested, and finding creative ways. I mean, the
 Ben Hylak: extreme example of this is the Hugging Face incident, right? Which is, like.
 Ben Hylak: I don't think a lot of people realize that, like, what was going on at that time was, like, they were running cybersecurity evals, right? Like, they were just evaluing their agent. And it was trying to
 Ben Hylak: find the answer key to the evals that it was being run, right? So it's like, that's kind of the most extreme example of this.
 Hamel Husain: And do you see this happening in production, like, at these companies you work with? Like, sometimes you find that there's eval awareness? Okay.
 Ben Hylak: Definitely, definitely. Again, I think it's not usually, like, the Hugging Face incident, at least that, like, usually, but, like, it's more, it's more benign. It's like, oh, I see, like, this thing wasn't working because it's a simulation, I should probably answer, like, this.
 Ben Hylak: And now you've just completely, lost the whole point of the eval. Or, like, oh, the agent… or, like, the user's probably… like, based on this user question, the user's probably testing to see how polite of a response they would get in this case, like, I should be, you know, courteous of my tone and answer like this. And so it's like, well, you've just lost the whole.
 Ben Hylak: thing. And to be honest, I think that this is actually much more of a problem in the absence of simulations in many ways. Like, team… if you think about all of these tools your agent has access to to search Git, to search issues, to search previous conversations, all this sort of stuff, if all that's empty when the agent tries to run, it'll instantly know that it's in a simulation. It's like, oh, I'm in a fresh environment, I'm in an empty sandbox, I know that, like.
 Ben Hylak: This is just all fake, and the evals themselves end up being a lot less useful.
 Hamel Husain: And so, when you go to simulate this environment, like, because you're, like, okay, you're not simulating the human, but you're simulating, like, sort of the infrastructure.
 Ben Hylak: Yes, exactly.
 Hamel Husain: Are you creating… recreating the infrastructure? Are you recreating, like, like, to what… or is it like a…
 Hamel Husain: Is it… is it kind of like an LLM computer? That's like…
 Hamel Husain: you know, getting a request saying, okay, I'm gonna mock this response based on this and my understanding of the world, but, like, do you actually create all this code and all this, like, infrastructure? Like, to what extent, or is it in the middle somewhere?
 Ben Hylak: It's in the middle, it's in the middle. We try to recreate as much infrastructure as we can, and the reason for that is that there's a lot of things that are, somewhat deterministic, right? Like, imagine, you know, like, a common one is, like, you know, teams will have some sort of, like, SQL dialect or something like that they have internally for fetching data, or something like that.
 Ben Hylak: And it's like…
 Ben Hylak: there's a parser there. So, like, the agent's generating something and then it's getting parsed. Like, as much as we can use the actual code to validate what the agent just did, like, that's what we want to do. And so we try to push that boundary as much as possible, all the way out.
 Ben Hylak: To, like, the… to network calls, essentially. And then, simulate that.
 Hamel Husain: Interesting. Okay, that's, that's really, that's really fascinating.
 Ben Hylak: That's the really, I think, magical thing about simulations, and again, like, I think that, like, there are ways to get, like, started with this, like, just on your own, depending on how complicated your infra is, but, like, it really goes back to the looking at your traces thing, like, you want to see your actual, real agent traces, right? Like, not, like, some, like, random AI slot thing of, like, something. It's like, no, you want to see that your actual agent ran.
 Ben Hylak: code for your agent ran.
 Ben Hylak: And this is what happened. But ideally, again, you want to do that before production is also good, right? when you're testing new changes, yeah.
 Ben Hylak: Cool.
 Hamel Husain: Cool.
 Ben Hylak: So we talked a little bit about, just going back, like, this… you don't need thousands of simulations, OpenAI will talk about doing thousands of simulations, you really don't need thousands of simulations every single change. I think how many simulations you need is really a factor of, like, how big of a change you're making. If you're changing, like, if you're… let's say you remove one tool.
 Ben Hylak: So, like, well, like, maybe a little bit more than 5, but, like, probably on the order of, like, 5 to 10 of, like, traces that called those tools. Just, like, you're sort of just sanity checking that, like, the agent still, like, does the same thing.
 Ben Hylak: you know, if you're… if you're re-reading the entire harness or, like, something like that, like, you might want to do 50, you might want to do more than that. It really, again, it's both how big the change is and how well you pick the scenarios. You can imagine that, like.
 Ben Hylak: you know, a thousand wouldn't be enough if I removed a single tool. If I never call… if I never re-simulated a trace that actually used that tool.
 Ben Hylak: Right? And so again, it's really about, how well you select those scenarios, and how big of a change it is.
 Ben Hylak: And some of the things you're looking for when we do simulations, and these are sort of just, like, again, we'll talk a little bit more about evaluing simulations in a second, but, like, things we're looking for is, like.
 Ben Hylak: Is the final response different from what it was before? Are there new tool errors? Are there new tool usage? Essentially, did the trajectory of the response change?
 Ben Hylak: Is the step count different? Like, is it now taking many, many more steps to do the same thing? Cost and, like, latency are the other big ones. Like, essentially, is there a huge cost increase now? Or did the cost actually decrease as a result of this change? These are some of, like, the diffs that we're doing, based on the old traces.
 Ben Hylak: So, let's see… So one thing we think about are, like, there's essentially diffs, and then there's evals. So diffs are kind of what we were just talking about, which is, like, kind of, like, what changed, and you can also use an LM to decide if the change is good or bad.
 Ben Hylak: But then there's evals, which are more, like, scores that you want to, like, push up and target over time. I say score not just in, like, a, you know, 1 to 3 sort of thing, but, like, pass-fail, and, like, the number that pass and fail. And,
 Ben Hylak: Okay, I think we're gonna go more into…
 Ben Hylak: Sorry, we're kind of jumping around a little bit. We already talked about this, we talked about how, like, your code's running, you know, unchanged, and the state's getting mocked in between.
 Ben Hylak: Okay, got it, yes.
 Ben Hylak: So, back to evals. So we sort of think about it like simulations are this sort of, like, base infra in some way. On top of that, you have anomaly detection, so that's kind of like, did something weird happen? And then evals are what we define, I think increasingly are being defined as, like, pure functions that run over traces. So, as opposed to these sort of input-output pair evals, which still exist, they're more like pure functions.
 Ben Hylak: pure function, what I mean is it takes an input, and it returns an output.
 Ben Hylak: So, like, that input-output could be, like, a pass or fail. Also, the input can be, both the new trace and the trace before the change. So just sort of defining this really quickly, like.
 Ben Hylak: we talked before how there was a… two years ago, when we talked about evals, I think people mostly talked about, like, input-output pairs. So, people talked about, like, oh, generate this React component, and then it should generate code that's like this, right? That doesn't scale well.
 Ben Hylak: when we talk about evals now, most of the time what we're talking about is, again, you might hear the word judge, you might hear the word score, you might hear, like, something. Essentially, it's, like, something that takes an input, which is a trace.
 Ben Hylak: and then decide to just go back. For example, let's say verbosity. That's one that we see teams use. Like, you know, you don't want the agent to, like, you know, have these super long, rambling responses. So, your team might create a new eval, which is verbosity, and maybe even… either it's too verbose or not, or, like, say a score of 1 to 3, or 1 to 5, like, how verbose it is. I generally prefer the kind of binary, checks.
 Ben Hylak: But, like, we can talk about that at a different time.
 Hamel Husain: And is the right way to… to understand the one on the right is, like, underneath, like, inside this function, f of xy.
 Hamel Husain: You are doing… you're computing all these metrics, like the diff, the length, all that stuff you showed on the previous slide, and that's informing the pass and fail?
 Ben Hylak: Yeah, yeah. So, for example, you could create an eval that's, like, it's not 20… it's within 20% of the number of steps from before.
 Ben Hylak: Right? Or it's within 20% of the cost, or it's, like, the output length is within 20%, you know, something like that. You know, and so, that's, like, you can start to… or, like, you can create all kinds of cool things like this. Like, you can say, is the answer the same?
 Ben Hylak: Is the answer more… is it more concise? And have an LLM decide, like, is it more concise, right? And so the key thing, as opposed to the input-output pairs, is that this
 Ben Hylak: eval, once you define it, should scale to any arbitrary, trace, right? So now it's like, this is something you can just run over traces, versus, like, it being something that you're kind of, you know, accumulating these, like, input-output pairs. The way to really think about it, and how we think about it, is, like, you are aligning
 Ben Hylak: a, your organization, the humans in your organization, to a definition of what good or bad is.
 Hamel Husain: And just to make sure other people are following, so, like, why in this situation is a trace that you've decided is good, correct? Like, from the past, like, you said, hey, like, and you want to make sure X is still good? Is that how to understand?
 Ben Hylak: It can be, but it doesn't have to be. This is one of the really interesting ones. So, like, certainly this could be a dataset of good traces, like, you could have a whole dataset, and you could run and say, like, essentially, like, well, if I replay this trace, I want the same answer.
 Ben Hylak: There's also often value, if you think about, like, the output length one, it doesn't really need to be something that you know is good. You want to say, like, oh, I don't want it to get, like, more than, you know, I want the output length to be, like, within 20% of what it was before.
 Ben Hylak: like, I kind of know the state of my agent today. So, like, for example, let's say I'm, like, trying out a new model. I'm like, oh, cool, GPT-6 just dropped. Let's plug it in, and as long as it's within, like, 20% of the length of what it was before, then, like, I'm good.
 Ben Hylak: I'm good to ship it. Or, like, create an eval that's like, is it more verbose, yes or no?
 Ben Hylak: And it's, like, as long as, like, mostly, like, my pass rate is, like, you know, 80% of, like, it not being more verbose, then, like, I'm fine. Or if it's, like, maybe it's above 50%, like, you know, you can kind of decide. And so, it can be good traces, but it doesn't necessarily have to be good traces.
 Hamel Husain: Makes sense. It's like a… okay, it's like you're… one of the things you may want to check, essentially, is consistency. Like, you know, and so this is a… yeah, I like it. I like… this is a nice way to…
 Ben Hylak: Is the answer the same, is a good one, right? And then it also helps you narrow down the traces you should look at. Let's say that you created an eval that is like, is the answer the same? Run it over a thousand traces.
 Ben Hylak: And look at the ones where it's… they're not the same, right? Those are the traces you should be looking at. And it's either better or it's not, but again, creating something to score, like, it is a better answer, well, that starts getting a little bit trickier. You could still do it. But, like, the really easy one is, like, is the answer the same? Like, you could do that with Jev really cheaply, right? Like, is the final answer the same answer?
 Ben Hylak: Is an easier eval to create.
 Ben Hylak: Cool?
 Hamel Husain: Right.
 Ben Hylak: Yes, so this is, again, easy one, like.
 Ben Hylak: Like, to your point, actually, so, around the input data, it could actually be bad traces, actually. It's like one… that is one dataset we'll see a lot. Like, imagine, like, very easy, like, loop we'll see in Raindrop is, you get an issue notification, like, oh, a bunch of, like, users are, are, you know, complaining about this thing. They're not able to, like, download a file or something like that. You put, you push a fix.
 Ben Hylak: You then re-simulate.
 Ben Hylak: And you're essentially comparing the bad traces and saying, like, does the new output exhibit the same issue?
 Ben Hylak: right? Is the judge. And, if any of them return yes, then, like, now you know that your, like, your fix didn't work. So… so sometimes these are actually, like, bad input traces.
 Hamel Husain: I like it. Yeah, it's pretty smart. It's like, because this consistency thing is super important. Yes. Because this is a question that people want to know when they switch models, or make a change, and stuff like that. And I like the fact that
 Hamel Husain: There's a lot of…
 Hamel Husain: metrics? Like, you don't necessarily need to call an LLM, like, you highlighted the fact that you can compute all these metrics, which are super useful, and you might… you might want to do that first before reaching for an LLM, because those are super high-value kind of things that are not expensive.
 Ben Hylak: Yes, I think there's a… it's exactly what you just said. I think there's a gradient of, like, really deterministic things
 Ben Hylak: to, like, you start introducing, like, really deterministic classifiers to, like, your, you know, if you think on the completely opposite side of the spectrum, like, is the writing good, or something? It's like, well, man, it's a really hard and very tricky thing to define, which is why muddles are still really bad at writing. And so it's like, it's like, you can do it, it's possible to get an LM judge to, like.
 Ben Hylak: you know, you break out, like, what your organization means by bad, which is some mix of, like, using specific phrases, using M dashes, but it's, like, it's really hard, and so definitely, like, you want to start with things as deterministic as you can, and then start moving up the gradient of, like, consistency, like you said, and, and then go from there.
 Hamel Husain: Yeah, I'm gonna go ahead and front-run this question, because I know it's going to come up. You mentioned classifier. Have you tried GEM in this? Yeah.
 Ben Hylak: Yes, so, we actually… so we published this blog post, like, 2 months ago, where we were talking about, like, classifiers, right? And, called, like, our pipeline, and, like, I think, I think we realized, like, years ago, like, oh, you could actually just train really good classifiers and make it, you know, easy, et cetera, et cetera. That's not our business, but, like, we just needed to do it to make our product. And, we, we've been evaluating
 Ben Hylak: Jev a lot, recently, it's very good. Our, our pipeline is still, A, like, I don't know, it's still, like, 50x, 50 to 100x cheaper or something like that, and the accuracy is the same, so it's, like, but there's a lot of things that we're, like…
 Hamel Husain: So you did evals on your pipeline.
 Ben Hylak: We did Evo… we have so many evals, I… I couldn't even… I couldn't even start. Like, we have so many evals now, so many online… like, everything. That would be a really fun one, is actually, like, how… how… to be clear, like, this is mostly, like, we… we… what I'm talking about here is not… is not different from how we think about it, right? Which is sort of the magic of the company that we're building, is, like, we try to just, like.
 Ben Hylak: be really upfront with ourselves of, like.
 Ben Hylak: how we would do evals. And, like, a lot of it is, for example, like, historical data. Like, does…
 Ben Hylak: like, does it agree with what we've labeled before? And, like, if no, like, well, like, let's look at, like, where it disagrees, and have even another classifier decide if, like, those disagreements are, like, right or wrong. So we can, like, you know, then escalate that to Opus, right? And so you can start building those sort of chains, where it's like, I only need to have Opus decide on the ones where it's, like, it disagreed, or something like that.
 Hamel Husain: Another thing I like about what you're showing about this consistency thing is
 Hamel Husain: One of the things we talk about in the class is, like, how to sample data. Yes. And you want to be very sample efficient after you learn a little bit about evals, and so I really like the fact that, okay, you're… have this in your pipeline.
 Hamel Husain: And you're trying to show these examples, these are, like, one of the kinds of things you're trying to surface people. Say, like, hey, this is probably something you want to look at.
 Ben Hylak: Totally.
 Ben Hylak: Yes, I think about sample efficiency both in, like, obviously LMs and cost and all that sort of stuff, but also, like, humans looking at traces. Like, we talk a lot about, like, you know, look at traces, look at traces, but it's like, well, if you have, like, 100,000 events a day, like, you're not gonna look at all of them, and so what are the ones you should look at? It's not even just the ones where things went wrong, because if you're looking at the same ones, you'll often have a few error modes, like, that dominate, that you're not that interested in, like, if I
 Ben Hylak: about a lot of consumer apps that is, like, people complaining that the product isn't free. It's like, well, like, you know, that might not be the number one thing you want to be looking at every single day, right? And so, yeah, very, very important from both perspectives.
 Ben Hylak: Cool.
 Hamel Husain: Great.
 Ben Hylak: Yeah, again, just some more examples of, like, you know, easy things here, like, you know, is the tool call count after a model, is it less or is it more? Super easy eval to define, really easy to run.
 Ben Hylak: You know, we talked about verbosity a little bit, like, you know, rating it between 1 and 3, and, and this is one, again, where, like, human alignment does really start to, start to matter.
 Ben Hylak: And… yeah, this is the loop. It's like, you know, you log, you detect issues, you simulate fixing those issues, and you ship. And you ship, knowing that, like, at least having a little bit more signal that you actually fix the thing before you ship, which is great. And then you kind of just, can just do this loop over and over again.
 Ben Hylak: So, yeah, like, just, like, common footguns with simulations in general, this is, like, outside the scope of our product, like, our product exists to, like, solve a lot of these things, but, like, replaying against live systems, we talked a little bit about, like, where that starts to hit problems, and, like, where the agent will start, like, when you… if you try to do this, the agent will often start to, like, realize it's being simulated. Like, the easy one is, like, there will be data from, like, a week after.
 Ben Hylak: you know, when it actually was ran in your production systems, the agent will see the fact that there's later data that disagrees with the time that was passed in, and it'll be like, oh, I'm being, like, this is no longer the right date. Just trying to serve cache tool responses doesn't really work. Only replaying failures, like, good, but, like, you can overfit really easily, so you also want to be including, like, a random sample when you replay.
 Ben Hylak: Like, important to replay, like, like, taking into account these things that are non-determinism, or non-deterministic, you want to replay it a few times, usually.
 Ben Hylak: And not looking at the traces, like, the big thing. I don't remember what I meant by number 5 here. But, like, not looking at the traces is, like, really, really critical. Like, when you simulate, you want to actually look at at least a few of those traces, and that'll actually tell you more than, like, any… your eval suite will actually tell you.
 Ben Hylak: And… yeah, that is…
 Hamel Husain: Look, I have a question about this. Okay, so we kind of… went… kind of… we talked about simulation.
 Hamel Husain: And so the nagging questions I have in my mind is, like, okay, you have this agent. It might have complicated infrastructure, it might have tools, there might be data, databases… Right.
 Hamel Husain: you know, all kinds of… all kinds of stuff. It may be very complex, And so…
 Hamel Husain: How do you… Okay, like, it seems like a non-trivial task to simulate all of that, like.
 Ben Hylak: It's not.
 Hamel Husain: It's like, what do you do? Like, you take, the person's code, and you, like.
 Ben Hylak: Yes.
 Hamel Husain: fork it or something, and do something? And then, like, the question that enters my mind is, like.
 Hamel Husain: How do we know the simulation…
 Hamel Husain: is faithfully simulating the thing. You know, because it seems like it could be a lot of surface area, so if you could give any thoughts on that, because, like, you've obviously thought about it way more than I have, about how to simulate.
 Ben Hylak: I have thought about it a lot, and you're right, it is not trivial. It is actually pretty, pretty hard. It's actually, I think, one of the hardest problems in the world right now. So, yeah, a couple things. Like, one, yes, our customer is connected to GitHub.
 Ben Hylak: And, like, we are, checking out their entire agent into a sandbox.
 Ben Hylak: We have other sandboxes where their agents are actually executing, keeping state, like, if their agent has sandboxes, we're also spinning up sandboxes to, you know, replicate those sandboxes. And, and we… there's a whole flow of, like.
 Ben Hylak: essentially, like, almost like a smoke testing or, like, alignment flow of, like, we're doing a loop of, like, well, like, let's take, like, it's, again, they're simulations for the simulations and, like, evals for that, to, like, take production traces from main, rerun them, they should equal main, right? And so, before you're running on any PRs or anything, you're just trying to align with
 Ben Hylak: With production, as it is.
 Ben Hylak: And…
 Hamel Husain: That's really funny, like, the answer to my question is…
 Ben Hylak: I know, I know, I know. But that is actually how you do it, right? It's like, you're trying to align to something, you have it, you know what you should be aligned to, and so you just keep doing that, and keep picking fresh things to try.
 Ben Hylak: And so that's the first step, is that, like, we call it, like, the world-building phase. And, and then there's, as far as, like, the faithful simulation, that's what I was talking about earlier, is, like, there's a few ways you can, eval for faithfulness. One…
 Ben Hylak: probably more obvious one that you can do after it runs is to have an LLM, you know, blindly decide, look at all… say you run 20 simulations. You have an LLM blindly decide, essentially, take the original trays, take the new trays, is it a simulation, yes or no?
 Ben Hylak: And, and, if an LLM can correctly guess more than, you know, like, would be statistically, probable that, that it is a simulation, it's a pretty good… it's a pretty good sign that something's wrong. And so there's a few, few tricks like that that you can use.
 Hamel Husain: And then what about data? So, okay, you connect your GitHub, maybe they have some databases and stuff like that.
 Ben Hylak: Yes.
 Hamel Husain: How does that work?
 Ben Hylak: Good question. So, two. Two things. So, there's sort of this, like, this is where, like, the Swiss cheese analogy comes in, which is, like, the previous run of that agent
 Ben Hylak: probably has some good signs of, like, what the underlying databases, et cetera, had, and what you'll need to, see for that question. B is that, like, on the fly, we can, like… let's say you add a new tool for some sort of new database that was, like, never there before,
 Ben Hylak: we can simulate and guess, like, what that database would have. Also, like, we have the ability now for people to connect, like, MCPs to the worldbuilding process, so, like, if people want more realistic data, they can either drop in, you know, JSON files or whatever, or they can, like, connect an MCP that can be used in the worldbuilding process.
 Ben Hylak: And that'll, like, you know, actually pull that production data in.
 Hamel Husain: And the MCP is, like, meant to impersonate The… the… the thing?
 Ben Hylak: It's actually easier than that. It's like, okay, let's say you have, like, some new database. You could connect, like, a read-only, you know, MCP just, like, let's say you're using Superbase. You could, you know, do a read-only Superbase MCP, just so the agent that builds the world.
 Ben Hylak: for that run can pull the data it needs and understand the schemas from Supabase. And truthfully, the schema can be understood from the codebase, but the data, it allows it to populate that data from production.
 Ben Hylak: That is really… we've only really seen that necessary if you're adding, like, a whole new data source internally that, like, you know, that the agent has just never seen before in its life. It's like, if you really want that, simulated faithfully, then that's something you should do.
 Hamel Husain: Interesting. I think this is really fascinating. Yeah, thank you for sharing this.
 Hamel Husain: So, one question, okay, so a lot of people are learning evals in this class.
 Hamel Husain: And the question always comes up, what are good companies to work for? If you are into evals?
 Hamel Husain: Do you have any thoughts?
 Ben Hylak: Well, Raindrop, as you just heard, we have a lot of evals.
 Ben Hylak: No, I mean, I think that there's a range. I think a lot of our customers are pretty good, science and people that, like, care a lot about evals, whether that's Vercel, whether that's, Tolin is, like, there's a lot of people in the consumer space. Obviously, there's, like, you know, bigger companies as well, but, you know, I would be remiss not to, not to mention ourselves here. I think, ultimately, you want to look for companies where…
 Ben Hylak: the real-world cost of failures is, like, high, and I think that it's…
 Ben Hylak: More than you'd expect, actually, like, anything that touches the real world in a meaningful way, or a lot of people, probably the cost of failure is pretty high.
 Hamel Husain: Cool. What kind of roles are you hiring for?
 Ben Hylak: We're currently hiring, most roles, so it's like, sales, head of sales, AEs, and then on the engineering side, we're hiring for, FDEs, we're hiring for, product engineers, and we're hiring for MLEs. So those are the three roles.
 Hamel Husain: Alright, cool.
 Hamel Husain: I think a lot of people in this class will be interested in checking it out. That's why I asked.
 Ben Hylak: Yes, you can DM me, or email me, it's ben at raindrop.ai.
 Hamel Husain: Cool.
 Ben Hylak: Drop in the chat, too.
 Hamel Husain: Probably have some time for some questions. Okay, yeah, thank you for dropping your email in the chat, I'll just pin it.
 Hamel Husain: Okay.
 Hamel Husain: Let me see…
 Hamel Husain: Kevin's asking, is there any situation where simulations might be overkill?
 Hamel Husain: Like, how do you know you need a simulation? And when should you go for it? Should you go for it right away? Should you start something else first?
 Hamel Husain: What do you think?
 Ben Hylak: Very good question. And so, I mean, the very first place that you start is just trying it yourself.
 Ben Hylak: Right? Like, you know, you have it running locally, and just try it, take the traces, ask an agent what went wrong in the traces, and for it to, like, show you the parts that went wrong, some way of, like, annotating and seeing those traces. So, like, that's honestly why we built, like, Raindrop Workshop, like, there was another question about it, like, what it is. It's like, open source tool, runs locally, streams all the traces directly into it, like, do look at your traces locally, like, it's very, very important.
 Ben Hylak: I think it's, like, by far, probably the most important thing.
 Ben Hylak: You can do. Go through every tool call, understand, and ask an agent, like, how could I improve this? How could I optimize this? Like, it really does work. So, that's where you should start.
 Ben Hylak: I think as soon as you're trying to start running evals, now that you have agents, like…
 Ben Hylak: you really kinda need to find some way to simulate it. Now, like, depending on how complex your agent is, like, you may be able to just do this yourself, like, if you only have, like, a few tools, or, like, the data sources are pretty straightforward, or maybe you have a case where, like, you can just hook it up into, like, a read-only version of production and, like, limit the data it's reading, or something like that, like.
 Ben Hylak: definitely, like, Right, I think that, like.
 Ben Hylak: You should always try building out your own solutions here, because you'll… you'll at least understand, the problem that we're solving, or any other, you know, vendor is solving. But, but yeah.
 Ben Hylak: Oh, someone asked about, like, shadow deployments in production? Definitely. Definitely very, very useful, like, running against, running against, like, essentially, especially if you're doing, like, classification, there's a lot of things where it's, like, just, just run them both in parallel. The problem is that, like, agents are really expensive, so…
 Ben Hylak: you know, if you're gonna do a shadow deployment of your agent across all traffic, now you're doubling your costs, and then now you also have to look at those traces still. So, like, it's not totally solving the problem, right? And so, I would think about it a little bit like, simulations are the way to have an action… like, also, the iteration loop
 Ben Hylak: there is ridiculously slow, right? It's like, push to production.
 Ben Hylak: monitor for some time, find the things, then, like, go make another change, push to production. So it's like, I think you want to try to make that, that, that feedback loop as tight as possible.
 Ben Hylak: And then you, you, sorry, the other question from Jeffrey was, like, on, on simulations versus, experiments and, like, A-B tests. So, Raintop actually has, like, we have an experiments, feature that, like, is probably one of the most heavily used things in our entire app, right after issue detection.
 Ben Hylak: it's really good, it's really important. Like, I don't want to, like, de-emphasize the importance of production. It is, like, production is ultimately, like, the source of truth of, like, what is actually happening in your agent, how it's actually behaving, and,
 Ben Hylak: you just, like, want to do something before you get to production, to make sure that, like, people, aren't, you know, bad things aren't happening, so…
 Ben Hylak: Michael asked, how does this compare to LangFuse? I see it also does traces, where does it stop being different? So, I think that, like, the, the, like, trace-wise, like, you know, being able to see your traces, like, that's something that a lot of tools have.
 Ben Hylak: And where this really differs is, like, getting… I think one is, like, proactive, sort of, like, real-time, unsupervised issue detection. Like, something goes wrong.
 Ben Hylak: you'll get an issue that's actually really, really good. So, I think that, like, there's not really any companies that have that in a real or a good way, and, like, that's the kind of thing you don't want to look at, like, oh, it checks a box, like, it has issue detection, like, you know, you could just…
 Ben Hylak: Ask law, like, make issue detection.
 Ben Hylak: having issues that are, like… it's like all evals, right? Like, you could have evals, or you can have evals that, like, are actually high signal and good and tell you when things actually go wrong. So, we have, like, best-in-class issue detection, and then everything else, like simulations, signals, all these sorts of things, like, these platforms don't really have, like, the last thing I'll say about signals is, like.
 Ben Hylak: you can define anything you care about that you want to track in production, and we train models that are really good at classifying those things. Like, you can say, like, where the agent, you know, said it was going to transfer to a human, but never called the tool, and now we're going to train a classifier that's really good at that, both code and semantic evaluations, and you don't pay separately for it, which is pretty cool.
 Ben Hylak: It's great.
 Hamel Husain: Thank you so much for the presentation, people really loved it. I learned something, too. I think you've thought about simulations more than anyone I've talked to in this way, so…
 Ben Hylak: Hope so.
 Hamel Husain: Very, very, very cool.
 Ben Hylak: Amazing. Thank you. Well, if I can, you know, end a day with having taught Hamel, the Grand Master of Evil, something, then my life is complete. But, yes, like, I think that, like, I think simulations are going to be a big deal. We're excited to have been the first company to bring it to market, and, please, like, reach out with any sort of questions.
 Hamel Husain: Alright, amazing, thank you so much.
 Ben Hylak: Cool, take care.
 Hamel Husain: Alright, thank you.
 Ben Hylak: Bye.





















