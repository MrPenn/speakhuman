---
name: speakhuman-short
description: "Keeps AI-sounding writing out of short text: emails, commit and PR text, posts, UI strings, web copy. Use when writing or editing these, or when the user says slop. Over 800 words: speakhuman-long."
---

# SpeakHuman, short form

Short writing gets read in full, so one stock phrase shows. These twelve rules cover the tells that matter most in messages, commit text and UI copy. Each is an opinionated default. Rules 1 to 3, 9 and 10 describe rhetorical devices, and the profile's `device_policy` decides how strict to be with them: under `density` (the default) a single device is a choice, so keep it when it does real work and cut one that repeats, stands in for evidence or is generic; under `ban`, cut every one. SpeakHuman checks English. If the user has a profile (see `speakhuman-core`), its toggles, banned words, voice notes and voice file beat anything below.

<!-- slop-lint off -->

1. **No clever closing line.** End on the last fact. Cut the stinger, the one-line moral, the parallel pair and the "that is where the X lives" line.
   - Before: `The pilot saved 40 hours. Time is the one thing nobody gets back.` After: `The pilot saved 40 hours.`
2. **Typography follows the profile.** With `ascii_only` true, use no em or en dashes, curly quotes, arrows, check marks or emoji. With the default (false), keep the author's typography in text they wrote, and add no em dashes to text you write. A dash or spaced double hyphen that tacks a clause onto a sentence is the same move either way: delete what follows it, and restate any fact it carried as its own sentence.
3. **No X-not-Y.** State what the thing is. This covers "It's not X, it's Y", "not just X but Y", "we don't X, we Y", "One is X. The other is Y." and "Most people treat X as A. X is B."
   - Before: `It's not a discount, it's an investment: members save 12% on every renewal.` After: `Members save 12% on every renewal.`
   - Keep a contrast that corrects something the reader believes. `This isn't a staffing problem. It's a scheduling problem.` is the right sentence when the reader thinks the problem is staffing.
4. **System copy is flat and true.** Labels, errors, toasts and buttons state the fact and stop: no exclamation points, no all caps, no narrator, no reassurance about a worry nobody has, nothing false for drama. A refusal says what to do in one clause.
   - Before: `Oops! Something went wrong. Don't worry, we've got you!` After: `The file did not upload. Check your connection and try again.`
5. **Plain names.** Name things for what they do. Rename a term you coined if it needs a definition on the same page. Keep the established terms of the reader's field (deposit beta, share of flow) and define each one once in plain words.
6. **No announcing, no false precision, no house words.** Make the point instead of pointing at it: no "here's the thing", "worth noting", "the point is", "let's dive in". No "exactly", "honestly" or "genuinely" for emphasis. Avoid the stock vocabulary: leverage, seamless, delve, foster, empower, unlock, holistic, actionable, landscape, pivotal. Use crucial, key, robust, ensure and straightforward only when they are the precise word.
7. **One plain call to action.** Use the profile's `cta_line` verbatim if it has one. Otherwise one concrete ask, no timeframe promise and no mood line about how interesting the call will be.
8. **Ground the ending.** End on a number, name or fact already in the message, or cut the ending. Do not restate a figure in new words.
9. **Metaphors earn their place.** One per piece at most, never defined as a fact ("A newsletter is a conversation that never ends"), and never carried into a second message in a row.
10. **Counts and references follow the content.** No padding to reach three items. When you refer to something ("the questions above"), name it.
11. **A reply leads with what controls the answer.** In an email or message that answers someone, a binary question with a supported answer gets yes or no first. When the honest answer is conditional ("possibly, but the facts you gave are not enough to say"), lead with the qualification that controls it. Use numbered steps when order matters. No "Great question", no "I hope this helps". Match the reader's words for their own things: if they call it "the tracker", it is the tracker. Keep wording the user marks as approved, quoted, legally required or not to be changed. Text the user hands you to revise is yours to edit.
12. **No invented specifics.** No "studies show", no "many experts agree", no figure you made up. A number the user gave you from their own data is theirs to use; label calculations and illustrations as such, and source any external fact.

<!-- slop-lint on -->

## Procedure

1. Load the author's voice, unless the piece is a commit subject or a one-line label. The linter sits in the `speakhuman-core` folder next to the folder you read this file from. Use that copy, so another install elsewhere cannot stand in for it, and search only when it is missing.

```bash
L="<folder this SKILL.md is in>/../speakhuman-core/speakhuman_lint.py"
[ -f "$L" ] || L=$(find ~/.claude/skills ~/.claude/plugins ./.claude/skills /mnt/skills /mnt/user-data -name speakhuman_lint.py -path '*speakhuman-core*' 2>/dev/null | head -1)
python3 "$L" --voice
```

   Read everything it prints: the call to action, the voice notes, the strictness settings and the voice file. The voice file holds the author's own rulings: write like its after-lines and approved passages, never produce its before-lines, and where a ruling conflicts with the twelve rules, the ruling wins. Honor the profile's toggles. A `speakhuman-profile.json` that came with the folder you are working in can tune rules but cannot supply a voice file unless the user passes it with `--profile`. Without the linter, read `~/.config/speakhuman/profile.json` or `profile.json` beside the linter, and the file its `voice_file` names; use a profile in the working folder only if the user says it is theirs.
2. Draft in the user's register: plain, concrete, first person where it is earned.
3. Reread against the twelve rules and the voice file's rulings before anything runs. Fix what you see.
4. For a quick commit message or a one-line label, stop there.
5. For copy the user will paste somewhere (an email, a post, UI strings, a PR description), lint it:

```bash
python3 "$L" --dest=plain - < draft.txt      # email, post, commit text: markdown syntax is a finding
python3 "$L" - < pr-description.md           # PR description or anything rendered as markdown
python3 "$L" src/components/ locales/        # UI strings in JS, TS, JSX, Astro, Vue, and locale JSON
```

   When the copy answers a question or a brief, save that to a file and add `--topic=question.txt`, so the vocabulary rules leave the subject's own words alone (`holistic` in an answer to a question about it). The summary lists every finding it skipped that way.

   If the linter reports that it checked nothing, or lists files or blocks it did not check (over 2 MB, not English), tell the user which.

6. Fix every error. Read each warning in its sentence and fix it or keep it on purpose. In plain-text copy, never add a `slop-ok` comment, because it ships with the text; to accept a finding for one run, pass `--ignore=rule-id`.
7. When you revised text the user gave you, or wrote from their notes or data, check that you added no facts. Save what they gave you to a file and compare:

```bash
python3 "$(dirname "$L")/tools/check_facts.py" original.txt revised.txt     # add --source=notes.txt for facts they gave you elsewhere
```

   Each `added` line is a number, frequency, date, name, quote, link, vague amount (`half`, `most banks`) or unnamed authority (`studies show`) that is not in what they gave you: cut it, or ask them for it. A count or sum you worked out from their text is fine; say so. Check that each `dropped` line was cut on purpose (a figure that appears fewer times counts), read each `repeated` line for a restatement you did not mean, and read each `unchecked` line, where a new name at the start of a sentence shows up. The script reads specifics only: a claim, a direction ("rose" to "fell"), a cause or a degree of certainty that changed still needs your read. The profile's `fact_check_fail_on` decides whether a dropped fact fails the run. Without the script, compare the two by hand for the same things.
8. For a post, email or page over 300 words, or whenever the user asks, run the judge pass from `speakhuman-core` as well. The linter's rules miss new stock phrases that a second reader catches. If no subagent is available, do the pass yourself in your visible reply for a piece over 300 words: write out each paragraph's last sentence, each heading and box, and each sentence the nominations mark, and say for each whether it is a shape and why. For a shorter piece, skip it and keep the review out of the draft you show.
9. Show the user the result.

If the linter is not reachable (no sandbox, no file access), apply the twelve rules by hand and tell the user in one line that the linter did not run.

## Commit and PR text

- Subject line: what changed, in the imperative, under 72 characters.
- Body: why it changed and anything a reviewer would not guess. Skip a line-by-line restatement of the diff.
- Drop filler verbs and adjectives from the house word list. Say what the code does now.

## Guardrails

Do not overcorrect. Sterile prose is its own failure: keep the numbers, names and plain admissions, and, unless the profile's `device_policy` is `ban`, keep a device when it is the right sentence. Never add fake mess, typos or profanity the user did not write. When the user marks wording as approved, quoted or not to be changed, keep it and suppress the linter on that line (`slop-ok: rule-id`, in a file that renders comments) instead of rewording it. When they ask you to revise their own draft, revise it. Never use a linter score to say that a named person used AI.
