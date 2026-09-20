---
name: class-notes
description: >
  Summarize a course lecture or office-hours transcript into a structured
  Markdown study note. Use when asked to summarize, condense, or write up a
  class transcript, recording, or office hours session.
---

# Class transcript summaries

Turn a raw transcript into a note the student can study from after missing (or attending) the
session. The student reads best from headings and bullets, not paragraphs.

## Inputs

- A transcript path, usually `homework/module-<n>/class<N>_transcript.md` or
  `class<N>_office_hours.txt`. Read the whole file before writing.
- The repository itself, for the "How this lands on my own work" section.

## Output

- `homework/module-<n>/class<N>_summary.md` for a lecture.
- `homework/module-<n>/class<N>_office_hours_summary.md` for office hours.
- Always `.md`, even when the transcript is `.txt`.

## Structure depends on the transcript type

**Lecture** — thematic headings that follow the arc of the material. Typical spine:

- What the class covered (3 to 6 bullets).
- One section per concept, in teaching order.
- Definitions, formulas, and worked numbers kept intact.
- Pitfalls the instructors called out.
- Homework preview, when they gave one.

**Office hours or any Q&A** — one section per exchange, in the order asked:

- Heading: `## <n>. <Asker> — <question in a few words>`.
- Then `**Q.**` restating the question in one or two sentences.
- Then the answer as bullets.
- Nest follow-ups as `### Follow-on: <topic>` under their parent question, rather than splitting a
  thread into separate sections.

## Rules

- **Headings and bullets.** No long paragraphs. Use a table when items share a structure
  (metrics, options, comparisons).
- **Name askers only when the transcript is legible.** Transcription garbles names, so mark unclear
  ones "Unnamed" and note at the top that names are approximate.
- **Attribute contested points.** When two instructors differ (for example one starts with a
  frontier model, the other with a cheap one), record both rather than blending them.
- **Keep the numbers.** Metric values, thresholds, split ratios, label minimums, and version-by-
  version results are the parts worth studying.
- **Quote memorable lines verbatim**, sparingly, where the phrasing carries the point.
- **Do not invent structure the session did not have**, and do not pad thin answers.

## Closing sections

End every summary with:

1. **Topics to explore** — named concepts, papers, or tools worth following up, drawn from the
   transcript rather than from general knowledge.
2. **How this lands on my own work** — connect the material to the current state of this repository:
   the student's annotations and counts, which failure modes look code-checkable versus judge
   material, what is blocking the next homework. Check the repo for the current numbers rather than
   reusing figures from an earlier summary.

## Scope

Keep it to one page of reading per hour of transcript. This is a study aid; over-structuring it
buries the content.
