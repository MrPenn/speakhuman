# Profile guide

A profile is a small JSON file that changes what the linter flags and tells the writing skills how you sound. Copy `profile.json` or one of the presets in `profiles/`, edit it, and save it where the linter will find it: `--profile=FILE`, the `SPEAKHUMAN_PROFILE` environment variable, `./speakhuman-profile.json` in your project (rule settings only: a project profile cannot switch on `allow_regex` or supply a `voice_file`, `voice_notes` or `cta_line` unless you pass it with `--profile`, and the summary lists every rule it switches off), `~/.config/speakhuman/profile.json`, or `profile.json` beside `speakhuman_lint.py`, in that order. Keep your own profile in `~/.config/speakhuman/` so updating the skill never overwrites it. In claude.ai, build the core zip with `python3 scripts/build_zips.py --profile=your-profile.json` so the profile ships inside it.

## Presets

- `profile.json` (default): every rule on at its normal severity; typography such as em dashes is allowed (`ascii_only` false).
- `profiles/strict.json`: every rhetorical device is flagged, a piece may keep two short closing lines, and any warning fails the run (`fail_on_warnings`). Severities stay as they are: stingers, closers, metaphors and X-not-Y remain warnings, because they are calls for a reader to make, so each one is read and then fixed or kept with a `slop-ok`. The fact check also fails on a dropped fact (`fact_check_fail_on`). Use it for published articles and site copy.
- `profiles/light.json`: typography allowed, the judgment rules are information only, six short closers allowed. Use it for casual writing where only the mechanical tells matter.

## Fields

`ascii_only` (true or false). Default false. When true, em and en dashes, curly quotes, ellipsis characters, arrows, bullets, check marks and emoji are errors. Set true if your house style bans them. Invisible characters and look-alike letters from another alphabet inside a word are errors either way.

`disable_rules` (list of rule ids). Turns rules off entirely. Run `speakhuman_lint.py --list-rules` for the ids. Common ones: `title-case-headings` if you write headings in Title Case, `passive-voice` for legal or scientific text, `exclamation-point` for consumer copy.

`enable_rules` (list of rule ids). Turns on rules that are off by default, such as `flavor-named-ui-chrome`, which flags buttons and headings named in a fiction's voice and suits a game or fiction product. `--list-rules` shows every rule; the catalogue marks the ones that are off by default.

`severity_overrides` (object). Raise or lower a rule: `{"manufactured-rule-of-three": "info"}`.

<!-- slop-ok: b2b-buzzwords -->
`extra_banned_words` (list). Added to the house avoid list. `"circle back"` matches the phrase; `"synerg*"` matches synergy, synergies and synergize.

`allowed_words` (list). Words the vocabulary rules should leave alone because they are normal in your field, such as `leverage` in finance or `ensure` in compliance writing. Each word covers its common forms (`leverage` covers `leveraged` and `leveraging`), a phrase matches as a phrase, and a trailing `*` matches any ending. It applies only to vocabulary rules, so allowing a word never silences a sentence-shape rule such as X-not-Y.

`rejected_phrases` (list). Exact phrases you have already rejected, matched case-insensitively with flexible spacing. A string that starts with `re:` is a regular expression, used only when `allow_regex` is true.

`retired_terms` (list). Metaphors and labels you have dropped. Every use is flagged. Use the inline `<!-- slop-lint retired: ... -->` comment for a term that applies to one piece only.

`disable_classes` (list). Switches off whole classes of rule: `artifact`, `evidence`, `pattern`, `density`, `house_style`. House style findings (dashes, Title Case, exclamation points, passive voice) are preferences, so a profile that does not share them can drop the class in one line.

`device_policy` (`"density"` or `"ban"`). Rhetorical devices such as X-not-Y, a metaphor asserted as a definition, a rhetorical question and a stinger are fine once. Under `density` (the default) a single use is information and `device_min` or more in one piece are warnings. Under `ban` every use is flagged. Use `ban` if your own taste rejects them outright.

`device_min` (number). How many devices in one piece count as a pattern under `density`. Default 2.

`allow_regex` (true or false). Default false. When true, entries in `rejected_phrases` that start with `re:` run as regular expressions. A pathological expression can hang the linter, so turn this on only for a profile you wrote or read, and never for a profile you received from someone else without reading it.

`fail_on_warnings` (true or false). Default false. When true, a warning fails the run (exit 1) the same way `--strict` does. It changes the exit code only; no rule changes severity.

`device_scope` (`"piece"` or `"rule"`). Default piece: every rhetorical device in a piece counts toward `device_min` together. With rule, each kind counts on its own, so one X-not-Y and one metaphor stay single uses.

`fact_check_fail_on` (`"added"`, `"added_or_dropped"` or `"anything_unchecked"`). Default added. What fails `tools/check_facts.py`: only facts the revision added, dropped facts too, or also capitalized sentence openers it could not check.

`short_closers_allowed` (number). How many paragraph-ending short lines a piece may keep before the density check speaks up. Default 3.

`cta_line` (text). Your standard call to action. The writing skills paste it verbatim instead of inventing one.

`voice_notes` (text). Two to five lines on how you write: sentence length, person, how you handle numbers, what you never say. The writing skills read this before drafting and treat it as higher priority than their defaults.

`voice_file` (path). A markdown or text file of your rulings: lines you rejected, what you said about them, and what you approved instead. The path is relative to the profile's folder and must stay inside it, so keep the file next to the profile (`~/.config/speakhuman/voice.md`). The writing skills read it in full before drafting, through `speakhuman_lint.py --voice`, and treat it as the highest-priority guidance: where a ruling conflicts with their twelve rules, the ruling wins. The linter does not lint against it; your exact rejected phrases still belong in `rejected_phrases`.

## The voice file

A model copies a before-and-after pair far more reliably than it follows a description of a voice, so most of the file should be pairs in your own words. A structure that works:

<!-- slop-lint off -->

```markdown
# Voice: Jordan Lee

## Rulings

### Clever closing lines
- Before: `The pilot saved 40 hours. Time is the one thing nobody gets back.`
- After: `The pilot saved 40 hours.`
- What I said: "Stop ending on a fortune cookie."

### Announcing the point
- Before: `Here's what surprised me: the cheapest plan churned least.`
- After: `The cheapest plan churned least.`

## Approved passages

Two or three paragraphs I wrote or signed off on. Write like these.

## My words for my things

The weekly numbers are "the tracker", never "the dashboard".
```

<!-- slop-lint on -->

Keep the rulings that still matter and cut the rest: the skills read the whole file before every draft, and the linter refuses a file over 200 KB. If you lint the voice file itself, wrap the quoted before-lines in `slop-lint off` and `on` comments.

To keep a voice file in claude.ai, build the core zip with your profile, into a folder of its own so it never replaces the shareable zips in `dist/`: `python3 scripts/build_zips.py --profile="$HOME/.config/speakhuman/profile.json" --out="$HOME/.config/speakhuman/dist"`. The script copies the voice file into the zip as `voice.md` and points the profile at it.

## Example

```json
{
  "name": "jordan",
  "ascii_only": true,
  "disable_rules": ["title-case-headings"],
  "severity_overrides": {"manufactured-rule-of-three": "info"},
  "extra_banned_words": ["circle back", "synerg*"],
  "allowed_words": ["leverage"],
  "rejected_phrases": ["at the end of the day"],
  "retired_terms": [],
  "disable_classes": [],
  "device_policy": "density",
  "device_min": 2,
  "short_closers_allowed": 3,
  "cta_line": "Reply with two times that work and I will send an invite.",
  "voice_notes": "Short sentences. Second person for instructions, first person for opinions. Every number gets a source.",
  "voice_file": "voice.md"
}
```
