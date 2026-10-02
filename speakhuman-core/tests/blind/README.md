# Blind test for the judge pass

The linter's word and pattern rules can only catch what someone has already seen, so their score on a fixed test set says little about new writing. This folder measures the judge pass on text nobody tuned against.

1. Ask a fresh agent to write 10 labeled paragraphs on topics you have not used before, from different parts of imagined articles (openers, middles, closers), with two paragraphs written clean. Use the generator prompt below. Do not read the output until you score it.
   Add three or four paragraphs written by people before 2022 (public-domain speeches, old essays, `tests/human/`). Do not assume they are clean: people write stock phrases and stingers too. Have someone who did not write or generate any paragraph label every sentence, the human ones included, before anyone sees the judge's verdicts, and name each shape with its code from `references/shapes.md` (S1 to S12, S3b) so the scorer can check the judge's shapes as well as its sentences. The first two sets had no human paragraphs and name shapes in plain words, so the judge's false-flag rate on human writing and its shape agreement are both still unmeasured.
2. For each paragraph, run `python3 tools/make_judge_input.py para.md --position=opener` and give the resulting prompt to a separate fresh agent. Have it write its JSON array to `verdictN.json`.
3. Collect the verdicts into `[{"para_id": N, "verdicts": [...]}]` and run `python3 tools/score_judge.py labels.json verdicts.json`.

`labels-example.json` and `verdicts-example.json` are the first run (2026-10-02): 22 of 22 slop sentences caught with 0 false flags on 36 clean sentences, against 6 of 22 for the linter's rules alone. `labels-set2.json` and `verdicts-set2.json` are the second, harder run: 22 of 24 caught, with 7 flags on the 22 sentences the generator labeled clean. Read the caveats in the main README before trusting the 100 percent: the generator and the judge were the same model family, the slop was textbook, and the clean sample was small. Re-run with a new set each time, and add harder cases when the score looks too good.

## Generator prompt

<!-- slop-ok: closer-without-fact -->
Write 10 standalone paragraphs, each from a different hypothetical article on a different, unrelated topic (avoid any topic already used). Assign positions: 1 and 2 openers, 3 to 7 middle, 8 and 9 closers, 10 middle. Write the way a fluent AI model writes by default: subtle, plausible slop mixed with real specifics. Paragraphs 4 and 9 are clean. The others each contain 2 to 4 slop sentences. Output JSON: `[{"para_id": 1, "topic": "...", "position": "opener|middle|closer", "text": "...", "slop": [{"sentence": "exact text", "shape": "a code from references/shapes.md, S1 to S12 or S3b"}]}]`.
