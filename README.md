# SpeakHuman

Three skills that keep AI-sounding writing out of what Claude writes for you.

- `speakhuman-short`: emails, commit and PR text, posts, UI strings. Twelve rules and a short procedure.
- `speakhuman-long`: articles, essays, reports, long emails. Outline first, a linter pass, a judge pass, a review checklist, then a fact check.
- `speakhuman-core`: the linter (`speakhuman_lint.py`), 131 rules, the judge-pass and fact-check tools, your profile, and the tests. The other two load it.

## Install

Claude Code: copy the three `speakhuman-*` folders into `~/.claude/skills/`.

Claude chat or Cowork: download the zips from the [Releases page](https://github.com/MrPenn/speakhuman/releases) and upload `speakhuman-short.zip`, `speakhuman-long.zip` and `speakhuman-core.zip` under Settings, Capabilities, Skills. If you only have this folder, build them first:

```bash
python3 scripts/build_zips.py
```

That writes the three skill zips to `dist/`, plus `dist/speakhuman.zip` with the whole bundle for sharing.

## Set up your profile

Ask Claude "set up my SpeakHuman profile" and answer the questions, or copy `speakhuman-core/profile.json` and edit it. The fields are explained in `speakhuman-core/references/profile-guide.md`. The fields to look at first: `ascii_only` (true to flag em dashes and curly quotes; the default allows them), `extra_banned_words`, `allowed_words`, `cta_line` and `voice_notes`.

Keep your profile outside the skill folders so an update never overwrites it:

- Claude Code: `~/.config/speakhuman/profile.json`, or `speakhuman-profile.json` in a project for that project only. A project profile tunes rules, and the summary lists every rule it switches off. It cannot switch on regular expressions or supply a voice file, voice notes or a call to action unless you pass it with `--profile`.
- claude.ai and Cowork: build the core zip with your profile (and its voice file) inside it, and upload that zip: `python3 scripts/build_zips.py --profile=path/to/profile.json --out=personal-dist`. Use `--out` so the personal core zip does not replace the shareable one in `dist/`. The bundle zip always carries the default profile, and the build stops if `speakhuman-core/profile.json` itself holds personal settings, so yours is never shared by accident.

The most useful part of a profile is the voice file (`voice_file`): a markdown file of lines you rejected, what you said about them, and what you wanted instead, plus a passage or two you like. Claude reads it before every draft and follows it over the default rules. `speakhuman-core/references/profile-guide.md` shows a layout. When you reject a phrase, tell Claude to add it to `rejected_phrases`; when you reject a move or say what you wanted instead, tell Claude to add a ruling to your voice file.

## Claude's own replies

A skill loads when a task matches it, so it cannot reliably shape every chat reply. For that, paste these lines into `CLAUDE.md` (Claude Code) or your personal preferences (claude.ai) and edit them to taste:

```markdown
## How to reply
- Lead with the answer, or with the qualification that controls it. If the question is yes or no and the answer is supported, the first word is yes or no.
- Keep it short. Explain the reasoning only when I need it to act.
- No recap of work I can see. One or two sentences on the outcome.
- No "Great question", no "I hope this helps", no closing offer and no "let me know if".
- Use my words for my own things.
- No em dashes, no "It's not X, it's Y", no "here's the thing", no clever closing line.
```

## Check it works

```bash
python3 speakhuman-core/tests/run_tests.py
```

Expected: 0 failures, then the error and warning rates on the human corpus, overall and for each genre. `--quick` skips the command-line runs, the corpus and the timing checks and finishes in about a second. GitHub runs the full suite on Python 3.9 and 3.13 for every push.

## What to expect

The linter's errors cover the mechanical tells: the house avoid list (`leverage`, `seamless`, `delve` and the rest), setup lines, chatbot wrappers, emphasis words, placeholders, and typography when the profile sets `ascii_only`. X-not-Y and overused words such as `ensure`, `robust` and `crucial` are warnings, because people use them too. Under an earlier version of the rules, five Paul Graham essays (about 24,000 words, 2001 to 2023) produced 86 errors before the error tier was narrowed and 48 after, 19 of them em dashes; of 300 Homebrew commit messages from 2018 to 2021, 44 failed before and 11 after, and with house style off only 1 did. Those runs predate the October 2026 changes, and the essays and commits are not in the repository.

`speakhuman-core/tests/human/` holds human writing from before chat models in seven genres, including three kinds of email, and the test suite fails if the error or warning rate climbs, overall or in any genre; its README has the current rates for each genre. Human blog posts run highest, mostly on house words such as `empowered` and `exactly`. Business email from 2000 and 2001 is full of `Let me know if you have any questions`, so that line and its cousins are the house-style rule `stock-email-courtesy`: a warning you can switch off with the house_style class.

The rules are weak on semantic slop: stock metaphors, clever closers, portable truisms. On freshly written slop they caught about a quarter to a half.

The judge pass is built for that gap. A fresh subagent reads each sentence against twelve shapes and applies a swap test (could this sentence move unchanged into an article on another subject?). It reads every block, headings and summary boxes included, and in quotes, dialogue and pull quotes it names the slop without suggesting a change. On one blind set of 10 new paragraphs on 10 new topics, from openers, middles and closers, it caught 22 of 22 slop sentences with no false flags on 36 clean ones. The rules alone caught 6 of 22.

Read that 100 percent with care. The paragraphs were written by the same model family that judged them, the slop was textbook, and the clean sample was small.

A second, harder set (12 paragraphs, 24 labeled slop sentences, written by a smaller model and told to include unnecessary inference, causal glue, stock adages and "exploit" stingers that hide behind a number) gave 22 of 24 caught. Both misses were exploit cases, a closing sentence that cites a real figure but adds no information: a concrete fact makes the judge less sure. The judge also flagged 7 of 22 sentences the generator had labeled clean. On review all seven read as acceptable sentences, so count them as false flags until someone outside the tool labels the set. Neither set included human-written prose, so the judge's false-flag rate on human writing is still unmeasured; expect some over-flagging of writing full of its own figures of speech.

The judge only nominates sentences for you to decide on. `speakhuman-core/tests/blind/README.md` explains how to re-run its test with a new set of 10 generated paragraphs and three or four written by people, which is how its false-flag rate on human writing gets measured.

## License

MIT, in `LICENSE`. The human writing in `speakhuman-core/tests/human/` keeps its sources' terms: U.S. government works in the public domain, CC0 dedications, and a 1918 book in the public domain. That folder's README lists each source.
