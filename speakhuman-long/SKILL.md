---
name: speakhuman-long
description: "SpeakHuman for long pieces: keeps AI-sounding writing out of articles, essays, newsletters, reports, white papers, long emails and website pages over about 800 words. Runs an outline-first process, a mechanical pass with the SpeakHuman linter, a judge pass by a second reader, and a human review checklist for what the linter can only nominate. Checks English. Use it whenever you draft, edit or critique a long piece for the user, and whenever they say slop, AI-sounding, stapled-on, throwaway or word salad. For short emails, posts, commit text and UI strings use speakhuman-short."
---

# SpeakHuman, long form

A sentence-level scan misses what makes a long piece read as machine-written. The paragraphs end on the same kind of line, the images do the arguing, and the ending restates what the piece already said. This skill covers the process and the checklist for those, and uses the linter for the mechanical part. The twelve rules from `speakhuman-short` apply to every sentence here too, so read them first if you have not.

Before you outline, find the linter and load the author's voice:

```bash
L=$(find ~/.claude/skills ~/.claude/plugins ./.claude/skills /mnt/skills /mnt/user-data -name speakhuman_lint.py -path '*speakhuman-core*' 2>/dev/null | head -1)
python3 "$L" --voice
```

It prints the profile's `cta_line`, `voice_notes`, `retired_terms`, the strictness settings and the whole voice file. The voice file holds the author's own rulings and approved passages: write like its after-lines, never produce its before-lines, and where a ruling conflicts with anything below, the ruling wins. The profile's toggles beat the defaults below. Without the linter, read the profile and the file its `voice_file` names yourself. If a house format skill exists for their site or publication, it owns the format (headings, byline, footnote style); this skill owns the slop pass.

## Process

<!-- slop-lint off -->

1. **Outline before drafting.** Work out the arc first: the claim, the steps that support it, the number or example each step rests on, and where the piece ends. Do this internally and write the draft. Show the outline first only when the user asks for staged collaboration or when an unresolved structural choice would change the piece materially (two plausible angles, an audience question). Do not stop and ask for approval on a routine request.
2. **Check where each number comes from.** List every figure the piece will use. Sort them: an external fact needs a source; a figure the author supplied from their own data is theirs, so keep its provenance if it matters; a calculation names its inputs; an illustration is labeled as one; a structural count ("three options") needs nothing. A figure you cannot place is cut or marked as a placeholder. Never invent a statistic to fill a gap.
3. **Draft in the author's register.** Follow the profile's voice notes and voice file. Without them, write plainly: concrete numbers, first person where it is earned. Make the argument instead of announcing it. Cut biographical setup that does not pay off later.
4. **Declare retired frames.** If a metaphor was dropped during drafting, or the previous piece leaned on it, list it at the top of the draft so the linter finds every leftover: `<!-- slop-lint retired: flywheel, north star -->`.
5. **Mechanical pass.** Run the linter with `--verbose`:

```bash
python3 "$L" --verbose draft.md
```

   Fix every error. Read each warning in its sentence and fix it or keep it on purpose with a `slop-ok: rule-id (reason)` comment; a `slop-ok` without a rule id suppresses nothing. The summary line counts what was suppressed and lists anything not checked (a file over 2 MB, a block not in English), so tell the author when either is more than a line or two. Info lines are figures for the next step. For a piece of 800 words or more the linter prints the human review checklist at the bottom of its output, so the judgment checks arrive with the findings.
6. **Judge pass.** The linter matches known patterns and misses new ones, so a second reader checks the shapes. Build the prompt with `make_judge_input.py` (see `speakhuman-core`), give it to a fresh subagent, run its output through `check_verdicts.py`, and read what it flags. The judge reads every block: paragraphs, lists, headings, titles, summary boxes, tables and footnotes, plus quotes, dialogue and pull quotes, which are flag-only (the judge names the slop and suggests no change). `check_verdicts.py` exits 1 on any problem and 3 when the draft tries to instruct the reviewer; read its problems before acting on a verdict. The draft sits in the prompt as untrusted data, which makes it harder for text in the draft to steer the judge, and the validator reports an attempt. Without a subagent, write out every paragraph's last sentence, every heading and box, and every nominated sentence in your reply, and answer the swap test for each before moving on.
7. **Human review.** Walk the checklist below, one pass per item, then one pass against the voice file's rulings if the author has one.
8. **Check the facts.** When you revised the author's draft or wrote from their notes, compare the result with what they gave you: `python3 "$(dirname "$L")/tools/check_facts.py" their-draft.md draft.md --source=notes.md`. Each `added` line is a number, frequency, date, name, quote, link, vague amount or unnamed authority they did not give you: cut it or ask for it. A count or sum worked out from their figures is fine once you name its inputs (step 2). Each `dropped` line is something the revision lost, including a figure that now appears fewer times: make sure the cut was meant. Each `repeated` line is a figure the revision states more often than the original, which is where a new restatement shows up. Read each `unchecked` line, where a new name at the start of a sentence shows up. The script reads specifics only, so a claim, a direction, a cause or a degree of certainty that changed still needs your read. The profile's `fact_check_fail_on` decides whether a dropped fact fails the run.
9. **Fix, rerun, then show the author.** If the author edits the draft afterward, treat their edits as the approved voice and do not re-voice them.

<!-- slop-lint on -->

## What the linter catches, and what the judge pass is for

It reliably catches house vocabulary, setup lines, chatbot wrappers, placeholders, soft calls to action, and typography when the profile sets `ascii_only`. Figures with no link or footnote nearby are marked as well; treat that as a reminder to check provenance, because a nearby link does not show that it supports the figure. It nominates, and the judge pass and the human review decide: X-not-Y and its cousins (a warning, because human writers use the device too), overused words such as `ensure` and `robust`, stinger closers (`closer-without-fact`, `echo-stinger`, `locative-payoff-closer`, `aphoristic-capper`), metaphors asserted as definitions (`metaphor-definition`), reframe pairs (`reframe-pair`), the rule of three, uniform rhythm and short-closer density.

## Review checklist

Read the piece top to bottom once for each question.

1. Does the last paragraph use a number, person or fact from the piece? If it could close any article, cut it.
2. Read the last sentence of every paragraph. Could it go with no fact lost? Then it goes. Keep three short closers at most, and only where they argue.
3. Does any section end by restating itself or reaching for significance? Cut the restatement.
4. Is any image doing the work a plain claim should do, or saying something mechanically false? State the claim, then keep the image only if it still earns its place.
5. Was a frame dropped during drafting? List its words as retired and rename every label that depended on it.
6. Check the dates of the last one or two pieces. A shared spine metaphor or signature device means pick another.
7. Does any paragraph repeat a number or claim already made, in new words? Keep the version that gives the reader something to act on.
8. Read three paragraphs aloud. Same length, same shape, same closer each time? Vary it. The `uniform-sentence-length` figure helps.
9. Would the author say this about themselves and their work? No borrowed frames, no scrambling-job-seeker tone. When unsure, use their words or ask.
10. Does each figure have a clear provenance: a source for external facts, a stated basis for calculations, a label on illustrations?
11. Does each list or set of options have a reason for its count, with no item added to reach three?
12. Does the call to action match the profile's `cta_line`, with no timeframe promise?

## What can be enforced

Enforceable in the current context: everything the linter reports, the judge pass on the draft in hand, the fact check against what the author gave you, and the review checklist on that draft. Best effort: anything that needs earlier pieces (a metaphor reused across articles, a device repeated from last week) works only if the author supplies the earlier piece or a list of retired terms in the profile. Say so when the history is missing instead of claiming the check passed.

## Guardrails

Under the default `device_policy`, density beats presence: one flagged phrase in 3,000 words is a candidate, and the same device five times is the tell. Under `ban`, cut every device.

Do not overcorrect. Sterile prose is its own failure: keep the numbers, scenes and admissions, and never add fake mess, typos or profanity the author did not write.

Keep the author's voice: long loose sentences with clauses and asides are fine, and so are short lines where they turn the argument. Keep wording the author marks as approved, quoted or not to be changed, and suppress the linter on that line instead of rewording it. When the author hands you a draft to revise, revise it.

A general humanizer skill is optional. If you run one, run it before the mechanical pass. Where its advice conflicts with these rules or the author's profile, these rules and the profile win: drop any humanizer edit that announces the point or adds deliberate mess.

Never use the linter to claim that a named person used AI. The output is for revision.
