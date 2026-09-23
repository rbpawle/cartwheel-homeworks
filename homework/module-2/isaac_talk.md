# My Notes

Hamel has worked with Isaac Flath for ~5 years, worked with him for a while. Knowledgeable about AI engineering. Recently, document processing, OCR, etc. He has a workflow for document processing. See how he has designed custom interfaces for error analyses. Also runs a community.

Isaac: Showing lots of annotations and workflows. OCRs and full agent traces. For responses to be useful, need citations. Focus is on documents, tiny niche. OCR product pictures, etc. Anything storing information that is not a database. We need retrieval over documents (often have new stores of them, have to do ML or research generation). Document evals are harder than most for many reasons. (1) Agent problems are usually upstream data issues. You might see hallucination (document says A, agent says B, hallucination). Somewhere along the way, OCR agent got the answer wrong. When you think about which domains do document work, it's high sensitivity, you need citations and confidence that things are right. that's true in almost every good product, but it can be criminally negligent if you don't like, not review a legal document before submitted to court. It feels like a spot-the-difference game--it's hard. It's hard to anticipate which errors are harmless until you understand the end goal. When you do open coding, you need boundary boxes to see where things line up. Lots of these annotation apps are critical. Go into OCR error analysis, open documents, errors there, some nuance, but understandable.

We're connecting eval learnings to workflows.

Retail food inspection report. This document has different patterns in the same table. Pretty clear overall, but there's some inconsistency (#2 on same line as header). Real world data is messy.

He has an annotation app. It gives for each model, the rendered structure from the document, and the original thing on the left. He had Chandra (OCR model) view the document, and then rendered to HTML (sorta--partials). Chandra is a vision model. There are two main types of models. Chain of ML models. Chandra is a vision model. It's looking at the whole thing as a vision model. Seeing page as regular PNG image.

He's going through and noting all the differences/problems between the original and the rendered. Some differences are small, some are critical--this depends on your use case.

(It's interesting how spec issues and interpretation issues are different.)

How do you get source data to be correct?

Most people don't check out OCR--it's rare that somebody does error analysis on a document and says, is the data being processed correctly?

This document is actually pretty good. It's tabular. And it's still fucked up. What if you have charts, etc?

How long did it take to create this interface? An hour to start, an hour or so for incremental changes to it.

One problem with checkbox is it's hard to know intent. Was it not-checked because someone chose not to check it, or because they forgot to check it.



Another document: medical report with watermark

Everything works pretty well, and the watermark (which says "example") is not captured at all. If the question is, what patients did the doctor see, the report should be tossed. Watermarks happen all the time. It might say "confidential", and it might be a government document. Chandra is best of the best, too. So it's missing and that's bad.

You might need different things from the document. You might just want a subset. But you need to look at your data to see what are you missing.

Next step is--what was the reason you want the source data in the format you wanted it? As you work through with agents, all the OCR still becomes important. Upstream error that could cause all this.

Looking at documents as PDF is not solved at all. A PDF is like an image but harder. It has lots of complexities--it has tables, graphs, etc. It has a text layer. A PDF is kind of an image format, but some of the stuff might be stored as text (I think in metadata). You can basically read it like reading an image.

Lots of time you can type in an image in a PDF. How? It's stored as text. Half could be text, half could be hand-written.

Looking at BerkshireHathaway report, with a simple question, how much did costs decrease? In his example, it hallucinated a number. So, why did it get to the wrong answer? The question is, can a better prompt fix this? A better model? We don't know, until we know what the problem was. So we have to work backwards from the wrong answer. He looked at the trace, and found that he was repeating something in the context window. He just "figured it out".

# Transcript

 Hamel Husain: Hey, Isaac. I sent you a Riverside link, if you want to join that too, just for a recording of your face, because Zoom…
 Hamel Husain: Has very poor, quality when it comes to… People's cameras for some reason.
 Isaac Flath: Okay, where'd you send it to me?
 Hamel Husain: In a text and iMessage.
 Isaac Flath: Oh.
 Isaac Flath: Yeah.
 Hamel Husain: All you have to do is, you join the Riverside, and then, like, you mute the audio there.
 Hamel Husain: But this is, again, just for your face, because, like… Zoom has low quality.
 Hamel Husain: There you go.
 Hamel Husain: Okay, I'm gonna mute the riverside.
 Hamel Husain: On my end, I think you're muted. Okay, great.
 Hamel Husain: Just leave it open for a little bit after… It's a…
 Isaac Flath: Yeah, makes sense.
 Isaac Flath: I'm gonna go close my texts out, because I'm… I've been really good about doxxing myself and, like, showing stuff recently, so… that's why I had everything closed.
 Hamel Husain: I'm glad that I'm not alone in that.
 Hamel Husain: When I did that, I was so embarrassed.
 Isaac Flath: I did it.
 Isaac Flath: I was like, well, I was like, I was like, man, I can't believe you did that. And then, I don't know, like, last week, I've done it, like, 4 times.
 Hamel Husain: I feel like… Yeah, it's hard.
 Hamel Husain: This is maybe make a software for ourselves that… you know, obfuscation.
 Isaac Flath: Do you have real-time classification? Is this sensitive?
 Isaac Flath: We'll send all our secrets to Jeff. I guess you can't, because it's, not multimodal yet. Maybe you can. Accessibility features, but…
 Hamel Husain: Okay, let me, okay, we have… we can wait a little bit. I can…
 Hamel Husain: I can let people in, though. I mean, let me get…
 Hamel Husain: Let me actually get pretty here.
 Hamel Husain: Alright, welcome everybody, we'll just, wait.
 Hamel Husain: Like, a few minutes, they'll kick it off.
 Hamel Husain: A lot of models came out today, Isaac. We got, like, new OpenAI ones, Claude.
 Hamel Husain: So, both on the same day, same time. I mean, I guess, like, this happened before, but there's a lot to, think about.
 Isaac Flath: Well, I'll wait a couple days and see, see what people think. Maybe I'll try the…
 Isaac Flath: I don't know.
 Isaac Flath: That's kind of what I tried to do with Jev, but then after… I don't know.
 Isaac Flath: By the next day, it was really clear, it was really useful, so…
 Hamel Husain: Okay, let's jump into it. We can… we can go ahead and kick things off. Okay, so…
 Hamel Husain: I just wanted to introduce everybody to Isaac.
 Hamel Husain: I've been working with Isaac for, I don't know, I think, like, 5 years, 4 or 5 years, I've lost count at this point. I've known him, from open source land.
 Hamel Husain: I've also worked with him at a AI research lab, Answer AI,
 Hamel Husain: And I've just known him as a friend and colleague for this entire time. He's also an… he's also an educator.
 Hamel Husain: He's really knowledgeable about AI engineering. More recently, he's been focusing a lot on document processing, OCR, and things like that.
 Hamel Husain: And he actually… he has a really interesting workflow that he uses for document processing, and it ties in really well with this class, because you'll see how he has designed
 Hamel Husain: Customize interfaces for error analysis, amongst other things.
 Hamel Husain: Isaac also runs a community. I'll put a link to that community in the chat, if you want to check it out.
 Hamel Husain: And also, Isaac, you might be seeing him in the Discord, you could… he's active in the Discord already, you can tag him as well. So with that, I'll just kick it off to Isaac.
 Isaac Flath: Yeah, so I'll be showing a lot of the, as Hamel mentioned, a lot of the annotation apps and workflows that I use, not just for OCR, but also for, like, full agent traces, because usually when you're working with PDFs, documents.
 Isaac Flath: You want to create a research report, or you want to ask it questions, and you want some sort of response. For those responses to be useful, you need to also need citations, so you need to eval those as well, and so we'll get into all of that.
 Isaac Flath: My focus is on documents in general. It sounds like it's a super tiny niche, because people kind of only usually think about OCR over PDFs, and that's a huge part of it, because there's lots of PDFs.
 Isaac Flath: But it could be OCRing security footage, or product pictures, or… or anything like that. And I think of documents as…
 Isaac Flath: Anything that stores information that's not a database.
 Isaac Flath: You know, which is a lot.
 Isaac Flath: So, on top of that, we also need retrieval over documents, because we need to find the right documents. Often we have huge stores of them, and we have to often do some sort of ML or Agentic
 Isaac Flath: question answering or research generation over those documents as well, and so all of that plays in. We'll look at all of that.
 Isaac Flath: I'm a little biased, because I focus on documents, but I think Document evals are harder than most, for a lot of reasons. The first is that…
 Isaac Flath: A lot of agent problems when you're working with documents often are actually upstream data issues. So you might see…
 Isaac Flath: And we'll see how to identify all these, but you might see a hallucination. You're like, well, the document says A, and the agent says B, obviously it's a hallucination. And in reality.
 Isaac Flath: somewhere along the way, the OCR model.
 Isaac Flath: got the answer wrong. And so, it looks like a hallucination, people might tune their prompts, so they say, well, maybe I need, instead of Luna, I need Soul.
 Isaac Flath: to, pull it up, and we find that maybe in a dense financial table, one digit got swapped. And so, all of that doesn't matter if the data doesn't get to the model right.
 Isaac Flath: A lot of times, when you think about which domains often do, Document work.
 Isaac Flath: It's often a lot of really high reliability domains, where wrong answers can be really harmful, like.
 Isaac Flath: Who uses PDFs? It's like, well, medical, and legal, and finance, and governments, you know? So, a lot of times, these are situations where you really need the citations, you really need the confidence that these things are right.
 Isaac Flath: And that's true, I think, in almost every good product.
 Isaac Flath: But it's… it's often…
 Isaac Flath: can be, like, criminally negligent if you don't have it over documents. Like, if you don't have… if you don't fact-check a legal brief before you submit it to the court, that's…
 Isaac Flath: Like, you can get a lot of trouble for that. It's not just… Oops, I'll lose a customer.
 Isaac Flath: A lot of times it's hard to compare. It feels like a spot-the-difference game, because you might have a dense table with 100 values, and then you're like, well, what's wrong? And it's hard to anticipate which errors are harmless until you understand the end goal.
 Isaac Flath: Which we'll look at these as well. And a lot of times when you… even when you're open coding, a lot of times you need bounding boxes to know, like, where these issues line up, and not just…
 Isaac Flath: you know, notes, so you don't have to recreate it. So, all of these make these evals hard.
 Isaac Flath: and mean that a lot of these, annotation apps are critical. So, we're gonna start, I'll go into…
 Isaac Flath: OCR error analysis, we'll do agents over documents, do some error analysis there. We'll look at some kind of examples that are a bit nuanced. All of these will be kind of easily understandable, to everyone, though. And, then we'll talk about how I use this pretty much every day.
 Isaac Flath: I'm doing it this way because…
 Isaac Flath: I thought y'all have gotten a ton of information about evals over the last few weeks.
 Isaac Flath: So I thought connecting that to workflows.
 Isaac Flath: would be most helpful. So let me share my screen.
 Isaac Flath: Okay.
 Isaac Flath: Everyone should see my screen now.
 Hamel Husain: I do.
 Isaac Flath: This is the.
 Hamel Husain: First PDF. Retail Food Inspection Report. Okay, here we go. So this is like a real… this is a real document. It looks like. Where did you get this document from?
 Isaac Flath: I found it online.
 Hamel Husain: America.
 Isaac Flath: Yeah, it's, it's, it's, it's public.
 Isaac Flath: form that I found online. Now, you look at this, and it's like, I don't know, what's hard about this document? It probably looks pretty straightforward, everything's typed up.
 Isaac Flath: You have a table, it's two columns, but it's not…
 Isaac Flath: Nothing's hard to read. But there's a lot of judgment calls, even in this, you know, already. So, there's things like…
 Isaac Flath: These fields have underlines, and these don't. Do you care about that? Do you care, should they all have underlines? Should none of them have underlines? Do you care what the model does? And you might say, no, that's a harmless change.
 Isaac Flath: We'll ignore that. And so, other changes might be harmful. For example, the number of points that each one of these gets, if that's wrong, that's probably…
 Isaac Flath: That probably is harmful. That almost certainly is bad.
 Hamel Husain: And there's groupings here, too. It's like, employee health and hygienic Practices, that's all one group, and that's very subtle.
 Hamel Husain: You can see that as a human.
 Hamel Husain: Like, okay, if you try to extract that data.
 Hamel Husain: I wonder if it's gonna know it's part of one group.
 Isaac Flath: Yeah, and it's almost, and it's difficult, even as a human in this case, is no discharge from eyes, nose, and mouth, so I guess that's not part of this group, right?
 Isaac Flath: But in this case, I guess all of these are part of this group, so there's a little bit of ambiguity, but overall, it's…
 Hamel Husain: Wait, you don't think number 3 is part of that group? Employee Health? I think it could.
 Isaac Flath: Does this count for everything underneath?
 Hamel Husain: That's the way I read it. Yeah, that's the way I read it.
 Isaac Flath: It could be, so then why is this one separate? This one's done differently. And so…
 Hamel Husain: Oh, there, oh, that's a really good point. Interesting.
 Isaac Flath: Now, I do know that number 3 is part of here. Employee health and hygiene, we're seeing proper eating, tasting, and so I know that this is part of here. The point is, is that we have this pattern of, oh, this header goes in the first cell, but it actually belongs to all these cells and rows below it.
 Isaac Flath: Versus here, it gets a row of its own, everything below there is clearly under that group, and so we have…
 Isaac Flath: different patterns in the same table. But again, like, overall, it's pretty clear. There's no…
 Isaac Flath: no handwriting or anything, so… This is amazing.
 Hamel Husain: This is, like, this is how… see, data is like this. It's messy, it's inconsistent, like, it… this is real. The real world has stuff like this. Even if it's not a PDF, even databases have problems like this, where, like, data is, like, kind of messy.
 Isaac Flath: Yeah, so, this is my presentation, by the way, so, we can look at this.
 Isaac Flath: In the annotation app. And so this is the annotation app. I'll do a little walkthrough.
 Isaac Flath: of, of this.
 Isaac Flath: Can I get rid of… Okay, I'll just get rid of that, hopefully.
 Isaac Flath: And so, this is an annotation app. So what do we see here? First, On the left here.
 Isaac Flath: I see the model output. In this case, I'm using Chandra. You can see for this particular food inspection, I've got them for Chandra, and Gemini Flash, and Minor U, Paddle, a whole bunch of them.
 Isaac Flath: I can see this is the rendered output. I can click on raw. This is the raw output of Chandra. You can see it's kind of giving you this XML, HTML format, which…
 Isaac Flath: you know, is nice if you have a really complicated table structure, because Markdown tables don't always do it, so…
 Isaac Flath: If the table structure's really important, Might be something to consider.
 Isaac Flath: And I can look at it in a rendered way. And so then the question is, okay, what do I do? Do I, like…
 Hamel Husain: So just to be clear, this thing you have on the left, it's like, you had Chandra, this OCR model, parse the PDF, and then you… that data that came out, because, like, Chandra, I think, as you marked this XML, you basically render this XML. Now…
 Isaac Flath: Yeah, I mean, it's kind of… it's not technically HTML, because you don't see, like, the HTML opening tag and all this, but you can see, it's like a table, it's HTML. And so you can render it as HTML partials.
 Hamel Husain: I see. And why does it look so much like…
 Hamel Husain: The original document with, like, the spacing and the columns, like, is that…
 Isaac Flath: So Chandra is… it's a… it's a vision model, basically, and so there's… there's kind of two main types of…
 Isaac Flath: OCR models. I mean, there's more, but simplify things. There's kind of, like, pipelines, which are, like, if you think about traditional
 Isaac Flath: ML, where you're like, let me detect the line, and then in the line, let me do, like, a model that will predict what text is in that line, and then now that I have that, let me predict, like, the layout. So you have, like, a chain of, like, traditional ML models.
 Isaac Flath: And Chandra is a vision model, so a vision model is like… it's like giving Gemini a PDF, which we'll look at Gemini in a second, where it's just looking at the whole thing and predicting the output kind of in one pass as one big vision model, and so it actually sees this page. It's kind of treating them almost like
 Isaac Flath: Like it would just a regular PNG image or something.
 Isaac Flath: And so, it tries to replicate it as much as it can. It's predicting that.
 Isaac Flath: Now, we can see some of the things here, like, over on the right, I deemed this not an issue. There are underlines here. These underlines are a bit shorter. I think that's okay. These permit numbers.
 Isaac Flath: The model decided that it added underlines all there, so that's actually a difference. There's no underline for the permit number and expiration date, but I do see them here.
 Isaac Flath: And so, I think for most use cases, it's probably harmless, but for yours, it might be a problem, so you have to think about that.
 Isaac Flath: You know, this inspection type isn't centered, so depending on, like, if you're trying to display this in a really professional way, that might be something you care about. If you're just trying to answer a question over it, you probably don't. And so, there's small differences up there.
 Isaac Flath: And then when we go down here, we can start to see what we have, and so…
 Hamel Husain: I think there's a big difference, actually. Like, when you scroll up a little bit. It's really interesting, right? Because, like, inspection type seems like, at least semantically, the way it's rendered on the left-hand side, it's completely decoupled from its children, R-F-U-C-O, whereas in the PDF, it feels like those are grouped.
 Isaac Flath: Yeah, I would actually… I guess I'd call that an error, so let's… let's annotate it. So here, I'm gonna say this is an error, so I'm gonna click, and I'm gonna draw a bounding box.
 Isaac Flath: I'm gonna write my note.
 Isaac Flath: Inspection type… is, not?
 Isaac Flath: Tied to… The children?
 Isaac Flath: In the model output.
 Isaac Flath: Cool.
 Isaac Flath: And… We could find our inspection type here.
 Isaac Flath: So, let's find this.
 Isaac Flath: Which should be…
 Isaac Flath: Inspection type… through here. Good. And so now this is,
 Isaac Flath: You set me up perfectly to show a real example, it's great. So, what we have here is we've got 3 things tied together, and we kind of… you kind of think of this as open coding, I just wrote a note, I didn't classify it.
 Isaac Flath: But we're tying together a bounding box, a location on the actual PDF,
 Isaac Flath: With our note, because the note only applies to that section, and
 Isaac Flath: you know, sure, I could, like, go look at the PDF and then scroll through the output again every time I look at it, but that's horrible. And so I tied the bounding box to that note to actual lines in the model output.
 Isaac Flath: And so, I can see,
 Isaac Flath: It doesn't do it perfectly, but I at least see, hey, in 6, there's this… there's this error in this table here that I do, and so I can kind of revisit this. And the same thing here, for error number 3, this is an interesting one.
 Isaac Flath: I see this circle, there's very clearly a 1 there. We can go back and see here. It's very clearly, next to signs and requirements, there's very clearly a 1.
 Isaac Flath: However, in the OCR output, there's no one, there's no one there. It missed it.
 Isaac Flath: And we can see this. And if I hover over, I can see, kind of, the source model stuff, just so I don't have to jump back and forth all the time.
 Isaac Flath: And so there's all kinds of these differences. And so in this case.
 Isaac Flath: this seems pretty bad. And so… but even here, it's ambiguous, right? It's…
 Isaac Flath: Should… this is a header, sign slash requirements, there's a points of 1.
 Isaac Flath: Because this is… like, you're using a vision model that can hallucinate, even though it's quite good, you get this issue of, hey, every header, demonstration of knowledge, employee hygiene health, here, protection and contamination, everything it had seen on this page says that headers do not get a point value.
 Isaac Flath: And here, the header had a point value.
 Isaac Flath: And so it decided it didn't need a point value.
 Isaac Flath: So, you might need some domain expertise to say, like, well, should it? Is this actually the signs and requirements? Is there something here that I should be… is there something different about this? And so, is this a…
 Isaac Flath: It's clearly not representing the document correctly.
 Isaac Flath: Is the document wrong, or is the OCR model wrong?
 Isaac Flath: Because it's the only case where a header has a value. And so, for now, I would say.
 Hamel Husain: It's unclear, it's really unclear, yeah, I mean, I don't know. It sounds… yeah, I would say probably that's a mistake in the original document, having won there.
 Hamel Husain: I mean, why would you put it in the header? I don't know.
 Hamel Husain: but I'm also…
 Isaac Flath: about a food inspection.
 Isaac Flath: You know, so it's like…
 Hamel Husain: I mean, it's like, yeah, but if I were to guess, let's put it that way, I'd be like, that seems like an error.
 Isaac Flath: Yeah, no, I agree. I agree. And so…
 Isaac Flath: we get all these differences, where sometimes the headers are in their own cell, and sometimes they're not. This value wasn't represented faithfully, we'll look at others, but the point is, like, even in this case, I know that this OCR model didn't respond faithfully, and if I had a product around this, that would be my first path for resolving that one.
 Isaac Flath: is… I would say, interesting, let me see if this original food inspection report is wrong.
 Isaac Flath: If it is wrong, how do I get the source data fixed? Because this looks like a form that people are walking around with on their clipboards and filling in, I don't know.
 Isaac Flath: So there might be a process there, or hey, maybe there is a reason that this one's goofy, and the OCR model is wrong, and I need to address that.
 Hamel Husain: I love this. Most people, they don't even think about their OCR. They just assume
 Hamel Husain: They give it to a model.
 Hamel Husain: And then they act like it's coming from God.
 Hamel Husain: Because they're just like, okay, here's the data. I'm serious! I'm 100%…
 Isaac Flath: Oh, I know, it's…
 Hamel Husain: No one, like, it's rare that somebody gets out, does error analysis on a document, and says, is the data being processed correctly?
 Hamel Husain: So, this is amazing. I mean, again, this is a real document. Look at how messy it is.
 Hamel Husain: Like, we don't even know what the right answer is.
 Isaac Flath: Now, here's the thing, I picked this document because it actually kind of looks like a regular document. It doesn't even look… it doesn't look controversial at first. It looks like, oh, this is just, like, a regular form, everything's typed, a human can read everything easily, and you still have all these issues.
 Isaac Flath: And so this doesn't get into, like, what if you have…
 Isaac Flath: A chart, a graph, with no labels.
 Isaac Flath: do you guess the values? How do you label that as estimated? What if you have a flow chart? So there's all kinds of things, that are much trickier than this. But this is… this is the start, and it's already ambiguous.
 Hamel Husain: Amazing.
 Hamel Husain: And, I love that, I mean, obviously, so you're doing what we teach people is, like, create a custom annotation interface that is…
 Hamel Husain: fits like a glove with your data and what you're trying to inspect. So can you tell us a little bit, like, how did you create this? Or, like, how long did it take you? Or, I don't know, like, just to give us some insight into this.
 Isaac Flath: Yeah, so how long it took is, it's kind of hard to know how to answer that, because…
 Isaac Flath: The first version probably took about an hour.
 Isaac Flath: But the first version sucked, you know? As most things.
 Hamel Husain: do, yeah.
 Isaac Flath: Yeah.
 Isaac Flath: But then, like, every time I tried to do a trace, it got a little bit better. Like, at first, I just had, I just had open code where I was just, like, writing stuff, and that was it. And then I'd, like, go back, and I'd say… I'd say, like.
 Isaac Flath: this one cell, it is split on the OCR output, and then I'd be like, wait, what cell is this talking about?
 Isaac Flath: I'm like, I have no idea. Like, I don't know what this error is. And like…
 Isaac Flath: And so then I was like, okay, well, I need bounding boxes. And so then I did bounding boxes, right? So I added that at some point. And that didn't take very long, because agents are pretty good.
 Isaac Flath: Most of the time was…
 Isaac Flath: Telling it to quit adding unnecessary labels everywhere.
 Hamel Husain: Yeah. Okay, so you iterated on it.
 Hamel Husain: language makes sense. Like, you just kept asking your agent to make improvements when you found, like, hey, it's like, need something else.
 Isaac Flath: Yeah, and then I was like, oh, I hate looking at this, let me add a rendered thing, because I also probably want to go back to the raw. And then I was like, even here, then I'm like, I hate jumping back and forth to see exactly what the model output is all the time, and so then I added, like, this hover where I can hover over, and it'll, like, highlight that. So yeah, it was like, I don't know, an hour?
 Isaac Flath: At a time, every time I got really annoyed, and I… I don't know.
 Isaac Flath: I do this… because I'm doing this data work every day, basically, it… I get annoyed at things, right? Like, if you only do it, like, once, and you're not gonna look at your data again.
 Isaac Flath: for 4 months until you work on the next feature, then you probably won't care. You'll be like, well, I never looked at this anyway, I don't need to spend the time on it. But if you actually do it all the time, like, I think you should,
 Isaac Flath: Then, yeah, you just… you just get better at it.
 Isaac Flath: So this is the same document with Gemini, and in this case, you know, you can ask Gemini to return whatever you want. In this case, I asked it to return Markdown, and so you can see a Markdown version of this table. You can see it just does one column, and maybe you're like, well, one column is… that's fine.
 Isaac Flath: So, like, it broke these CDC risk factors and approved retails into different ones.
 Isaac Flath: And maybe you say that's fine, that's… I don't… I don't need that exact format. And you can see here, it did do better at this inspection type, but it added checkboxes here, and it added checkboxes here.
 Hamel Husain: Okay, so this is a… this is 3.5 Flash before we were, looking at Chandra, okay.
 Isaac Flath: Exactly. And so here we see all these differences, and it's, again, ambiguous, and, because…
 Isaac Flath: These inspection types, yeah, my guess is you're probably supposed to check or circle one. These, these, things in the actual document, it's, very clear that these are yes or no's, and so a checkbox makes sense, but they aren't on the original document. And the question is, is a checkbox okay?
 Isaac Flath: One of the problems with a checkbox is that
 Isaac Flath: You can't easily put not applicable, especially if you want an agent to fill it in.
 Isaac Flath: Is the checkbox checked or not checked? If it's not checked, is it because someone didn't check, or is it because it's not applicable for this
 Isaac Flath: particular restaurant.
 Isaac Flath: I don't know.
 Hamel Husain: Basically, it's assigning a data type to this field out that is binary, and we don't really know what's supposed to go in that field, honestly.
 Isaac Flath: Yeah, that's right, and that's, again, that's something, you know, in this case, you know, it might be the check… I think the check boxes are probably okay.
 Isaac Flath: But I don't know what all the regulations and whatever are. Like, if you check it as correct, and it's not as good, and it's not good, like, are you supposed to…
 Isaac Flath: If you don't check it, versus…
 Isaac Flath: If it's not applicable, do these points apply the same way?
 Isaac Flath: I don't know, that kind of depends on how the… maybe if they're not applicable, you shouldn't do them at all.
 Hamel Husain: Yeah.
 Isaac Flath: And if you can't check them, that's because you weren't able to get access to it, and that's a market against the restaurant, I don't know.
 Isaac Flath: Yeah.
 Isaac Flath: So, anyway, point is, lots of ambiguity.
 Isaac Flath: I'll go through one more quickly, and then we'll get kind of more into the agent stuff here.
 Isaac Flath: Here's another one. This is, this is, again, I'm picking ones that appear to be very simple. We have a patient name, medical records, alt text.
 Isaac Flath: Bunch of pros here, and we have this watermark. This watermark, says example.
 Isaac Flath: And so, in this case, everything is, pretty,
 Isaac Flath: Everything works pretty well, except we have this watermark, and the actual OCR output, both for Chandra and Gemini Flash, by default, don't capture that watermark.
 Isaac Flath: And so, if the question is.
 Isaac Flath: who… what patients did Dr. Teachwell see?
 Isaac Flath: what patients is he working with? What patients are assigned to him? Then it can answer this question, and it probably should tell them, like, hey, this is an actual report, this isn't a real patient, this is just an example document.
 Isaac Flath: You might say, well, this example document shouldn't be in the dataset at all. It's probably true, but you have the same issue in, legal and finance all the time.
 Isaac Flath: Or government. The watermark might say confidential, and if you're working on a…
 Isaac Flath: an agent over confidential documents, maybe with, like, Anthropic's,
 Isaac Flath: you know, clawed for government, and these are confidential documents, and it answers a question, it'd be really nice to tell the person that these answers do touch confidential documents.
 Hamel Husain: And by the way, these are state-of-the-art OCR, like, Chandra.
 Isaac Flath: Hell yeah, yeah.
 Hamel Husain: This is the best model… this is, like, on the frontier of the best OCR, so this is not, like, an… like, this is real, kind of, error we're seeing. This is not contrived.
 Isaac Flath: Yeah, and so that's government example with confidential and legal. A lot of times, things are marked like draft, not for execution. Like, you're like, hey, I wrote up a contract, I'm gonna watermark it as draft, send it over for review. That might be really important to say, like, hey, what's…
 Isaac Flath: what's the state of this contract? Or, what are the terms with these people? And it might say, like, oh, there's no executed contract, but there is a draft contract marked not for execution that says these terms. And if it misses that draft not for execution, that's a big problem.
 Isaac Flath: Because that's, like, is this a real… is this something we're just thinking of, or is this something everyone's agreed and signed to?
 Isaac Flath: Or…
 Isaac Flath: doing OCR over invoices. Well, if there's a big void watermark, whether it's handwritten or text, that makes a big difference as to what you could do with that invoice. And so, these watermarks.
 Isaac Flath: extremely easy to see. It's not always, guaranteed that
 Isaac Flath: it's just going to, like, happen. Now, you can… you can get these out, you can fix them in a lot of ways, but you can't just assume that your data is just gonna magically.
 Hamel Husain: BOC.
 Isaac Flath: OCR's not solved. That's what I'm saying.
 Hamel Husain: Yeah.
 Isaac Flath: So, what do you do with this?
 Isaac Flath: Well, there's a lot of things you can do. You could,
 Isaac Flath: You can, of course, if you prompt Gemini Flash, just say, like, be sure to include any watermarks as YAML front matter before you OCR the rest of the page.
 Isaac Flath: That's one way to handle it. Like, ask it specifically to look, because it won't look by default, usually.
 Isaac Flath: Another option is to do structured data extraction, and so you can have models that output JSON, and you might not need all this text here, you might just need…
 Isaac Flath: Let me get all this patient name, medical record, date admitted, discharged, attending physician, this example, like, status of the document.
 Isaac Flath: And you might just use a vision model to do structured extraction of text, so that you can, like, search and filter. Maybe you don't need the text. And so there's ways to handle it.
 Isaac Flath: But, but you need to look at your data to find, like, what of these edge cases are you hitting?
 Isaac Flath: Any questions before I go to agent stuff?
 Hamel Husain: Nope.
 Isaac Flath: Alright.
 Isaac Flath: So, okay, so the next step is…
 Isaac Flath: I've been talking about often you want to use an agent to do stuff, or like, usually when you have a document, whether it's PDF or an image or whatever, and you put it in text, you're not like, great, it's in text, that's all I wanted. I saved the file and I don't touch it. You want to do something with it. There's a reason you wanted it in a format that you could work with.
 Isaac Flath: And one of the most common ways to work with that now is with an agent. And so, OCR is one piece.
 Isaac Flath: When you're working with agents, citations are very important.
 Isaac Flath: Getting…
 Isaac Flath: as you… as you work through with agents, this… all this OCR annotation still becomes important, because that's, like, an upstream error that could cause all this.
 Isaac Flath: But it's also important to test, both the OCR stuff and the final answer. So, this is a post that's going out soon. Shameless plug, you can go to my site here, hit subscribe, and you will get this in your email when it comes out.
 Hamel Husain: Definitely subscribe. It's like here. Like, if you have documents in your AI pipeline.
 Hamel Husain: Isaac goes deeper on this topic than anyone that I know. He basically… well, yeah, he goes really deep on, like, hey, this is what can go wrong with document processing, and how to fix it.
 Hamel Husain: So, definitely suggest that. I'll put the link in the chat.
 Isaac Flath: Great.
 Isaac Flath: So,
 Isaac Flath: make a few finishes, and it'll come out in the next few days, but this is the first example, and they build in complexity, but, you know, you might have just a question answering that says, how much did Berkshire Hathaway's insurance and other costs decrease from 2023 to 2024?
 Hamel Husain: So I have a question for you, Isaac, because this comes up, it's the same thing about evals. Whenever you present a problem in AI, everybody wants to know, but what about this tool?
 Hamel Husain: Is there a silver bullet with AI? Like, surely, like, there's a vendor, Reducto, Azure.
 Hamel Husain: you name it, somebody that's solved this problem, where you can just close your eyes, submit a PDF,
 Hamel Husain: And it's… and it's, like, really good. And you don't have to worry about anything, you don't have to look at the data. Is that… is that what you… does that exist?
 Isaac Flath: So, no, not at all. And we know this because in much simpler… like, so…
 Isaac Flath: The thing is, is like, if you think about what is a PDF,
 Isaac Flath: A PDF is an image, except much harder, because not only can it handle scanned images, it often has much denser information and tables, and it can also have a text layer on top of it. So it's like, you take all the complexities of working with text.
 Isaac Flath: And if you use coding agents to code, you've probably gotten annoyed and mad at how bad it is at text sometimes. They do incredible things, I use them a lot, but they aren't…
 Isaac Flath: you know, it's not like I can go to, you know, Astra, or whatever the new Clod model is today that came out, or whatever, and just say, like, build me a SAS, you know, and expect.
 Hamel Husain: And just to drill into what you're talking about here, when you talk about PDF, there's multiple layers to a PDF. So, like, you mentioned text layer. Text layer is, like.
 Hamel Husain: Can you describe what a text layer is, exactly, for people that might not know?
 Isaac Flath: Yeah, so a PDF, it's kind of an image format, but some of the stuff in a PDF might be stored as text, where you can just
 Isaac Flath: Basically, extract it, without reading it as an image.
 Isaac Flath: The problem is, is that some stuff can be stored that way, other stuff can be scanned, and most PDFs have…
 Isaac Flath: Some aspect of both.
 Isaac Flath: And so, like, if we think about…
 Isaac Flath: I don't know this company, I don't endorse this company, I don't know anything about them, but,
 Isaac Flath: If you think about this, right?
 Isaac Flath: Can I just get an image? Okay, so if you think about this, people have probably filled out a W-2 before. A lot of times you go on a platform, and if you need to fill some of this out, or you get these.
 Isaac Flath: If you… if you need to fill some of these stuff out, a lot of times you can enter text, and you tab to the next field, enter text, and so you can type.
 Isaac Flath: And how can you type in an image? It's because it's getting stored as text. Another case is, if you have a W-2, if you're an employee, and you have a W-2,
 Isaac Flath: and you're like, hey, I want to save this for my records, because I got it mailed to me, and you scan it, there's no text, it's just an image, you just scanned it on your PDF. And so, the same thing…
 Isaac Flath: sometimes you could extract this completely from just text, reading text very quickly, and sometimes it's like, well, it's just an image, I have to, like, OCR and, like, look at it as an image and process it. And both can happen, and…
 Isaac Flath: Half of it could be text, and the other half could be handwriting, you know? This could be handwritten if it's a very small
 Isaac Flath: small employer, they might have written stuff out. And so, you would just have… So much stuff there.
 Hamel Husain: Okay, and so when you fill this out, like a form, like a PDF, and you type it in on your computer and save it, and then you, like, maybe sign it by hand.
 Hamel Husain: Does that mean, like, some of the data is in the text… in the… in the text layer, and some of the data is in the image layer, or, like, how does that… Yep. Okay.
 Isaac Flath: Yeah, and you probably need to get both out, you know? So…
 Hamel Husain: Okay, thanks for… thanks for taking us through that.
 Isaac Flath: Yeah, absolutely.
 Isaac Flath: Okay, so we have this question, a very simple question. It needs to give an answer. To get the answer, it needs to give me a citation, and it clicks at two numbers, and it needs to say, how far off are these? So, simple subtraction.
 Isaac Flath: And in this case, the agent got it wrong. I think I was using, like, Sol. So, pretty good agent, got it wrong. It's $3.5 billion. If you click on math, you might see…
 Isaac Flath: 75, 76, 77, 78, it should be a little over 4 billion.
 Isaac Flath: So it's wrong. And so, that can be a top-level eval. You can say, like, hey, when I ask this question, does the right 4.134 billion show up in the agent's response? Great, you can eval that, you can write a test for it if you want, whatever you need to do.
 Isaac Flath: The question is, why did this happen? And this is where the annotation apps make it… are really helpful. And so, we'll see this. This is, like, an abbreviated version, but we'll see this exact actual thing. We have a question, we have an expected answer, and we have an agent answer. And so, very quickly, I can see…
 Isaac Flath: Cool, on this question, it failed. It got the wrong answer, I have a citation, it circled some boxes, cool, those are the right boxes.
 Isaac Flath: Great. And so, the first question is, why did it get this wrong when it had… when it seemed to have the good citations?
 Isaac Flath: And we might say, well, maybe it just hallucinated a number.
 Isaac Flath: Maybe it,
 Isaac Flath: maybe just didn't find the right document, and so I just didn't have the information, because maybe the citation is, like, an after-post-processing step. And so it's like, it's not clear, you know, why it got to this wrong answer. And so…
 Isaac Flath: the question is, it's like, can I fix this by writing a better prompt?
 Isaac Flath: Can I fix this by… maybe I was using, I don't know, a super small local model. Can I… can I fix this by just paying a bit more and moving up to Terra? You know, GPT Terra? I don't know, because I don't know what the problem is.
 Isaac Flath: And so, to do that, I kind of start from the back, from the… from this… from this end point, and work backwards, and I say, okay, I have the wrong answer. Is the wrong answer, like, a model hallucination, or is it just repeating something in its context window?
 Isaac Flath: Cool. It's repeating something in its context window. Great. I immediately know that just prompting better, or going to a more expensive bottle, or trying this is not going to help.
 Isaac Flath: Because the model did what it… it got information, and it told me the information.
 Hamel Husain: something in its, context window. How did you do that?
 Isaac Flath: trace. I look at the trace.
 Isaac Flath: So, like, for example, I'll just jump ahead real quick.
 Isaac Flath: So, in my app here, I go and I just look at the trace, and I look at the tool calls.
 Isaac Flath: And I figure it out. I say, like, oop, there we go. It's in there.
 Isaac Flath: And now I can use, like, a Command-F to, like, search, like, here's the wrong value reported.
 Isaac Flath: Can I look for 3.5, or whatever number I'm looking for?
 Isaac Flath: exist in the trace? And I could say, like, oh, it is in the trace, and then I could read around that to jump to it quickly. But you would look at the trace and say, it is in the model's context window.
 Isaac Flath: So we can rule that out.
 Isaac Flath: So the next question is, well, how did it get there? How did the wrong information get there? And it could be from a prompt, maybe it was hard-coded in a prompt, it could be a retrieval tool call, like, maybe it was, like, templated into the prompt for you. In this case, I'm looking at the trace, and this is just an example.
 Isaac Flath: I say, well, there's a retrieval tool call it came in from.
 Isaac Flath: Cool.
 Isaac Flath: So that leads us to the next question.
 Isaac Flath: Is this wrong data there because retrieval failed and gave me the wrong page or document?
 Isaac Flath: Or is the wrong data there because it retrieved
 Isaac Flath: the right page, but it was wrong. And based on looking at this trace, I say, oh, okay, well, the data it retrieved was wrong, it got the right page, it brought it in, something was wrong.
 Isaac Flath: And then I want to know why is it wrong?
 Isaac Flath: You know? Is it that the source PDF was wrong, or was there, like, an extraction error? And I can say, oh, there's an extraction error. The source PDF does not match the extracted model output. And so now I can know exactly where this issue is.
 Isaac Flath: And I could work on formulating a little test around this. Maybe I… maybe I, take the text, run it through a model, I can use Jev to, like, do a structured extraction for all these values.
 Isaac Flath: from the text, because the text, I mean, that would be a very easy task, like, just take these values from text and extract them with Jev.
 Isaac Flath: And I can, like, if I sum all these up, does it equal the total?
 Isaac Flath: or not.
 Isaac Flath: That's possible that, like, one value is 100 too big, and another value is 100 too small, and therefore the test still passes, and it's theoretically possible, but in practice.
 Isaac Flath: That would catch most of them. Like, do all these numbers sum to the total, and if any one number is off, was misread wrong, that test will fail.
 Isaac Flath: And so, that gives you, like, a fast test you can do without having, like, rerun the whole agent loop over and over and over. So that's… that's kind of what…
 Isaac Flath: I'm building towards here. Does that kind of make sense?
 Hamel Husain: Yeah, that makes sense. So you have, like, you basically have this eval. You're, like, trying to…
 Hamel Husain: You're basically trying experiments
 Hamel Husain: After you say… you're gonna get the data out, you're gonna try experiments to see, like, okay, how can you get the right answer? But you're doing some root cause analysis to say, like, okay, kind of just, like, process elimination.
 Hamel Husain: Okay, like, how did we arrive at this number?
 Isaac Flath: Yeah, and now I know that this question is wrong because my OCR model failed.
 Isaac Flath: And maybe… maybe all of them. Maybe… maybe 80% of my failures are actually just because my OCR model failed, in which case…
 Isaac Flath: Prompt tuning is just a waste of my time right now.
 Isaac Flath: So it depends. And so, in this post, which again, you can subscribe if you want it, I'll go through a medical example, which is a little more complicated, and then I'll go with, like, a floor plan, like, sink double counting, thing as well. So,
 Isaac Flath: Check that out.
 Hamel Husain: And do you have a gallery or something that shows, like, all these kind of different kinds of failures? I think, like, can you show us?
 Isaac Flath: Yeah, I do. So,
 Isaac Flath: I don't show all of them, because I don't… like, I use, I use this as an internal,
 Isaac Flath: benchmark.
 Isaac Flath: And I don't want it to get,
 Hamel Husain: You don't want it to get benchmaxed.
 Isaac Flath: Yeah.
 Hamel Husain: Yeah.
 Isaac Flath: Exactly. So, yeah, and so you can see this looks a whole lot like, my annotation app, you just can't draw bounding boxes, but yeah, it's… there's stuff here.
 Isaac Flath: And I still find stuff as I go through this, like, stuff like this is really hard to, like, get everything right, you know?
 Isaac Flath: But yeah, I have some here. Or like this, how do you turn this into text, and how do you make sure
 Isaac Flath: Like, do you make a JSON graph? Like, it's not… it's not clear what the Bright representation for something like this is, so…
 Isaac Flath: Okay, so let's look at some actual agent things. So, we looked at this, I can see a very simple example, which, we'll look at a wrong one here soon.
 Isaac Flath: How much is the underwriting fee on a loan estimate? We see an expected answer of $1,000, an agent answer of $1,000, right? I have a citation here.
 Isaac Flath: You can decide, is this granular enough? For me, I think this is granular enough.
 Isaac Flath: Like, this is the 1097, it circled the whole table.
 Isaac Flath: I'm happy with that. Maybe you want it exactly at the right row? I don't know that that would really help that much, but…
 Isaac Flath: Depends on your application, right?
 Isaac Flath: So I call this a pass.
 Isaac Flath: I do use Jev in several places in my, thing, like, I, I, I…
 Isaac Flath: this is a kind of nice pass, where it… Jev basically predicts, is this… does the citation…
 Isaac Flath: Is this answer that the agent gave, supported?
 Isaac Flath: by the citation, does the citation contradict it, or is it kind of just unsupported in general? I used to just have a test. This was like a slight upgrade, right? I used to have an automated test that said, does a citation exist? Like, did it return a citation?
 Isaac Flath: And that would be, like, a thing, and this is just a little bit nicer. It just…
 Isaac Flath: looks at the value and sees if it supports it. So, I use Jev in small ways to give me
 Isaac Flath: visual things. I still… I still have to look at the data, doesn't… but it speeds me up.
 Isaac Flath: Cool, so in this case, I'd be kind of done. But what else can I do here? I have these pages and bounding boxes, this is this view. I can look at just the PDF, this is the actual, full extraction text, and so if I'm really getting into weeds, I can look at that, and I can look at this trace, and so I can see…
 Isaac Flath: what it read. We can see it read different parts of this loan estimate JSON, which… this is an output from a Sreya model, which is another OCR model, and I can see the final answer.
 Isaac Flath: We can see the citation is block ID.
 Isaac Flath: And so, this is where I can look in and dive in to say.
 Isaac Flath: How do the information get there if I need to?
 Isaac Flath: Now, in other ones, we can see,
 Isaac Flath: we can see here, you know, Jeb says, not established by cited text. And I look up the citation, and I'm like, yeah, that doesn't seem great. And so this is an OCR failure.
 Isaac Flath: And so I can see the citation is this entire form.
 Isaac Flath: This would probably… and this… all this text would probably immediately jump me to say… I would kind of skip some steps, because I'd be like, this looks very suspicious, you know? So I would say, rather than going through the full thing, let me just jump and see if citations… if the OCR process is wrong.
 Isaac Flath: And I can see that, like.
 Isaac Flath: this doesn't look right. Like, this clearly is not a great format for this form, right? I would say this OCR fail.
 Hamel Husain: Yeah, it's just, like, really mangled, and it's.
 Isaac Flath: It's like.
 Hamel Husain: maybe putting field names inside data. It's like this text field is just, like, trying to just shove stuff in there. That's not a great data format to parse. Like, you wouldn't want, like, if you had to parse that big text field.
 Hamel Husain: It would just be, like, really brittle and error-prone. This is not the way you would want to go about it, I totally agree.
 Isaac Flath: Yeah, and so I'm like, okay, well, I think this is probably, probably the issue.
 Isaac Flath: Let's look at another example here. I think I got one here.
 Isaac Flath: See, I put a head pinch.
 Isaac Flath: Let's see here…
 Isaac Flath: So here's another one. So, up here, I can change between different setups. Basically, what this allows, this whole document
 Isaac Flath: data set is, is there's three parts to this, and I've kind of talked about this, but not explicitly here, is there's an OCR process. I take the PDF, and I get it into text that I can work with, so that's one part.
 Isaac Flath: There's retrieval, I need to find the right document.
 Isaac Flath: With the right information.
 Isaac Flath: In this case, you know, find the right document. And the third thing I need to do is, I need to… I have an agent loop. And so these are kind of the three big parts of this… this particular question answering thing.
 Isaac Flath: And so this, lets me…
 Isaac Flath: I can change the OCR model, I can change the retrieval approach, whether that's just using grep, or using a semantic search, or whatever, or SQL queries.
 Isaac Flath: Or I can change out the agent harness, whether I use Pi or Codex or…
 Isaac Flath: A custom one, or the prime agent, whatever you want to do.
 Isaac Flath: And so in this case, I said, well, let's do OCR,
 Isaac Flath: By just giving it, Tesseract, which is a very simple, like, OCR tool that runs locally as a CLI, and, bash tools that let it, like, crop and zoom. And what happens?
 Isaac Flath: And so we can see this is a pretty damn specific citation. We see it gets the answer right, so this is cool, right?
 Isaac Flath: And we look at this trace here.
 Isaac Flath: And we can see what it's doing. We can see it's, like, going through, it's doing, like, resize and crops and conversions, and it's, like, piping all this stuff out, and it's, like, grepping through outputs.
 Isaac Flath: You know, and it gets to an answer. It gets to it…
 Isaac Flath: in a really expensive way, and really slow, but it does work. And so…
 Isaac Flath: In general, that approach gets pretty good results.
 Isaac Flath: You know, you also are probably gonna take about 10 times as long on the agent loop, so…
 Isaac Flath: Depending on what you want to do.
 Isaac Flath: And so, yeah, it just does crop and zooms, and just, like, keep zooming around and cropping. And it'll get into a loop. It'll just keep cropping things and OCRing things indefinitely, often. Like, sometimes it's, like, to answer a simple question.
 Isaac Flath: you know, it would run for 45 minutes and burn, you know, like, $20. Oh, wow.
 Hamel Husain: So it's like, there's no magic bullet here.
 Isaac Flath: I answered a question that I knew wasn't in the dataset, and I was like, okay, let's see if it tells me it's not there. And it just… and when I gave it all these, like, small tools, it was like, oh, there's always more it could try. And so it kept cropping and zooming and whatever on maps.
 Isaac Flath: And so, yeah, so I compare those.
 Isaac Flath: Let's look at this. So this is, this is actually using the Prime Agent. This is, literally how I evaluated the Prime Agent when it first came out.
 Isaac Flath: And so, we'll just do it.
 Hamel Husain: Can you tell us a little bit about the Prime Agent? I heard it for the first time.
 Hamel Husain: Yesterday on a podcast about, like, a new Asian harness. Can you tell us a little bit about it?
 Isaac Flath: Yeah, so the, so the main idea is that… what if, like, I would say.
 Isaac Flath: There's a few parts of it. One is, like, it's this kind of self-learning thing.
 Isaac Flath: but in terms of, like, tool use, it's kind of like, what if it only had one tool, and that tool was Python, you know? And it would all…
 Isaac Flath: Late.
 Isaac Flath: Yeah, we can see exactly how this project.
 Isaac Flath: And this is using… Yeah, and so, we had this prompt.
 Isaac Flath: And let's see how it solved it. So, it started by saying, let's look at the directories, let's see what relevant documents we have. These were, like, OCR outputs saved to disk.
 Isaac Flath: We can see what it did. It imported a whole bunch of stuff.
 Hamel Husain: There's the idea that this Prime Agent doesn't have tools, it just has the ability to write code.
 Isaac Flath: It's basically just Python, yeah?
 Hamel Husain: Interesting.
 Isaac Flath: And then it writes all this, and it, like, loops through everything. It's, like, printing the length of files, just like you might in a Jupyter notebook.
 Isaac Flath: You know, and then here, it's like, oh, let's look at content message, and let's, like, open each one, and then, like, search for a different thing, and, like, let's lowercase it all, and let's see if transfer tax is in this, or if loan estimate is in the substring, right? Like, it's like…
 Hamel Husain: I'm really skeptical, like, if you showed me this is the way you want to solve this problem, I'd be like, I don't know about this. But…
 Isaac Flath: Yeah, I would say it didn't do as well as, Vanilla Pie Agent, and it cost about 3 times more, so…
 Hamel Husain: You're right. Interesting.
 Isaac Flath: But, like, how would you know that unless you looked at this, right? Yeah.
 Isaac Flath: And so, in this case.
 Isaac Flath: The expected answer is none. The transfer tax amount is blank.
 Isaac Flath: Agent said, hey, there's $0 in transfer taxes.
 Isaac Flath: It gave this citation, which is important. As I mentioned, if…
 Isaac Flath: if I have to look through the whole dataset myself manually to, like, verify if this answer is right or not.
 Isaac Flath: And more importantly, if your user has to do that, then, like, the whole thing's garbage, because they're just better off doing it themselves. So, I'm a big fan of visual citations.
 Isaac Flath: And we can see here, transfer taxes is empty, and the question is, is like, is empty… is it okay to represent this as zero, or is empty… should it say there's… there's no transfer tax, it's empty?
 Isaac Flath: It's a judgment call.
 Hamel Husain: It's, yeah, I'm here.
 Isaac Flath: Okay.
 Hamel Husain: I'll say it's probably fine, right? What do you think?
 Isaac Flath: I marked it as a failure, but yeah, it really depends on your, your end use case, you know? Sometimes zero and blank is the same thing, and sometimes it's not.
 Isaac Flath: So, it kind of requires a little…
 Hamel Husain: Domain knowledge, yeah.
 Isaac Flath: Exactly.
 Isaac Flath: Cool.
 Isaac Flath: Alright, so… great.
 Isaac Flath: So that kind of covers the… that.
 Isaac Flath: We mentioned signatures before, so think about this again.
 Hamel Husain: I can barely see some of these signatures, like, what is going on?
 Isaac Flath: Right. That's the thing. What do I do with these?
 Isaac Flath: Do I go back to source documents? Was this just scanned a whole lot of times, or did someone try and erase the signature?
 Isaac Flath: Did Mark pick tech? Did he accidentally sign the wrong place and be like, oh shit, let me erase that and put it back? I don't know.
 Isaac Flath: You know, why is there a date? There's a different date attached to these, these were earlier, so… why are these missing? And so…
 Isaac Flath: If this is at the end of the contract, is this contract legally enforceable? Is it enforced?
 Isaac Flath: I don't know, like…
 Isaac Flath: what do I… like, how do I mark this? Do I say there's a signature? Do I say, is this… is this document?
 Isaac Flath: Signed or not?
 Isaac Flath: do I… do I do, like, a percent likelihood that this is signed by Sean Heckler?
 Hamel Husain: Okay, I'm gonna take a screenshot of this, I'm gonna put it… I'm just gonna do… I'm just gonna put it into, like, Gemini, and say, like, is this signed?
 Hamel Husain: Just out of curiosity. I'm gonna, I'm gonna ask.
 Isaac Flath: And if it says yes or no, it's like, do you trust it? Probably not.
 Isaac Flath: You know?
 Isaac Flath: And so there's all kinds of, like, ambiguous cases like that.
 Isaac Flath: And these… these aren't ones that I made in order to, like, create ambiguous cases, these are ones I just… I just saw.
 Isaac Flath: So,
 Isaac Flath: Couple last things, all of this ends up, I use this all the time to create a document news feed,
 Isaac Flath: I know I'm gonna dump a whole bunch of stuff on there, so if you're interested in what goes on in Document News as things come out, I post stuff, I've got a whole bunch more to record today, new models, and when you see these models, and see my takes on them, I don't always go into the details of exactly how they scored on my benchmark.
 Isaac Flath: But I always try them, and this is how I evaluate them. So this is how I stay on top of things. New bottle comes out, I run them through all of them, I can annotate, I can quickly look at traces, because I have a nice annotation tool, and then I can post something that, you know.
 Isaac Flath: Where I'm not, you know, just talking out of my ass.
 Hamel Husain: So if you, yeah, if you're doing OCR, and you're, like, wondering, is this good?
 Hamel Husain: Isaac has probably looked at it.
 Hamel Husain: And he's probably done some evals on it, and he's probably even written an article or talked about it, and you can find it on this page.
 Hamel Husain: It's very… it's kind of niche?
 Hamel Husain: But, like, then again, there is nobody… I mean, like, yeah, it's very specific, like, he is going deep on this OCR thing. And, like, it is deceptively, like, a very important problem, because…
 Hamel Husain: A lot of people's company data, et cetera, a lot of stuff lives in documents like PDFs. And as you see.
 Hamel Husain: it is a really large failure point. Like, it's… things can fail very easily here.
 Isaac Flath: Yeah, here's a… here's a GitHub issue that was, you know, just recently closed in one of the state-of-the-art pipelines.
 Isaac Flath: They're like, this… this is extracting rock. Like, it extracted it, but now it's like, it saw all the,
 Isaac Flath: you know, all the, technical diagrams, and it started using superscripts and subscripts for lots of things, like it was a formula. It's like…
 Isaac Flath: It's a weird error. So you run into things like this all the time.
 Isaac Flath: This is the kind of stuff I look at for the, I have to use Google Translate for this, but for the newsfeed.
 Isaac Flath: So yeah, so that's,
 Isaac Flath: That's pretty much… that's pretty much it.
 Isaac Flath: If you want to learn more, here's a bunch of stuff. How to choose an OCR model, document answers, you can check. Talks about, this stuff. This is by Joe Barrow, this is really good. Number one question that people ask is, like, what model do I pick?
 Isaac Flath: You know, now you know.
 Hamel Husain: Can you copy and paste these links into the chat?
 Isaac Flath: Yeah. There's this post, which is coming out soon.
 Isaac Flath: I'm not gonna give that to you yet, because it's not quite done, but…
 Isaac Flath: If you want to know when it's done, subscribe.
 Isaac Flath: On the website. And then, I'm co-teaching a one-day intensive course. With that, you're gonna get 30 days of support, which is, like, unlimited Q&A on a, like, a private forum, and then weekly office hours.
 Isaac Flath: comes included with that, and then so far, we've got about $700 in OCR credits from vendors, and the course is not $700, it's cheaper than that. Probably have more.
 Isaac Flath: There's a link to that.
 Hamel Husain: Okay, yeah, you're gonna put it in the chat.
 Isaac Flath: Yeah.
 Isaac Flath: Where's the chat? Chat, chat, chat, chat.
 Isaac Flath: We am failing to find the chat.
 Isaac Flath: What the hell?
 Hamel Husain: Sometimes you have to stop sharing, or I think you have stopped sharing, and then it's…
 Isaac Flath: Oh, there we go, okay.
 Hamel Husain: There you go.
 Hamel Husain: I'll pin it.
 Isaac Flath: Cool.
 Hamel Husain: Does anyone have any questions? Do you want to take questions?
 Isaac Flath: Yeah, I can take questions.
 Hamel Husain: Alright, let's open the floor to questions.
 Hamel Husain: You can raise your hand. Let me, let me make sure you can raise your hand, one sec.
 Hamel Husain: okay, now you should be able to do that.
 Hamel Husain: Alright, Shirong.
 Shrirang Moghe: Mute button. All right, got it. Hey, Isaac, thanks. Hamel, thanks. You've done P&ID, kind of OCRs,
 Hamel Husain: B and ID?
 Shrirang Moghe: PNID's process and instrumentation diagram, these are, like, used by Chevron and all these gas stations. So, piping, valves, and all of this. There's reams and reams of… there are so many old PDFs out there, you can't believe that, and tons of money locked into this.
 Shrirang Moghe: There was a freeze that happened about 3 or 4 years ago, remember, in Houston, where, you know, things froze up, so they didn't even know where the shutoff valves were.
 Shrirang Moghe: And we got some of the contracts to write, OCR, some of these P&ID diagrams, and come up with a graph database. And struggled with YOLO, was training YOLO for all these,
 Shrirang Moghe: But it's an OCR problem too, and YOLO was one of the models actually used. So I just want to know whether you have struggled with YOLO, or SAM2 or any of these.
 Isaac Flath: Yeah, there, it's actually interesting. I didn't expect this to be the case, but, probably about a third of the questions that I get
 Isaac Flath: are on blueprints, or, like, schematic diagrams for, like, electrical diagrams, or, like, floor plans for construction, and, like, stuff like that. So, I get questions about that stuff all the time. I'm actually working on, I'm gonna be hosting…
 Isaac Flath: Someone who's been doing that work,
 Isaac Flath: for clients, like, building these systems, very recently. It's a company called Obelisk, and so I'm gonna host them on a talk on what they're doing there, which is pretty good stuff.
 Isaac Flath: But yeah, a lot of the times the vision models are pretty bad at reading these, and so, especially when you have specific questions, and so it depends on how targeted your…
 Isaac Flath: data set is. Like, you know, if you have… if all of it is kind of from the same firm, so to speak, or the same company, a lot of times their symbols are standardized enough that you can…
 Isaac Flath: grab images of all the different symbols, and then, like, rotate them, and then do, like, a comparison, just with, like, OpenCV, and find them all, and do bounding boxes, kind of the old-school way, for symbols, and then you can pass all that information into a VLM and get much better results.
 Isaac Flath: But if you have, like, a big data set, and it's from, like, lots of different contractors and companies.
 Isaac Flath: A lot of times they're symbols.
 Isaac Flath: I don't know, people do… like, I don't know why they're not as standardized as they are, but…
 Shrirang Moghe: they don't match, and then that's where the whole trouble starts, yeah.
 Isaac Flath: It's a huge challenge, though. And then there's, like, how do you draw…
 Isaac Flath: diagrams, like, how do you fill in spaces in the rooms and then get dimensions? And a lot of times, I don't know if you probably know this, but a lot of times.
 Isaac Flath: You'll have multiple views of the same… Area.
 Shrirang Moghe: Yes.
 Isaac Flath: Because you might have…
 Isaac Flath: Yeah, so, like, one might be focused on… for construction, and one might be focused just on plumbing, and another one on electrical, and another one top-level view, and one's like, okay, let's show it…
 Isaac Flath: Where we're gonna show the floor above it, and then we'll show where this fits in. And so you might have multiple views of the same thing, and then you have to, like, dedupe all of those, to not double count. So it gets very tricky.
 Shrirang Moghe: Makes sense. Alright, thank you. We ended up building a draft database out of that, but…
 Shrirang Moghe: to answer questions, but essentially, the YOLO model actually, didn't work that well, so it continues to be a problem, yeah. Thank you. Thanks so much.
 Isaac Flath: No.
 Hamel Husain: Iqbal.
 IqbalBhatti: Hi, yeah, thank you for the talk, it was very informative. I was very curious, because I'm facing the same kind of problem. I was just wondering, how do you marry up those JSON selectors with the bounding boxes? Is it a second pass? Is it…
 IqbalBhatti: just something that you instructed to the LLM to begin with, and did it just come up with something accurate? Or did you run, like, some more deterministic tools on it?
 Isaac Flath: So you're, you're asking when we get the answer, how do we get the bounding boxes with a citation as well?
 Isaac Flath: Yes, because…
 IqbalBhatti: I saw that there was a JSON representation on the left, and then inside your IDs, you had JSON selectors, and then you had bounding boxes in the same.
 Isaac Flath: Yeah, in this case, it was something that I asked the agent to do, so, like, as it gave the answer, I wanted it to list out all the citations as part of that answer. You can do it in a second pass, and sometimes that's good. The…
 Isaac Flath: Because you can get more accurate citations, but the really hard part about that, and why I try not to decouple them.
 Isaac Flath: Is because the agent can make an answer.
 Isaac Flath: And then you have to make sure that only the stuff that was in context for the agent who answered the question, only that stuff is passed to the model, the second model, to get citations. And so you kind of have to aggregate all the stuff from
 Isaac Flath: all the retrieval tool calls together, and then cite those. Because otherwise, you might get an answer, and then the next model might say, well, the right answer is here, might find something different, and cite a different document that was never in the agent's context window, and that can be really confusing. So, I try and prompt and have the agent do that. Now.
 Isaac Flath: If you're extracting it as… if your OCR model is extracting it as markdown, which some do, then it's a little tricky, because your citation might be trying to do string matching.
 Isaac Flath: Whether it's, like, a header or, like.
 Isaac Flath: we'll just put a string, and then we'll… we'll do that. If you're doing something like Chandra, which returns,
 Isaac Flath: you know, HTML, then, often it's a lot easier, and a lot of models of these VLMs will include block IDs, and so you can ask it to cite just using the block ID from the document, but usually you want them together, but not always.
 Hamel Husain: Alright, we can take one more question, so we'll go with Tommy.
 Tommy Crumrine: Hey, thanks so much for all the knowledge,
 Tommy Crumrine: I was curious if there's ever… do you ever, like.
 Tommy Crumrine: keep using more traditional, like, Tesseract OCR tools, or is it kind of all moving to, like.
 Tommy Crumrine: more of the model-based ones. Yeah.
 Isaac Flath: Yeah, so Sreya is more like, it's not a tesseract, but it's, like, it's a pipeline. So there's two big things, it's like the pipelines are…
 Isaac Flath: Very small, fast models that, can often run locally, and those are really popular when you need low latency, low cost, and they work really well in a lot of cases.
 Isaac Flath: They don't generalize as well to, like, out-of-domain stuff.
 Isaac Flath: But you can also, like, tweak individual parts, and so…
 Isaac Flath: you know, for example, you have, like, a layout detector model that just detects the layout, and then you have, like, a text reading that just takes one section of the layout, just reads text from it. And so you have these small models that are much more like the
 Isaac Flath: Tesseract feeling, they're just kind of a chain of them.
 Isaac Flath: And it depends on… I mean, it depends on the complexity of your PDF.
 Isaac Flath: And so, if Tesseract works, like, if you have a pretty straightforward, like, legal document, and, they're just contracts, and you don't really need to worry about the signatures, you don't really need to worry about…
 Isaac Flath: having, like, really complicated table layouts, or dense, or you don't have to worry about, like, people scanning something, like, 10 times, and then it's, like, super crusty… crusty, then, then yeah, I would use TestRact. I mean, I would use the cheapest model I… fastest model I could.
 Isaac Flath: These bigger models are coming because…
 Isaac Flath: There's more and more people are trying to get…
 Isaac Flath: like, a handwritten intake form that a patient filled out with their pen that…
 Isaac Flath: you know, you can barely read their handwriting as a human. And they, like, scan that into their record, or they have a picture of, a prescription that they need to transcribe, or, like, the table has, like, merged cells and, like, double columns, and then it's like, well, how do you represent that as markdown? You know, you can't.
 Isaac Flath: So, yeah, so I think there's still a place for Tesseract, it's… yeah, I think if…
 Isaac Flath: If I had documents that were kind of nice and straightforward and simple and consistent, I would use Direct.
 Tommy Crumrine: If you cared more about, like, character matching, it sounds like some of those more complex models are more for… do you really want specific layout representation, or, like, structure in, like, visual structure, almost?
 Tommy Crumrine: Whereas, like.
 Isaac Flath: Yo!
 Tommy Crumrine: Sometimes we care more about, like, the characters match exactly.
 Tommy Crumrine: And… That's kinda it, you know?
 Isaac Flath: Yeah, I mean, it's, it's,
 Isaac Flath: Yeah, if the characters match exactly and that's it, then yeah, you don't need a vision model for that. You don't need one of these big models, whether it's a pipeline or not. Now, it's rarely the case where I would say it's only the characters matching. So, for example, if you have
 Isaac Flath: Like, if you have, like, a piece of paper, like, a page with, like, two columns, you probably don't want just the characters, because you don't want those columns interlaced. Like, you want reading order. You want the first column all together, and then the second column below it.
 Isaac Flath: So there's small considerations still, or like…
 Isaac Flath: I have a simple table,
 Isaac Flath: Like, I want to make sure that the 2023 row, like, the value is in the 2023 row, like, those match up, they're not misaligned. But yeah, overall, I would say the vision models are…
 Isaac Flath: I mean, there are whole advantages that they can see the entire layout of the page together. That's… that's it.
 Tommy Crumrine: Thanks.
 Isaac Flath: Yeah, I mean, I mostly talked about the vision models today, because it was,
 Isaac Flath: I was mostly going into the evals, and I didn't want to go into, like, this… this, like, chain of models, and then, like, debug down.
 Isaac Flath: a pipeline.
 Hamel Husain: Alright, well, thanks, everybody, and thanks, Isaac, for this deep dive into OCR, maybe…
 Hamel Husain: the deepest dive that I've ever seen into OCR.
 Hamel Husain: And I think a lot of people have, you know, at least if you're watching, you're like, oh my god, like, it can fail so badly at this step. So I think it's super useful, thanks so much.
 Isaac Flath: Yeah, I enjoyed this, and
 Isaac Flath: Yeah, feel free. If you have anything document-related, feel free to ping me in the Discord.
 Isaac Flath: You can tell I love documents, I don't know.
 Hamel Husain: Very important subject. Alright, thank you so much.
 Isaac Flath: Bye.

