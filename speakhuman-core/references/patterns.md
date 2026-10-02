# Slop pattern catalogue

Every pattern the SpeakHuman skills know, grouped by category. Generated from `slop_rules.json` by `tools/build_patterns.py`; do not edit by hand.

How to read an entry: the severity is what the linter reports: `error` for mechanical rules, `warn` for candidates a person has to judge, and `info` for density and rhythm figures. The kind is how the linter looks for it: `pattern` (regexes), `density` (regex hits per 1,000 words), `engine:<check>` (a coded check in speakhuman_lint.py), or `manual`, which has no code at all and exists for the human review checklist.

Class says what kind of problem a hit is: `artifact` (model or editor residue), `evidence` (unsupported claims), `pattern` (common machine-writing moves), `density` (fine once, suspicious repeatedly) or `house_style` (a preference, not a defect). Switch classes off with `disable_classes` in the profile.

Each entry's body sits inside its own slop-lint off and on markers, because it quotes banned words on purpose. Typographic characters are described by code point so this file stays ASCII.

Totals: 131 rules by severity: error 11, warn 89, info 31. 13 are kind `manual` (no code).

## Contents

- [Punctuation](#punctuation) (5)
- [Vocabulary](#vocabulary) (15)
- [Editing residue](#editing-residue) (6)
- [Rhetorical devices](#rhetorical-devices) (8)
- [Framing](#framing) (4)
- [Endings and openings](#endings-and-openings) (10)
- [Tone](#tone) (10)
- [Sentence structure](#sentence-structure) (10)
- [Ui copy](#ui-copy) (8)
- [Metaphor](#metaphor) (7)
- [Chat replies](#chat-replies) (2)
- [Structure](#structure) (10)
- [Claims and evidence](#claims-and-evidence) (17)
- [Headlines and headings](#headlines-and-headings) (3)
- [Rhythm](#rhythm) (4)
- [Voice](#voice) (4)
- [Formatting](#formatting) (6)
- [Visual design](#visual-design) (1)
- [Guardrails](#guardrails) (1)

## Punctuation

### `non-ascii-typography`

<!-- slop-lint off -->

**Non-ASCII typography.** Class `house_style`, severity `error`, kind `pattern`.

Non-ASCII typography: em or en dash, curly quote, ellipsis character, arrow, bullet, check mark, emoji or invisible space. These read as machine-written and often break in plain-text destinations.

Bad:

- `The problem (U+2014 em dash) and this matters (U+2014) is systemic.`
- `Curly quotes (U+201C, U+201D) around a phrase`
- `Input (U+2192 arrow) Processing (U+2192) Output`
- `&mdash; or &#8212; written as an entity`

Good:

- `The problem is systemic.`
- `Input, then processing, then output.`

Fix: Retype in plain ASCII. Replace a dash with a period, comma, colon or parentheses, and rewrite the sentence if it leaned on the dash. Straight quotes, three periods, and the word 'to' in place of an arrow.

False positives: Letters with diacritics (a cited surname such as Parra Escartin with its accent), math signs (multiplication, division, plus-minus, degree) and currency signs are not matched here, and any other non-ASCII character is reported by non-ascii-other as a warning. HTML entities for names and math (&iacute;, &times;) are ignored. For quoted foreign text, add <!-- slop-ok: non-ascii-typography --> on the line.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; anti-slop verification pass, 2026-09-24 (precision and recall findings)

<!-- slop-lint on -->

### `non-ascii-other`

<!-- slop-lint off -->

**Other non-ASCII characters.** Class `house_style`, severity `warn`, kind `pattern`.

Non-ASCII character outside the typography list: a symbol such as the copyright, trademark or section sign, or text in another script. Fine in some destinations; check it is intended.

Bad:

- `(c) typed as U+00A9 in a footer`
- `TM typed as U+2122 after a product name`

Good:

- `(c) 2026 Jordan Lee`
- `Parra Escart&iacute;n and Arcedillo`
- `5 &times; 60 words`

Fix: Use the ASCII form ((c), TM, Sec.) or, on the site, the HTML entity (&copy;, &trade;, &sect;).

False positives: Letters with diacritics, math signs (multiplication, division, plus-minus, degree, micro, superscripts, fractions) and currency signs (cent, pound, yen, euro) are not matched. A quotation in another script is legitimate; suppress the line.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

<!-- slop-lint on -->

### `hidden-characters`

<!-- slop-lint off -->

**Invisible characters or look-alike letters inside a word.** Class `artifact`, severity `error`, kind `pattern`.

A word holds an invisible character, or a letter from another alphabet that looks like a Latin one. It hides the word from search, spell check and this linter, whatever the profile allows.

Bad:

- `We delv\u0435 into the data.`
- `We del\u200bve into the data.`

Good:

- `We look at the data.`
- `\u0414\u0430 means yes.`

Fix: Retype the word in plain letters.

False positives: A name that really mixes alphabets can be suppressed on its line. A whole word in Greek or Cyrillic is not flagged.

Sources: SpeakHuman red team, 2026-10-02 (homoglyph and zero-width bypass under the light profile)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `dash-clause`

<!-- slop-lint off -->

**Dash-appended clause.** Class `house_style`, severity `warn`, kind `pattern`.

Clause appended after a dash. Content after a dash is almost always a throwaway line. An ASCII ' -- ' is the same move in different clothes.

Bad:

- `Signing up is your agreement -- there is no other.`
- `Upload failed: check the file first -- it may be too large for the form.`

Good:

- `Check the file size and upload it again.`

Fix: Delete what follows the dash and reread. If the sentence lost a fact, restate that fact as its own plain sentence, or use a comma, colon or parentheses.

False positives: A dash inside code, a CLI flag or a date range is masked or not matched. Quoted source text is fine; wrap it in a slop-lint off region.

Evidence: measured: 39 finding(s) (0 error, 39 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `colon-reveal`

<!-- slop-lint off -->

**Colon reveal.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Colon reveal: 'The best part: it learns.'

Bad:

- `The detail that makes it work: a separate agent grades it.`
- `The best part: it learns.`

Good:

- `The recipe has one rule: weigh the flour.`

Fix: Write the plain sentence: 'It also learns, which is the best part', or just 'It learns from each review.'

False positives: Colons for lists, labels and quotations are not matched: the reveal noun must follow an article, so a bare note label ('Lesson: ...', 'Result: ...') passes.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Vocabulary

### `house-banned-vocabulary`

<!-- slop-lint off -->

**House-banned vocabulary.** Class `pattern`, severity `error`, kind `pattern`.

Word on the house avoid list (stock AI vocabulary). Replace it with the plain word or cut the clause. Add words with extra_banned_words in your profile.

Bad:

- `The tool serves as a catalyst for fostering alignment and streamlining workflows.`
- `A seamless onboarding flow.`
- `Unlock the full potential of your customer base.`

Good:

- `The tool gets the regions to agree on one version.`
- `Onboarding takes four screens.`
- `The bank is highly leveraged after the acquisition.`
- `The landscape slopes toward the river.`

Fix: Use the plain word or say the specific thing: leverage -> use; seamless -> cut it; delve -> look at; foster -> build; empower -> let; pivotal -> say why it matters; landscape -> market or field; unlock -> open or allow; holistic -> whole, or list the parts; actionable -> say what to do.

False positives: Four of these words have a literal meaning, so they match only in their stock sense: leverage as a verb with an object (leverage our data), foster with an abstract object (foster a culture of trust), landscape after a market or industry word or as something to navigate (the competitive landscape), and unlock with an abstract object (unlock the full potential). Leverage on a balance sheet, foster care, a landscape that slopes toward a river and unlocking a card or a door are not flagged. A regulation quoted verbatim keeps its own wording; suppress that line.

Sources: no-ai-slop (Peter Yang); Kobak et al. 2024, excess vocabulary in academic writing (arXiv:2406.07016); taste-skill (copy self-audit, section 9)

Evidence: measured: 6 finding(s) (6 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 6 of 6 must_flag cases that name it

<!-- slop-lint on -->

### `overused-vocabulary`

<!-- slop-lint off -->

**Overused vocabulary.** Class `pattern`, severity `warn`, kind `pattern`.

Word that machine writing overuses. It is normal in technical writing, so read the sentence: keep it when it is the precise word, replace it when it is filler.

Bad:

- `The key takeaway is that data matters.`
- `It is crucial to build a robust process.`

Good:

- `Make sure the backup runs every night.`

Fix: robust -> reliable, or name the test it passed; straightforward -> simple, or cut; crucial, vital, key -> say why it matters; ensure -> make sure, or say who checks.

False positives: Common in commit messages, specs and compliance text ('Ensure the cache is cleared before deploy'), which is why this is a warning and the rest of the house list is an error. Exempt: robust standard errors, vital records, vital signs. Set allowed_words in your profile to stop the warning for a word you use on purpose.

Sources: no-ai-slop (Peter Yang); Kobak et al. 2024, excess vocabulary in academic writing (arXiv:2406.07016); SpeakHuman red-team pass, 2026-10-02 (false positives on human essays and commit messages)

Evidence: measured: 31 finding(s) (0 error, 31 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `banned-intensifiers`

<!-- slop-lint off -->

**Banned intensifiers: genuinely, honestly, exactly, the whole X.** Class `pattern`, severity `error`, kind `pattern`.

Intensifier that adds sincerity or precision the sentence has not earned: 'genuinely' and 'honestly' claim candor, 'exactly' implies false precision, 'that is the whole point' implies false totality.

Bad:

- `it is exactly the problem`
- `useful to exactly the extent`
- `That is the whole story.`
- `that is the whole difference`
- `This genuinely changes everything about how teams work.`

Good:

- `It costs exactly $40 a month.`
- `That gap is what the new form closes.`

Fix: Delete the intensifier and reread. Keep 'exactly' only on a literal quantity (exactly $250, exactly three).

False positives: 'Exactly' before a number or quantity is fine and is exempted. 'Must match exactly' in UI copy is exempted, and so is a bare question such as 'What exactly?' or 'How exactly does it work?' (an FAQ heading).

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 5 finding(s) (5 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `glossary-needing-jargon`

<!-- slop-lint off -->

**Jargon that needs its own glossary.** Class `pattern`, severity `warn`, kind `pattern`.

A coined term that the page then has to define. If the term needs a glossary, the term is the problem.

Bad:

- `Momentum is our engagement score from 0 to 100.`

Good:

- `Logins in the last 30 days.`

Fix: Rename the term to the plain word ('Pulse' -> 'Activity', 'Closed gate' -> 'Private'). Keep shorthand in code and logs.

False positives: Established domain terms the audience owns (master data, type 2, MLR) are fine, as is a coined term the piece argues for on purpose.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `ai-lexicon-cluster`

<!-- slop-lint off -->

**AI lexicon cluster.** Class `pattern`, severity `warn`, kind `pattern`.

Word from the measured AI-overuse cluster (the delve family).

Bad:

- `Somali cuisine is an intricate and diverse fusion, drawing from the rich tapestry of flavours.`
- `An enduring testament to the influence of colonial rule, showcasing how these dishes integrated.`

Good:

- `Somali cooking mixes Arab, Indian and Italian dishes.`

Fix: Swap for the plain word: showcase -> show; underscore -> show; utilize -> use; facilitate -> help; bolster -> support; myriad -> many, or the count; testament -> evidence, or cut.

False positives: Proper nouns are skipped (Pivotal Software, Cornerstone Church). One use is weak evidence; three in a paragraph is a pattern.

Sources: Kobak et al. 2024, excess vocabulary in academic writing (arXiv:2406.07016); Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; no-ai-slop (Peter Yang); anti-ai-slop-writing (jalaalrd)

Evidence: measured: 24 finding(s) (0 error, 24 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `filler-phrases`

<!-- slop-lint off -->

**Filler phrases and padding connectors.** Class `pattern`, severity `warn`, kind `pattern`.

Filler phrase: padding that can be cut or shortened with no loss.

Bad:

- `When it comes to productivity, AI tools can help.`
- `At the end of the day, customer trust matters.`

Good:

- `AI tools cut the drafting time; review still takes three weeks.`

Fix: Delete it, or use the short form: in order to -> to; due to the fact that -> because; in terms of -> say what you mean.

False positives: Low. 'In order to' can separate purpose from a simpler 'to' in legal text.

Sources: no-ai-slop (Peter Yang); humanizer skill; elithrar anti-slop tells

Evidence: measured: 10 finding(s) (0 error, 10 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `b2b-buzzwords`

<!-- slop-lint off -->

**B2B and startup buzzwords.** Class `pattern`, severity `warn`, kind `pattern`.

B2B or startup buzzword.

Bad:

- `A frictionless, AI-powered, customer-centric platform.`

Good:

- `Opens an account in four screens.`

Fix: Say what the product does and what it costs or saves.

False positives: Quoting a vendor to critique it.

Sources: taste-skill (copy self-audit, section 9)

Evidence: measured: 6 finding(s) (0 error, 6 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `corporate-jargon`

<!-- slop-lint off -->

**Corporate jargon and inflated verbs.** Class `pattern`, severity `warn`, kind `pattern`.

Corporate jargon.

Bad:

- `Let's circle back and do a deep dive on the pain points.`

Good:

- `Let's meet Thursday and go through the three complaints.`

Fix: Plain verb and object: 'talk again Thursday', 'the easy fixes', 'raise renewals 4%'.

False positives: Ring-fence is a real regulatory term in UK banking; suppress when it is literal.

Sources: no-ai-slop (Peter Yang); George Orwell, Politics and the English Language (1946)

Evidence: measured: 3 finding(s) (0 error, 3 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `ai-default-names`

<!-- slop-lint off -->

**AI-default names and placeholders.** Class `pattern`, severity `warn`, kind `pattern`.

Name a model reaches for by default (Sarah Chen, Acme, Elara).

Bad:

- `Sarah Chen, a marketing director at Acme Corp, spent two weeks...`

Good:

- `A new marketing executive came in and found out...`

Fix: Use a real, cited example, or a specific invented one labeled as hypothetical.

False positives: Real people with these names; legal templates that use John Doe.

Sources: taste-skill (copy self-audit, section 9); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `fiction-sensory-cliches`

<!-- slop-lint off -->

**Fiction sensory cliches.** Class `pattern`, severity `warn`, kind `pattern`.

Stock fiction beat.

Bad:

- `She let out a breath she didn't know she was holding.`

Fix: Write what this character did, specifically.

False positives: Rare outside fiction.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `empty-intensifier-adverbs`

<!-- slop-lint off -->

**Empty intensifier and hedge adverbs.** Class `density`, severity `info`, kind `density`.

Intensifier and hedge adverbs above the house density.

Bad:

- `The findings are truly significant and fundamentally important.`

Good:

- `The findings moved the budget.`

Fix: Delete each one and reread; keep it only when the sentence is less true without it.

False positives: One 'actually' in a story is voice. Density is what reads as machine-written.

Sources: no-ai-slop (Peter Yang); elithrar anti-slop tells; humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `formal-connector-density`

<!-- slop-lint off -->

**Formal connector density.** Class `density`, severity `info`, kind `density`.

Formal connectors and upgrade verbs above the house density.

Bad:

- `Additionally, the tool enhances alignment. Moreover, it offers a comprehensive view.`

Fix: Cut 'additionally' and 'moreover'; the next sentence already follows. Replace enhance with the specific change.

False positives: These words have a real baseline rate in formal writing; only density is reported.

Sources: Kobak et al. 2024, excess vocabulary in academic writing (arXiv:2406.07016); anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `invented-concept-labels`

<!-- slop-lint off -->

**Invented concept labels.** Class `density`, severity `info`, kind `density`.

Coined 'the X paradox/trap' labels.

Bad:

- `the supervision paradox`
- `the acceleration trap`

Good:

- `shadow IT`

Fix: Keep a coined term only if the piece argues for it with a mechanism and a number (the longform skill wants one per piece at most).

False positives: Coining one good term is house style ('dark content', 'the 4.8-star trap').

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `legalese`

<!-- slop-lint off -->

**Legalese in non-legal copy.** Class `density`, severity `info`, kind `density`.

Legal register words in ordinary copy.

Bad:

- `The aforementioned policy is hereby updated.`

Good:

- `This policy changes on March 1.`

Fix: Plain words: 'this', 'from now on', 'despite'.

False positives: Quoted regulation text keeps its words.

Sources: no-ai-slop (Peter Yang)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `synonym-cycling`

<!-- slop-lint off -->

**Synonym cycling.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

The same thing called three different names in three sentences.

Bad:

- `The agent reviews the draft. The assistant scores the piece. The tool suggests fixes.`

Good:

- `The agent reviews the draft, scores it, and suggests fixes.`

Fix: Repeat the clear word, or use a pronoun. Keep a term list (invoice, order, refund) and hold to it.

False positives: Deliberate variation to avoid five repeats in one paragraph.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

<!-- slop-lint on -->

## Editing residue

### `chatbot-residue`

<!-- slop-lint off -->

**Chatbot residue and sycophancy.** Class `artifact`, severity `error`, kind `pattern`.

Chat-interface residue: a wrapper phrase from a chatbot turn left in the text.

Bad:

- `Great question! Here is an essay on this topic.`
- `Certainly! Here is a revised version of your email.`
- `You're absolutely right that this is a complex topic.`

Good:

- `The fee applies to accounts under $1,500.`

Fix: Delete it and start with the content. In a reply, lead with the answer.

False positives: Near zero. Quoting a chatbot on purpose is the only exception; suppress that line. Courtesy lines people also write in email (let me know if, hope this helps, happy to help) are the house-style rule stock-email-courtesy.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; no-ai-slop (Peter Yang); elithrar anti-slop tells

Evidence: measured: 2 finding(s) (2 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `stock-email-courtesy`

<!-- slop-lint off -->

**Stock email courtesy lines.** Class `house_style`, severity `warn`, kind `pattern`.

Stock courtesy line: an offer to help, a hope that this helps, a 'let me know if'. People wrote these in email long before chatbots, and chatbots now use them so often that readers skim past them. This is a house-style preference; switch off the house_style class to allow them.

Bad:

- `Let me know if you have any questions.`
- `I hope this helps.`
- `Please do not hesitate to call me.`

Good:

- `Call me before Friday if the numbers change.`

Fix: Cut it, or replace it with the one thing you want the reader to do next.

False positives: A specific request is fine: 'Call me before Friday if the numbers change.' Human business email from 2000 and 2001 uses these lines often, which is why this is house style and not chatbot residue.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; no-ai-slop (Peter Yang); elithrar anti-slop tells; SpeakHuman human corpus, 2026-10-02 (Enron business email: six of eight errors were these lines)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `citation-markup-artifacts`

<!-- slop-lint off -->

**Chat-tool citation and markup artifacts.** Class `artifact`, severity `error`, kind `pattern`.

Leftover citation token or markup from a chat tool.

Bad:

- `The rate rose in 2024 :contentReference[oaicite:3]{index=3}.`
- `citeturn0search2`

Good:

- `The rate rose in 2024.[^4]`

Fix: Delete the token. If it stood for a real source, replace it with a footnote to that source.

False positives: Near zero.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `directive-hygiene`

<!-- slop-lint off -->

**Linter directives that hide or leak.** Class `artifact`, severity `warn`, kind `engine:directives`.

A linter directive is hiding more than it should, or will ship with the text.

Bad:

- `We use it. <!-- slop-ok -->`
- `<!-- slop-lint off --> (with no slop-lint on after it)`

Good:

- `We use it. <!-- slop-ok: house-banned-vocabulary (quoting the vendor) -->`

Fix: Name the rule in every slop-ok (slop-ok: rule-id (reason)), close every slop-lint off with slop-lint on, and keep directives out of plain-text copy; pass --ignore=rule-id for a one-off instead.

False positives: None expected. A slop-ok that names a rule from an older rule set is reported so it can be renamed.

Sources: SpeakHuman red-team pass, 2026-10-02 (silent suppression)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `placeholder-text`

<!-- slop-lint off -->

**Unfilled placeholder text.** Class `artifact`, severity `error`, kind `pattern`.

Unfilled placeholder left in the text.

Bad:

- `Best regards, [Your Name]`
- `Official channel: (Add your channel URL here)`

Good:

- `Best, Jordan`

Fix: Fill in the real value, or delete the line if the value does not exist.

False positives: Template files that are meant to hold placeholders; run the linter on the rendered output instead.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `reasoning-residue`

<!-- slop-lint off -->

**Reasoning residue.** Class `artifact`, severity `warn`, kind `pattern`.

Visible reasoning scaffold left in the text.

Bad:

- `While some might argue the fee is fair, the data says otherwise.`

Good:

- `The fee costs the median customer $96 a year.`

Fix: Delete the scaffold and state the conclusion.

False positives: Numbered steps in instructions are fine; they are not matched.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Rhetorical devices

### `x-not-y-strict`

<!-- slop-lint off -->

**Strict X-not-Y forms.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

The X-not-Y construction: a claim built on a negated foil ('It's not X, it's Y'; 'not just X, but Y'). State what the thing is and stop.

Bad:

- `It's not bold. It's backwards.`
- `Feeding isn't nutrition. It's dialysis.`
- `The question isn't the model. It's the eval.`
- `Half the bugs you chase aren't in your code. They're in your head.`
- `The eval isn't a detail. It's the whole game.`
- `The future isn't coming. It's already here.`
- `The tool not only saves time but also improves accuracy.`
- `Not because the technology is complex. Because people are complex.`
- `This is more than a rebrand. It's a new chapter.`

Good:

- `The eval matters more than the model.`
- `The tool saves time and improves accuracy.`

Fix: State Y and stop. 'The question isn't the model. It's the eval.' becomes 'The eval matters more than the model.' Keep a contrast only when it corrects a belief the reader actually holds, and then write it as a plain statement of what is true.

False positives: Human writers use this device too ('not because X, but because Y'), so it is a warning, and under the default density policy a single use is information. Keep a contrast that corrects a belief the reader actually holds. The engine also fires on 'The office is not in Texas. It is in Delaware.', which is the same device.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); no-ai-slop (Peter Yang); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 11 finding(s) (0 error, 11 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 10 of 10 must_flag cases that name it

<!-- slop-lint on -->

### `negative-listing`

<!-- slop-lint off -->

**Negative listing (Not X. Not Y. Just Z.).** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Negative listing: a countdown of what something is not before the reveal. The X-not-Y family.

Bad:

- `Not a bug. Not a feature. A fundamental design flaw.`
- `Not ten. Not fifty. Five hundred and twenty-three lint violations across 67 files.`

Good:

- `It is a design flaw in how the scheduler assigns shifts.`

Fix: State the thing itself: 'Five hundred and twenty-three lint violations across 67 files.'

False positives: Low. A real list of excluded options in instructions ('No cash. No checks.') can stay; suppress it.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `x-not-y-contrast`

<!-- slop-lint off -->

**X, not Y contrast (candidate forms).** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Contrast built on a negated foil: 'A is X, not a Y', or 'One is X. The other is Y.'

Bad:

- `the dashboard is your COMMAND CENTER, not a report`
- `DECORATIVE badge, NOT a security feature`
- `One is a tool you buy once. The other is a subscription.`

Good:

- `A workspace groups the people who share a project.`
- `The bank is chartered in Texas, not Delaware.`
- `The vendor is a software company, not a licensed lender.`
- `These were self-reported survey answers, not an audit of individual records.`
- `For contracts, keep what each customer signed, not only the template.`
- `The charity is registered in Ontario, not Quebec.`

Fix: Say what the thing is. Keep the contrast only when the reader would otherwise believe Y.

False positives: Exempted: a legal-status disclosure ('Chime is a financial technology company, not a chartered bank'); a caveat on how a figure was produced ('institution-reported estimates, not an audit'); a how-to step that opens on its verb ('Keep every version that went live, with the dates, not only the current one'); and 'One is X; the other is Y' right after the text says the two sound alike or are confused. 'Chartered in Texas, not Delaware' (no article) is not flagged.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `negative-inventory`

<!-- slop-lint off -->

**Negative inventory (it does not X, and it does not Y).** Class `pattern`, severity `warn`, kind `pattern`.

Negative inventory: a list of what something does not do, standing in for what is true. Part of the X-not-Y family.

Bad:

- `It does not set prices, and it does not tell you which suppliers to drop.`

Good:

- `Choosing suppliers is a separate job, done by the buyer.`

Fix: Say what the thing does, or name who does the missing job: 'The tool sets prices. Choosing suppliers is a separate job, done by the buyer.'

False positives: Privacy and legal copy that lists what a system does not collect ('It does not set cookies, and it does not store your IP') is a factual disclosure; suppress it with slop-ok.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `rhetorical-question-setups`

<!-- slop-lint off -->

**Self-answered rhetorical setups.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Rhetorical setup: a question the writer answers at once ('The catch? It only works if...').

Bad:

- `The catch? It only works if you already have the data.`
- `Why does this matter? Because the deadline moved.`

Good:

- `It only works if you already have the data.`

Fix: Make the point directly.

False positives: A real reader question used as a section heading is fine. The old catch-all (any short question plus short answer) was removed because it fired on 'Ready? Let's go.'

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 3 finding(s) (0 error, 3 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 6 of 6 must_flag cases that name it

<!-- slop-lint on -->

### `thought-leader-formulas`

<!-- slop-lint off -->

**Thought-leader formulas.** Class `pattern`, severity `warn`, kind `pattern`.

LinkedIn thought-leader template ('Most people X. The few Y.', 'X is the new Y').

Bad:

- `Most people use AI to move faster. The few who win use it to think deeper.`
- `Stop grinding. Start systemizing.`
- `Data is the new oil.`
- `Most teams chase new tools to win speed. The few who win fix the handoffs first.`
- `Most developers ship features. The few who last write tests first.`
- `Good teachers never stop learning.`

Good:

- `Teams that wrote tests first shipped fixes in two days.`
- `Most days the clinic sees 40 patients. The busiest day this year saw 61.`
- `The Great Lakes always freeze by February.`

Fix: Replace the frame with the specific claim and the evidence behind it.

False positives: Rare in plain prose. The group can be anyone (founders, parents, nurses); time words ('most days', 'most of') and fixed names ('the Great Lakes') are excluded.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 6 of 6 must_flag cases that name it

<!-- slop-lint on -->

### `false-ranges`

<!-- slop-lint off -->

**False ranges.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

False range: 'from X to Y' pairs with no real scale between them.

Bad:

- `From innovation to implementation to cultural transformation.`
- `from the singularity of the Big Bang to the cosmic web, from the birth of stars to dark matter`

Good:

- `The book covers the Big Bang, star formation and dark matter.`

Fix: List the actual items.

False positives: A real span ('one to two months from request to use') is fine and is not matched.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `reframe-pair`

<!-- slop-lint off -->

**Reframe pair (they treat X as A. X is B.).** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Two-sentence reframe: how people see something, then what it really is. It is the X-not-Y device with the negation implied.

Bad:

- `Teams treat the newsletter as a chore. A newsletter is a conversation that never ends.`
- `Most teams see the audit as a cost. The audit is an insurance policy.`

Good:

- `Newsletter signups rose from 800 to 1,100 a month once someone owned it.`

Fix: Drop the foil sentence and state what the thing is, with the evidence for it.

False positives: A real misconception that the piece goes on to correct with data can stay once per piece. The rule needs the same noun in both sentences.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

## Framing

### `announcing-setup-lines`

<!-- slop-lint off -->

**Setup lines that announce the point.** Class `pattern`, severity `error`, kind `pattern`.

Setup line: the sentence announces that a point is coming instead of making it.

Bad:

- `The vendor's view of that is worth saying, because it is common.`
- `The point is that the contract expired in May.`
- `Here's the thing: most bioinformatics pipelines break in production.`
- `It's worth noting that this approach has several advantages.`

Good:

- `The contract expired in May, and nobody renewed it.`

Fix: Cut the announcement and open with the claim itself.

False positives: A topic sentence that previews a specific, named claim is normal structure. 'Keep in mind' inside a quoted rule stays; suppress it.

Sources: stop-slop (Hardik Pandya); elithrar anti-slop tells; no-ai-slop (Peter Yang)

Evidence: measured: 1 finding(s) (1 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 7 of 7 must_flag cases that name it

<!-- slop-lint on -->

### `interpretive-metadiscourse`

<!-- slop-lint off -->

**Interpretive metadiscourse and importance-flagging.** Class `pattern`, severity `warn`, kind `pattern`.

Metadiscourse: the sentence tells the reader how to feel about the point ('this matters', 'make no mistake').

Bad:

- `As you can see, the numbers are clear.`
- `Make no mistake, this matters.`
- `Because people are complex. Let that sink in.`
- `It fails. Period. Nobody noticed.`

Good:

- `34% needed one to two months, up from 5% a year earlier.`

Fix: Delete the flag and let the fact carry the weight. If it does not, add the number or consequence that makes it matter.

False positives: 'It turns out' inside a story can be natural speech; read it aloud.

Sources: stop-slop (Hardik Pandya); elithrar anti-slop tells; anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `faux-insight-nobody-framing`

<!-- slop-lint off -->

**Faux-insight and 'nobody' framing.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Faux insight: the sentence claims a secret ('the part everyone misses', 'a report nobody reads').

Bad:

- `Hours lost to meetings, and a report nobody reads.`
- `They also have the metric nobody mentions.`
- `The part everyone misses: distribution is the real moat.`

Good:

- `The city fined the landlord $12,000 for two missed inspections.`

Fix: State the fact. If nobody tracked it, say who should have and what it cost.

False positives: A literal statement that nobody does a thing, with the fact behind it, is fine ('Nobody on the night shift checks the loading dock, so the doors stay locked').

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `forward-signpost`

<!-- slop-lint off -->

**Forward signpost (an IOU to the reader).** Class `pattern`, severity `error`, kind `pattern`.

Forward signpost: the sentence promises that something comes later instead of saying it. An outline talking.

Bad:

- `It does not set prices, and it does not pick suppliers. Those come later in this guide.`
- `More on that later.`
- `As we'll see, the budget is too small.`

Good:

- `The tool sets prices from cost and demand. Choosing suppliers is a separate job, done by the buyer.`

Fix: Cut the promise. Say the thing now in one plain sentence, or let the later section arrive on its own; a linked jump is fine when the reader needs to go there.

False positives: A table of contents, a linked 'see Section 4' in a long report, and a literal schedule ('the second session comes later that afternoon') are fine.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Endings and openings

### `soft-cta-closer`

<!-- slop-lint off -->

**Soft call-to-action phrases.** Class `pattern`, severity `error`, kind `pattern`.

Soft call to action: a mood line about how good the follow-up will be ('that's where the magic happens') in place of a plain ask.

Bad:

- `Book a demo, and that's where the magic happens.`

Good:

- `Book a call at example.com/demo.`

Fix: Use one plain ask with a concrete action, and put any piece-specific context in the paragraph above it. If your profile sets cta_line, use that line verbatim. Add your own rejected closers to rejected_phrases.

False positives: A literal statement about where work happens ('that's where the work starts: the intake form') is fine; suppress it.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `aphoristic-capper`

<!-- slop-lint off -->

**Aphoristic capper (clever closing stinger).** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Aphoristic capper: the paragraph ends on a clever stinger that could be deleted without losing a fact.

Bad:

- `The team grew bigger. The product got slower.`
- `Next to price, design is cheap. Price needs a reason.`
- `What it cannot be is ignored.`
- `Between the old plan and the new one, only the price changed.`
- `That instinct backfires.`
- `This is where the money hides.`
- `Signing up is your agreement -- there is no other.`
- `The plan got cheaper. The support got worse.`
- `The pilot was a success. The rollout was a lesson.`

Good:

- `The test had passed. It had tested the wrong file.`
- `She tracked orders by hand until March. The system tracks them now.`

Fix: Cut the line. If the paragraph needs a last sentence, end on the last concrete fact, number or next step already in it. Do not re-voice the stinger softer.

False positives: The engine only nominates known capper shapes in the last sentence of a paragraph. Short plain closers such as 'The translation had done its job. The job was the wrong one.' and 'Nobody is being lazy.' are approved voice and do not fire. A short last line that carries a new number, name or step is fine.

Sources: elithrar anti-slop tells; stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 6 of 6 must_flag cases that name it

<!-- slop-lint on -->

### `standalone-aphorism`

<!-- slop-lint off -->

**Standalone aphorism paragraph or deck.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

A one-sentence paragraph or deck stated as a gnomic rule ('The exception gets argued in writing.'). It reads as a slogan with an unexplained referent.

Bad:

- `The budget gets decided in private.`
- `Pricing needs a reason.`

Good:

- `A refund request needs a receipt, and finance reviews it first.`

Fix: Fold it into the paragraph it belongs to, or replace it with the concrete fact it gestures at: who argues, where, and what happens.

False positives: Pronoun subjects, commas, colons and numbers exempt a line, so 'Nobody is in the office.' and 'The recipe has one rule: weigh the flour.' pass. Headings are not checked.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `summary-recap-ending`

<!-- slop-lint off -->

**Summary-recap ending.** Class `pattern`, severity `warn`, kind `pattern`.

Signposted recap: the ending restates the piece.

Bad:

- `In conclusion, the future of AI depends on...`
- `To sum up, we've explored three key themes...`

Good:

- `Send the signed form by Friday.`

Fix: End on the last concrete point, number or next step. The short version at the top already summarizes.

False positives: Structured academic abstracts.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `soft-cta-generic`

<!-- slop-lint off -->

**Generic soft call to action.** Class `pattern`, severity `warn`, kind `pattern`.

Generic soft CTA or engagement bait.

Bad:

- `Let's connect!`
- `Thoughts?`

Good:

- `Book a call: example.com/intro-call`

Fix: One concrete ask with no mood-setting: what to book, what to bring, what happens next.

False positives: A real question to a named person in an email is fine.

Sources: no-ai-slop (Peter Yang)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `generic-opener`

<!-- slop-lint off -->

**Generic scene-setting opener.** Class `pattern`, severity `warn`, kind `pattern`.

Scene-setting opener that could start any article.

Bad:

- `In today's fast-paced digital world, businesses must adapt.`
- `Imagine a world where every tool you use has a quiet intelligence behind it.`

Good:

- `A one-page permit took two to three months.`

Fix: Open on a scene or a concrete observation: a person, a number, a date.

False positives: Futures writing where the hypothetical is the subject.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); stop-slop (Hardik Pandya)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `stapled-on-ending`

<!-- slop-lint off -->

**Stapled-on ending.** Class `pattern`, severity `info`, kind `engine:stapled-ending`.

The last paragraph of the piece carries no number and no name from the piece. Check that the ending is grounded.

Bad:

- `In the end, every tool is only as good as the people who use it, and the best ones disappear into the work.`

Fix: Tie the ending to a specific number, person or fact already established, or cut it. Do not invent a new image to close on.

False positives: A closing line that calls back to the opening scene can work without a number; read it against the opening.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `locative-payoff-closer`

<!-- slop-lint off -->

**'That is where the X hides' closer.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

A paragraph-ending stinger that says where the important thing lives ('That gap is where the growth is hiding'). It announces significance and adds no fact.

Bad:

- `That gap is where the growth is hiding.`
- `This is where the risk lives.`
- `Pricing is where strategy goes to be tested.`

Good:

- `That is where 60 percent of churn happens.`

Fix: Cut it, or replace it with the number, name or consequence the paragraph was building to.

False positives: A closing sentence that names a real place or system and carries a figure is fine ('That is where 60 percent of churn happens'); the check ignores sentences that contain a digit.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `closer-without-fact`

<!-- slop-lint off -->

**Paragraph ends on a short line with no fact.** Class `pattern`, severity `warn`, kind `engine:closer-no-fact`, rhetorical device (fine once, a tell when repeated).

This paragraph ends on a short sentence, much shorter than the rest, with no number, name or figure in it. It reads as a moral added after the point was made.

Bad:

- `The team ran the pilot for six weeks across three offices and measured every referral that came through the new form, then compared the totals against the prior quarter before presenting them to the board. Most of the lift came from one office. The rest was noise.`

Good:

- `The team ran the pilot for six weeks across three offices and measured every referral that came through the new form. Most of the lift, 22 of 31 referrals, came from the Denver office.`

Fix: Delete the sentence and check that no fact is lost. If one is, fold it into the sentence before.

False positives: A short line that turns the argument is allowed (the density rule short-closer-density counts how many a piece has). Questions, paragraphs under three sentences, cited paragraphs and dialogue are skipped.

Evidence: measured: 24 finding(s) (0 error, 24 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `echo-stinger`

<!-- slop-lint off -->

**Echo stinger.** Class `pattern`, severity `warn`, kind `engine:echo-pair`, rhetorical device (fine once, a tell when repeated).

The paragraph ends on two short sentences built as a stinger: the second repeats a word and adds a payoff word (nothing, never, more, faster), or flips the first with 'did not'.

Bad:

- `The team built the report. The report built nothing.`
- `Costs fell. Trust fell faster.`
- `The sprint ended. The backlog did not.`

Good:

- `The team built the report. Finance read it on Monday.`

Fix: Keep the sentence that carries the fact and delete the echo, or join them into one sentence with the evidence.

False positives: Two plain short sentences that each state a fact are fine; the check needs a repeated content word and a payoff word, and skips sentences with a number or a name.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

## Tone

### `therapy-speak-reassurance`

<!-- slop-lint off -->

**Therapy-speak and unasked-for reassurance.** Class `pattern`, severity `error`, kind `pattern`.

Therapy-speak: emotional weight or reassurance attached to a routine action, or an answer to a worry nobody has.

Bad:

- `this discount is yours to keep`
- `the community welcomes you now`
- `Your report is private, and no one will be told.`
- `Most teams skip this step, and nobody wants to admit it. And that's okay.`

Good:

- `Settings saved.`
- `You can change this later in Settings.`

Fix: State the mechanical fact and stop. Reassure only about a worry a real person would have (is this permanent?), and then say the fact that answers it.

False positives: Real reassurance about a plausible worry is fine: 'You can change this later in Settings.'

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 1 finding(s) (1 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `dramatic-participle-tail`

<!-- slop-lint off -->

**Dramatic participle tail.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Ceremonial participle after a comma ('the key, handed over'; 'stands, founded'). Solemn register for a mechanical event.

Bad:

- `The deal is done, sealed.`
- `Your spot is saved, earned.`

Good:

- `Copy this link and send it to your manager.`

Fix: Say what happened in plain words: 'The link is ready. Nothing binds until they accept.'

False positives: Rare in plain prose. A list that ends on a participle ('drafted, reviewed, signed') is fine and is not matched unless the word is one of the ceremonial set.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `exclamation-point`

<!-- slop-lint off -->

**Exclamation points.** Class `house_style`, severity `warn`, kind `pattern`.

Exclamation point. Copy that states facts does not need one; exclamation-driven flavor reads as marketing.

Bad:

- `The sale ends tonight!`
- `Welcome back!`

Good:

- `Welcome back.`

Fix: Use a period.

False positives: Reported speech that really was shouted.

Evidence: measured: 39 finding(s) (0 error, 39 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `melodramatic-trailer-copy`

<!-- slop-lint off -->

**Melodramatic trailer copy.** Class `pattern`, severity `warn`, kind `pattern`.

Movie-trailer copy: poetic inversion and abstract nouns in place of saying what the product does.

Bad:

- `the first pages of this story are still unwritten`
- `A city seen from above, and lived from within`
- `your playlist is what lasts`
- `Every choice counts. What you build here stays done.`
- `Darkness swallows the checkout line, and the store manager rises to meet it!`

Good:

- `A shared calendar for neighborhood volunteers.`

Fix: Lead with what it does for the reader in one literal sentence; the benefit goes in the line under it.

False positives: A single plain emotional line at the end of a page, after the argument, is allowed. The register-neutral patterns are 'rises to meet it', 'the story is still being written' and 'the saga continues'. 'Supply rises to meet demand' and 'the rules are still being written' are not matched.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `reader-flattery`

<!-- slop-lint off -->

**Reader-directed flattery.** Class `pattern`, severity `warn`, kind `pattern`.

Flattery of the reader or the person you are replying to, with no fact behind it.

Bad:

- `As a forward-thinking leader, you already recognize that hiring needs to modernize.`
- `As a busy parent, you already know mornings are chaos.`
- `Savvy teachers already know this.`
- `Good catch!`
- `Smart people already know this.`

Good:

- `Your time to hire ran 41 days last quarter; peers ran 30.`
- `As a seasoned developer, I keep functions short.`

Fix: Cut it. Respect shows up as a number the reader can use.

False positives: The flattering word is the signal, so the reader can be anyone: a leader, a parent, a developer. A writer describing themselves ('As a seasoned developer, I...') is not flagged; the flattery form turns to 'you'.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes); Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `hedging-seesaw`

<!-- slop-lint off -->

**Hedging seesaw and stacked qualifiers.** Class `pattern`, severity `warn`, kind `pattern`.

Hedging: stacked qualifiers or a symmetrical both-sides frame with no conclusion.

Bad:

- `It could potentially be argued that the policy might have some effect.`
- `On one hand, AI saves time. On the other hand, it can introduce errors.`

Good:

- `The policy cut late-fee revenue 18% in the first year.`

Fix: Take the position the piece supports and give the other side one sentence.

False positives: Honest uncertainty about a contested question is fine when stated once and specifically.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; elithrar anti-slop tells

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `promotional-brochure-language`

<!-- slop-lint off -->

**Promotional brochure language.** Class `pattern`, severity `warn`, kind `pattern`.

Brochure language: adjectives that sell instead of describe.

Bad:

- `Nestled within the breathtaking region, the town offers a fascinating glimpse into its rich cultural heritage.`

Good:

- `The town has 12,000 residents and a Saturday market.`

Fix: Neutral, specific description. Cut adjectives that add no checkable information.

False positives: Quoted marketing copy under critique.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `narrator-from-a-distance`

<!-- slop-lint off -->

**Narrator from a distance.** Class `pattern`, severity `warn`, kind `pattern`.

Ungrounded generalization from outside the room ('Nobody designed this.', 'People tend to').

Bad:

- `Nobody designed this.`
- `People tend to underestimate this risk.`

Good:

- `Give a region a choice between new and existing, and they pick new every time.`

Fix: Put the reader or a named person in the scene, or give the example you are generalizing from.

False positives: A generalization backed by a cited study or the writer's own stated experience is fine.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `patronizing-analogy`

<!-- slop-lint off -->

**Patronizing analogy.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Reflexive 'think of it as' analogy.

Bad:

- `Think of it like a highway system for data.`

Good:

- `A bill of materials lists every part in a product and where each one is used.`

Fix: State the concept plainly, or use one analogy that clarifies something the reader does not know.

False positives: A well-chosen analogy for a general audience is good writing.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `false-vulnerability`

<!-- slop-lint off -->

**False vulnerability and performative candor.** Class `pattern`, severity `warn`, kind `pattern`.

Performative candor: a confession frame with nothing specific inside it.

Bad:

- `And yes, I'm openly in love with the platform model.`
- `This is not a rant; it's a diagnosis.`

Good:

- `I have said that sentence in a boardroom. It was true, and it was beside the point.`

Fix: Make the admission specific ('I did not understand how different the Spanishes are') or cut the frame.

False positives: Real first-person admissions are the voice to keep; this rule only matches the performance frame.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

## Sentence structure

### `tacked-on-tail-clause`

<!-- slop-lint off -->

**Tacked-on tail clause.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

Tacked-on tail clause: a casual generalization stapled after a comma ('..., and it is most of the job.').

Bad:

- `It is the busiest week of the year, and it is most of the revenue.`

Good:

- `It is the busiest week of the year.`

Fix: Cut the tail. Keep the image or fact before the comma if it is earned.

False positives: A metaphor before the comma can stay while only the tail is cut. A tail that adds a new fact is fine.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `false-agency-personification`

<!-- slop-lint off -->

**False agency and narrator personification.** Class `pattern`, severity `warn`, kind `pattern`.

False agency: an abstract noun doing a human verb ('the data tells us', 'the system takes notice'), or a narrator commenting on the reader from outside.

Bad:

- `The system takes notice.`
- `so the city now calls you`
- `Even the market stops to notice`
- `the data tells us`
- `a complaint becomes a fix`

Good:

- `The regions pick new every time; we saw it with every launch.`

Fix: Name the person who acted: 'The team fixed it that week.' In copy, write the moment as the reader lives it, second person and concrete.

False positives: Legal idioms ('the rule requires', 'the contract states') are not matched and are fine.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `dramatized-absence`

<!-- slop-lint off -->

**Dramatized absence (a shelf nobody watches).** Class `pattern`, severity `warn`, kind `pattern`.

Dramatized absence: 'nobody watches' turns a missing measurement into a scene. Say what is not measured.

Bad:

- `Every warehouse has a shelf nobody watches`
- `every room in that building had a thermostat with nobody watching it`

Good:

- `Most shelves are never counted.`
- `Nobody in the building logged the thermostat readings.`

Fix: State the gap as a fact: 'Most stages are never measured.' or 'No stage measured how long work waited in front of it.'

False positives: A literal statement about a monitoring role ('no one watches the overnight queue on weekends') can stay if it is true and specific.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `superficial-ing-analysis`

<!-- slop-lint off -->

**Superficial -ing analysis clause.** Class `pattern`, severity `warn`, kind `pattern`.

Trailing -ing clause that asserts meaning instead of adding a fact.

Bad:

- `The launch adds file search, highlighting the team's commitment to better workflows.`

Good:

- `The launch adds file search, so users can find old drafts without leaving the editor.`

Fix: Replace it with the concrete consequence: 'so users can find old drafts without leaving the editor.'

False positives: A trailing -ing clause that adds a new fact ('killing four workers') is normal English.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 3 finding(s) (0 error, 3 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `copula-avoidance`

<!-- slop-lint off -->

**Copula avoidance.** Class `pattern`, severity `warn`, kind `pattern`.

Avoids 'is' and 'has' with a fancier verb ('serves as', 'boasts').

Bad:

- `The app serves as a centralized hub for sponsor management.`
- `The gallery boasts over 3,000 square feet.`

Good:

- `The app is where sponsors are managed.`

Fix: Use is or has: 'Gallery 825 is LAAA's exhibition space.'

False positives: 'Serves as' is right when something acts in a role it is not (the chair serves as acting CEO).

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `correlative-bloat`

<!-- slop-lint off -->

**Correlative bloat ('Whether you're X or Y').** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

'Whether you're a beginner or an expert' scaffold.

Bad:

- `Whether you're a beginner or an expert, this guide will help.`
- `Whether you're a solo founder or a 400-person company, the same playbook applies.`

Good:

- `This is for the office manager who orders supplies.`

Fix: Name the reader you are writing for and drop the other half.

False positives: A real either/or instruction ('whether you rent or own, file by March 1') is fine.

Sources: elithrar anti-slop tells; skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `verbal-false-limbs`

<!-- slop-lint off -->

**Nominalization and verbal false limbs.** Class `pattern`, severity `warn`, kind `pattern`.

A noun phrase doing a verb's job ('made a decision to', 'has the ability to').

Bad:

- `The team made a decision to postpone the launch.`
- `The tool has the ability to process large datasets.`

Good:

- `The team postponed the launch.`

Fix: Use the verb: decided, can, analyzed, concluded.

False positives: Low.

Sources: George Orwell, Politics and the English Language (1946); no-ai-slop (Peter Yang)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `passive-voice`

<!-- slop-lint off -->

**Passive voice hiding the actor.** Class `house_style`, severity `warn`, kind `pattern`.

Agentless passive that hides who acted.

Bad:

- `A decision was made to close the branch.`

Good:

- `The board closed the branch.`

Fix: Name the actor: 'The board decided...'

False positives: General passive voice is reported only as a density figure (passive-voice-density).

Sources: George Orwell, Politics and the English Language (1946)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `wh-and-so-openers`

<!-- slop-lint off -->

**Wh- and 'So,'/'Look,' sentence openers.** Class `density`, severity `info`, kind `density`.

Pseudo-cleft openers ('What stops that is...') and 'So,'/'Look,' starters above the house density.

Bad:

- `What makes this hard is the missing data.`

Good:

- `The missing data makes this hard.`

Fix: Lead with the subject: 'A second reviewer stops that.' Keep the ones that pivot the argument.

False positives: A few of these on purpose are fine; only density is reported.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `passive-voice-density`

<!-- slop-lint off -->

**Passive voice density.** Class `house_style`, severity `info`, kind `density`.

Passive constructions above the house density.

Fix: Name the actor where the actor matters.

False positives: Passive is right when the actor is unknown or beside the point ('The claim was approved before the asset existed'). Privacy, terms, cookie, disclosure and accessibility pages are skipped by path: passive is the register of a data-flow disclosure.

Sources: George Orwell, Politics and the English Language (1946); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Ui copy

### `dramatized-system-copy`

<!-- slop-lint off -->

**Dramatized system and admin copy.** Class `pattern`, severity `warn`, kind `pattern`.

Dramatized system copy: all-caps shouting or flavor narration on a confirmation, error, toast or announcement.

Bad:

- `THE MARKET NEVER SLEEPS.`
- `The city awaits your next move!`
- `THE LEADERBOARD AWAITS ITS FIRST PLAYER`

Good:

- `Sound on, volume 2 of 5.`
- `Your order shipped on Tuesday.`

Fix: State the fact and stop: 'Hazards on, level 2 of 3.' A refusal says what to do in one clause: 'Remove your badge and step through again.'

False positives: Fiction and game text written in a character's voice is the one carve-out. The caps check needs a whole sentence in capitals, so one word in caps for emphasis and acronyms inside a sentence pass. A caps line with no end punctuation needs three or more words, so a two-acronym label (FDIC SOD) passes; table cells are not checked.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 6 finding(s) (0 error, 6 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `saas-cutesy-copy`

<!-- slop-lint off -->

**Cutesy SaaS system copy.** Class `pattern`, severity `warn`, kind `pattern`.

Cheerful SaaS filler on a system message.

Bad:

- `Oops! Looks like there's nothing here yet.`
- `Hang tight, we're on it!`

Good:

- `No events yet.`
- `Loading.`

Fix: Flat and factual. 'Saved.' 'No events yet.' 'Payment failed. Check the card number and try again.'

False positives: Reported speech and dialogue scenes are fine.

Sources: taste-skill (copy self-audit, section 9)

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `flavor-named-ui-chrome`

<!-- slop-lint off -->

**Interface chrome in flavor voice.** Class `pattern`, severity `warn`, kind `pattern`, off unless a profile lists it in `enable_rules`.

Navigation, heading, button or label named in the fiction's voice instead of for what it does. Off by default; a game or fiction product turns it on with enable_rules.

Bad:

- `The Keeper's Hand`
- `The Sky`
- `The Markets`
- `post to the herald`
- `Register Seal`
- `Establish Account`

Good:

- `Admin panel`
- `Weather`
- `Goods`
- `Schedule event`

Fix: Name chrome for its function: 'Admin panel', 'Map', 'Calendar', 'Schedule event', 'Create account'.

False positives: Content written in the fiction's voice (story text, character names, event names) keeps it; the rule is for chrome only. Title Case article titles are not checked.

Evidence: measured 2026-10-02: 0 finding(s) (0 error, 0 warning) in 80,126 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `generic-maturity-model`

<!-- slop-lint off -->

**Generic maturity-model self-assessment.** Class `pattern`, severity `warn`, kind `pattern`.

Stock maturity-model framing: staircase levels, a handful of generic questions, one blended score.

Bad:

- `a 2015 Marketing Maturity Model`
- `ten questions rolled into one blended score`

Good:

- `Password strength: weak. Turn on two-factor sign-in.`
- `Showing 2 of 4 items.`

Fix: Score each dimension on its own and report where the reader stands on each. Plain result labels. Questions tied to the real content.

False positives: A self-check with independently scored, content-specific questions is the approved design.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `option-overload`

<!-- slop-lint off -->

**Undifferentiated option overload.** Class `pattern`, severity `warn`, kind `engine:option-overload`.

A run of eight or more short, equally weighted items: in one sentence, or as consecutive list items or buttons.

Bad:

- `Eleven unrelated buttons in one toolbar: save, save as, export, print, share, archive, duplicate, rename, move, tag, close.`

Good:

- `Save and Share up front; everything else behind one menu.`

Fix: Group related actions, cut to what the context needs, and mark primary versus secondary. In an article, a list longer than four items becomes a table.

False positives: A flat directory (states, product names) can be long on purpose. Site navigation (<nav> or a nav class) and <select> options are not counted.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 4 finding(s) (0 error, 4 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `generic-value-proposition`

<!-- slop-lint off -->

**Mad-libs value proposition.** Class `pattern`, severity `warn`, kind `pattern`.

Value proposition that fits any product.

Bad:

- `We help teams grow.`
- `Our platform empowers teams to streamline workflows.`
- `We help families thrive.`
- `Your wellness journey starts now.`

Good:

- `I rebuild scheduling systems for veterinary clinics, on contract.`
- `It helps the seedlings grow two inches a week.`
- `Log your journey time in the app.`

Fix: Say what it does for this reader, with a number: 'See how many no-shows you had last month.'

False positives: The vague verb is the signal: 'help X grow' with nothing after it, for any X. A help sentence with an object or a measure ('helps the seedlings grow two inches a week') is not flagged.

Sources: taste-skill (copy self-audit, section 9); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `generic-ui-microcopy`

<!-- slop-lint off -->

**Generic UI microcopy.** Class `pattern`, severity `warn`, kind `pattern`.

Generic microcopy: a label or message that says nothing about this action.

Bad:

- `Something went wrong.`
- `Click here`

Good:

- `Book a 20-minute call`

Fix: Use the verb and object: 'Book a call', 'Download the playbook', 'Card declined: check the number.'

False positives: Only checked in UI strings and headings.

Sources: taste-skill (copy self-audit, section 9)

Evidence: measured: 14 finding(s) (0 error, 14 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `ambient-hover-text`

<!-- slop-lint off -->

**Unsolicited ambient labels and hover text.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Idle labels or floating text on objects at rest (game objects, tooltips added for flavor).

Bad:

- `a Home Stone floating the idle label 'Homestone'`
- `a server floating a steady 'Online' label`

Fix: Placed objects stay silent at rest; flash text only on an action or an error, then clear it. A worn HUD may carry one status line. Run lsl-lint for scripts.

False positives: Transient in-use and error text is fine.

<!-- slop-lint on -->

## Metaphor

### `retired-vocabulary`

<!-- slop-lint off -->

**Retired metaphor vocabulary.** Class `pattern`, severity `warn`, kind `engine:retired`.

Word from a metaphor or frame this piece retired, or one the previous piece used. Declared with <!-- slop-lint retired: term, term -->.

Bad:

- `Fuel for growth`
- `Turning the flywheel`
- `Launchpad calculator`
- `the digital north star (in the post right after the north star post)`

Good:

- `Where to start`
- `Your project list`

Fix: Rename the label or heading to something plain and literal. When a frame is cut, sweep every heading, label and tool name that depended on it.

False positives: Only fires on terms you declare. A literal use of the word (a real flywheel, a real engine) can be suppressed on its line.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `metaphor-overreach`

<!-- slop-lint off -->

**Metaphor overreach.** Class `pattern`, severity `warn`, kind `pattern`.

Ornamental metaphor that stands in for the claim.

Bad:

- `drawing from the rich tapestry of Arab, Indian, and Italian flavours`
- `Data is the lifeblood of the modern hospital.`

Good:

- `The dishes mix Arab, Indian and Italian cooking.`

Fix: Say the literal thing. Keep one concrete, earned image per piece at most.

False positives: A central metaphor the piece is built on on purpose is a choice; check it against the metaphor-spacing rule instead.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; taste-skill (copy self-audit, section 9)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `dying-metaphors-cliches`

<!-- slop-lint off -->

**Dying metaphors and stock idioms.** Class `pattern`, severity `warn`, kind `pattern`.

Stock idiom that stopped carrying an image years ago.

Bad:

- `The rate cut is a double-edged sword.`

Good:

- `The rate cut helps borrowers and squeezes the margin.`

Fix: Say the literal thing.

False positives: Reported speech.

Sources: George Orwell, Politics and the English Language (1946)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `abandoned-metaphor-residue`

<!-- slop-lint off -->

**Abandoned metaphor left in labels.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Labels and headings that only make sense under a frame the piece dropped.

Bad:

- `Fuel for growth`
- `Turning the flywheel`
- `2 of 4 gears turning`
- `Launchpad calculator`

Fix: When a frame is cut, list its words in <!-- slop-lint retired: ... --> and rename every hit (retired-vocabulary does the search).

False positives: A metaphor still carrying weight elsewhere in the piece can stay.

<!-- slop-lint on -->

### `metaphor-reuse-across-pieces`

<!-- slop-lint off -->

**Signature metaphor reused in consecutive pieces.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

The central metaphor or signature device repeats the previous piece.

Bad:

- `'the flywheel' as the spine of the post right after the flywheel post`

Fix: Check what the last one or two months of articles used (frontmatter dates) and pick something else. Declare the previous piece's signature words as retired so the engine catches them.

False positives: Reuse after one to two months is fine. Template chrome shared by every article is exempt.

<!-- slop-lint on -->

### `dead-metaphor-overuse`

<!-- slop-lint off -->

**One metaphor beaten across the piece.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

A single image repeated until it carries nothing.

Bad:

- `bridges and roads used 30+ times in one article`

Fix: Use it once, memorably, then let plain language carry the rest.

False positives: A deliberate spine metaphor that does new work each time.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

<!-- slop-lint on -->

### `metaphor-definition`

<!-- slop-lint off -->

**Metaphor asserted as a definition.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

A literal thing is defined as a vivid object ('A newsletter is a conversation that never ends'). The image does the persuading, so the claim never gets its evidence.

Bad:

- `A newsletter is a conversation that never ends.`
- `Your pricing page is a handshake that never ends.`
- `Your calendar is a battlefield where meetings win by default.`
- `Your brand is a promise you make every single day.`

Good:

- `A cache is a store that returns recent results without recomputing them.`
- `The newsletter goes to 4,000 readers every Tuesday.`

Fix: Say the literal claim with its number or example, and keep the image only if it survives being stated plainly. If you keep it, it needs to be the only one in the piece.

False positives: Real definitions ('A cache is a store that never expires entries until evicted') match the shape. Read the noun: a literal category is fine, a physical object standing in for a business or idea is the tell. Warn only.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 5 of 5 must_flag cases that name it

<!-- slop-lint on -->

## Chat replies

### `buried-answer`

<!-- slop-lint off -->

**Buried answer and rambling reply.** Class `pattern`, severity `warn`, kind `pattern`.

The reply opens by surveying options instead of answering.

Bad:

- `There are several factors to consider when choosing a core provider.`
- `Great question! There are several factors to consider when picking a core provider.`

Good:

- `Use the variant lane. It takes two days and review reads only the change.`

Fix: First sentence is the answer or recommendation. Supporting detail after it, trimmed.

False positives: A real 'it depends' followed at once by the deciding factor is fine.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `offer-closer`

<!-- slop-lint off -->

**Offer-to-do-more closer.** Class `artifact`, severity `warn`, kind `pattern`.

Reply ends by offering to do more instead of stopping.

Bad:

- `Would you like me to expand on any section?`

Good:

- `Which version goes to print, A or B?`

Fix: Stop after the answer. Ask a question only when the work depends on the answer, and make it specific.

False positives: A real blocking question ('Which of the two lists do you want published?') is fine.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

## Structure

### `manufactured-rule-of-three`

<!-- slop-lint off -->

**Manufactured rule of three.** Class `pattern`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

A tidy set of three: either an announced count ('the next three steps') or a triad of abstract nouns or adjectives.

Bad:

- `The next three steps cover setup, billing and support.`
- `Efficient, effective, and reliable.`
- `Attendees can expect innovation, inspiration, and industry insights.`

Good:

- `The branch is open Monday, Wednesday, and Friday.`

Fix: Let the content set the count. Cut a padding item; keep two if two is true. A factual list of three concrete things is fine.

False positives: The engine no longer flags every three-item list. 'Open Monday, Wednesday, and Friday' and 'medical, legal, and regulatory review' pass.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); anti-ai-slop-writing (jalaalrd); anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 5 finding(s) (0 error, 5 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `hunt-for-referent`

<!-- slop-lint off -->

**Reader sent to hunt for referenced material.** Class `pattern`, severity `warn`, kind `pattern`.

Points the reader at material elsewhere in the piece without restating or linking it.

Bad:

- `The open issues are the ones above, starting with the venue.`

Good:

- `Three questions are still open: the venue, the date, and the budget.`

Fix: Restate the item at the point of use, or link to its anchor.

False positives: A linked jump to an anchored section is fine.

Evidence: measured: 4 finding(s) (0 error, 4 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `despite-challenges-formula`

<!-- slop-lint off -->

**'Despite its challenges' formula.** Class `pattern`, severity `warn`, kind `pattern`.

Formula: acknowledge vague challenges, then wave them away.

Bad:

- `Despite these challenges, the initiative continues to thrive.`

Good:

- `Traffic rose after three IT parks opened in 2015; the city began a drainage project in 2022.`

Fix: Name what went wrong and what was done, with dates and numbers.

False positives: A real problem-and-fix account with evidence is argument.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `fractal-summaries`

<!-- slop-lint off -->

**Fractal summaries and section recaps.** Class `pattern`, severity `warn`, kind `pattern`.

Summary at every level: section previews and recaps.

Bad:

- `In this section, we'll explore the pricing model.`
- `As we've seen, the budget is too small.`

Good:

- `Every shelf in the warehouse is counted weekly.`

Fix: Summarize once, in the short version at the top. Sections make their point and stop.

False positives: Academic papers use previews by convention.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is); elithrar anti-slop tells

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `faq-padding`

<!-- slop-lint off -->

**FAQ padding.** Class `pattern`, severity `warn`, kind `pattern`.

FAQ section bolted onto prose.

Bad:

- `## Frequently asked questions`

Fix: Answer the questions in the body where they come up, or cut them.

False positives: A real support page is fine.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 10 finding(s) (0 error, 10 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `content-duplication`

<!-- slop-lint off -->

**Content duplication.** Class `density`, severity `warn`, kind `engine:content-duplication`.

The same sentence appears twice in the body, whole or embedded in a longer sentence.

Bad:

- `(paragraph 3 and paragraph 17 carry the same sentence)`
- `Later in the review, the committee noted that <the same sentence from paragraph 2>.`

Fix: Delete the repeat, or rewrite the second as a callback that adds something.

False positives: Not compared: frontmatter, and a repeat where either copy is a pull quote, callout, markdown blockquote, deck, or glance or summary box (a class name containing pq, pullquote, callout, glance, tldr, summary or deck), since those repeat body text by design.

Sources: elithrar anti-slop tells; anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 13 finding(s) (0 error, 13 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `uniform-paragraph-shape`

<!-- slop-lint off -->

**Uniform paragraph shape.** Class `density`, severity `info`, kind `engine:paragraph-shape-cv`.

Paragraphs are all the same length in sentences.

Bad:

- `(every paragraph three sentences)`

Fix: Let some paragraphs be one sentence and some run four. Do not force every section into the same shape.

False positives: Reference docs are uniform on purpose.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is); elithrar anti-slop tells

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `ordinal-signposting`

<!-- slop-lint off -->

**Ordinal signposting.** Class `density`, severity `info`, kind `density`.

Paragraphs that enumerate with ordinals: a listicle in a trench coat.

Bad:

- `The first wall is... The second wall is... The third wall is...`

Fix: Make it a real list or table, or vary the openers so it reads as argument.

False positives: One ordinal is fine ('Price is the first').

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `diff-anchored-writing`

<!-- slop-lint off -->

**Diff-anchored writing in docs.** Class `density`, severity `info`, kind `density`.

Docs that describe the change instead of the current state.

Bad:

- `The config now uses YAML (previously, it used JSON).`

Good:

- `The config is YAML.`

Fix: Describe what is true now. Change history belongs in commit messages.

False positives: Commit messages and changelogs should describe the change.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `over-explained-instructions`

<!-- slop-lint off -->

**Over-explained instructions.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Rationale and caveats before the steps.

Bad:

- `(three paragraphs of background, then: step 1 do this, step 2 do this)`

Good:

- `1. Open the board. 2. Click it. 3. Pick Settings.`

Fix: A bare numbered list. The reader will ask if they need the why.

False positives: One line of context that picks which procedure applies is fine.

<!-- slop-lint on -->

## Claims and evidence

### `portable-generic-sentence`

<!-- slop-lint off -->

**Portable generic sentence.** Class `pattern`, severity `warn`, kind `pattern`.

Portable sentence: true of any subject, so it says nothing about this one.

Bad:

- `The reasons are structural.`
- `The implications are significant.`
- `This is the deepest problem.`
- `The stakes are high.`
- `The integration improved efficiency.`
- `The tool significantly improves engineering productivity.`
- `92% of teams report improved outcomes.`

Good:

- `The tool cut review time from 30 minutes to 8.`

Fix: Replace with the number, name, mechanism or date that only fits this subject ('cut review time from 30 minutes to 8'), or cut it.

False positives: A vague topic sentence followed at once by the specifics is fine.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); elithrar anti-slop tells

Evidence: measured: 3 finding(s) (0 error, 3 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `fabricated-specificity`

<!-- slop-lint off -->

**Fabricated or unsourced specifics.** Class `evidence`, severity `warn`, kind `pattern`.

Precision that looks invented: a study with no citation, 99.99%, '4.1x faster', or a quote attribution with no source.

Bad:

- `99.99% satisfaction`
- `4.1x faster`
- `A recent study by McKinsey found that retailers...`

Good:

- `Veeva's system data across 350+ companies shows 1.3 review cycles per asset.[^9]`

Fix: Cite the primary source in a footnote, round to what the method supports, or label the figure as an illustration.

False positives: Real measured numbers with a footnote nearby are fine. Every number needs a source either way.

Sources: taste-skill (copy self-audit, section 9); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `pseudo-precision`

<!-- slop-lint off -->

**Hedged pseudo-precision ('up to X%').** Class `evidence`, severity `warn`, kind `pattern`.

'Up to X%' sounds quantified and commits to nothing: it is true if one case hit X.

Bad:

- `Save up to 40% on processing costs.`

Good:

- `Median savings were 12% across 30 clinics in the 2025 pilot.[^3]`

Fix: Give the typical result and the baseline, or the specific case where X happened, with its source.

False positives: Skipped when a footnote or link sits in the same paragraph or the next one.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `vague-quantifiers`

<!-- slop-lint off -->

**Vague quantifiers in place of a number.** Class `evidence`, severity `info`, kind `pattern`.

Vague quantifier where a checkable number belongs.

Bad:

- `A growing number of school districts have adopted this approach.`

Good:

- `41 of the 150 largest school districts use it, per their 2025 budget filings.`

Fix: Give the count, share or date range, with a source. If no number exists, say what is known and from where.

False positives: Skipped when the sentence already contains a digit.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `citation-fabrication-tells`

<!-- slop-lint off -->

**Citation-fabrication tells.** Class `evidence`, severity `warn`, kind `pattern`.

Academic-looking citation (Author, Year) or DOI. Well-formed citations are what a model invents most convincingly.

Bad:

- `(Chen & Alvarez, 2023)`
- `doi 10.1234/abcd.5678 with no reference list`

Good:

- `Kimball Group, 'Type 2: Add New Row'.[^8]`

Fix: Open the source and confirm it exists and says this, then convert it to a footnote with a link. Never publish a citation you have not opened.

False positives: Every real citation also fires; this rule is a verification prompt.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `importance-puffery`

<!-- slop-lint off -->

**Importance and legacy puffery.** Class `pattern`, severity `warn`, kind `pattern`.

Puffery: the sentence asserts significance instead of showing the consequence.

Bad:

- `The launch marks a pivotal moment for the company.`

Good:

- `The launch is the company's first paid product.`

Fix: State the fact and let the reader judge. 'The launch is the company's first paid product.'

False positives: A fact can be pivotal; show it with the consequence ('after the ruling, 40 states changed their statute').

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `grandiose-prediction`

<!-- slop-lint off -->

**Grandiose prediction and stakes inflation.** Class `pattern`, severity `warn`, kind `pattern`.

Stakes inflation: a sweeping claim about the future.

Bad:

- `This will fundamentally reshape how we think about everything.`
- `It will define the next era of computing.`

Good:

- `If the rule passes, firms under 50 employees keep the exemption.`

Fix: Scope it to something defensible: what changes, for whom, by when, and the evidence.

False positives: Some things are big; the fix is a scoped claim.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 1 of 1 must_flag cases that name it

<!-- slop-lint on -->

### `weasel-attribution`

<!-- slop-lint off -->

**Weasel attribution.** Class `evidence`, severity `warn`, kind `pattern`.

Unnamed authority: 'experts agree', 'studies show'.

Bad:

- `Industry reports suggest that adoption is accelerating.`
- `Experts believe it plays a crucial role.`

Good:

- `The 2025 city budget puts 12 percent of spending into parks.[^3]`

Fix: Name the source and cite it, or cut the claim.

False positives: Summarizing a cited survey's overall finding is fine when the citation is right there.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 3 finding(s) (0 error, 3 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `knowledge-gap-speculation`

<!-- slop-lint off -->

**Knowledge-gap disclaimer and gap-filling guess.** Class `evidence`, severity `warn`, kind `pattern`.

Disclaimer about missing information, usually followed by a guess.

Bad:

- `While specific details about the company's founding are limited, it appears to date from the 1990s.`

Good:

- `No public benchmark for it exists; I looked.`

Fix: Find the fact and cite it, or say plainly that it is unknown and stop.

False positives: Saying 'no public benchmark exists; I looked' is honest and is not matched.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `media-coverage-as-proof`

<!-- slop-lint off -->

**Media coverage offered as proof.** Class `evidence`, severity `warn`, kind `pattern`.

Coverage listed as evidence of importance.

Bad:

- `She was featured in Vogue, Wired, and other prominent media outlets.`

Fix: Report what the source said about the subject.

False positives: Rare outside press-release writing.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `vague-connection`

<!-- slop-lint off -->

**Vague connection or association.** Class `evidence`, severity `info`, kind `density`.

'Associated with' in place of the actual relationship, above the house density.

Bad:

- `He is associated with the Rajhans Orchestra.`

Good:

- `He founded the Rajhans Orchestra.`

Fix: Name the relationship: founded, led, caused, is used for.

False positives: Statistical association is a real claim; only density is reported.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `historical-analogy-stacking`

<!-- slop-lint off -->

**Historical analogy stacking.** Class `density`, severity `info`, kind `density`.

Several famous-company analogies in one piece.

Bad:

- `Apple didn't build Uber. Facebook didn't build Spotify. Stripe didn't build Shopify.`

Fix: Pick one analogy and develop it with real specifics, or use an example from your own field.

False positives: Only a company named in a comparison counts ('the next Kodak', 'the Uber of banking', 'Apple didn't build Uber'). A vendor named as a fact ('Email: Apple iCloud Mail') is not counted. A piece about one of these companies still needs a read.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `weak-quantifier-density`

<!-- slop-lint off -->

**Weak quantifier density.** Class `evidence`, severity `info`, kind `density`.

'Many', 'several' and 'various' above the house density.

Fix: Replace some with counts.

False positives: Only density is reported.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `unsourced-figure`

<!-- slop-lint off -->

**Figure with no nearby source.** Class `evidence`, severity `info`, kind `engine:unsourced-figure`.

A figure that reads as an external fact appears with no footnote or link nearby. Source it, or label where it comes from (your own data, a calculation, an illustration). Internal figures the author supplied are fine; the point is provenance, not citation style.

Bad:

- `92% of teams report improved outcomes.`

Good:

- `62% of renters moved within three years.[^1]`

Fix: Footnote every number to a dated primary source, or label it as a placeholder in the text and in About the numbers.

False positives: Not counted: a figure that is cited anywhere else in the piece (reused after its footnote, or previewed in a deck before it), figures in scripted dialogue and in pull quotes. Still a false positive: worked examples labeled as placeholders.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `restatement-as-new`

<!-- slop-lint off -->

**Restatement presented as new information.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

A rewrite repeats the same number or claim in new words (often with a citation added) and gives the reader nothing new to act on.

Bad:

- `Each new hire costs $4,000 to onboard and $900 a year in software. (rewritten with the same $900 and three citations)`

Fix: Keep only the version that tells the reader something new they can use; cut the rest.

False positives: Adding a missing source to an unsourced number is a real fix on its own.

<!-- slop-lint on -->

### `causal-glue-participle`

<!-- slop-lint off -->

**Causal glue ('X, enabling Y').** Class `evidence`, severity `warn`, kind `pattern`, rhetorical device (fine once, a tell when repeated).

A participle clause asserts a consequence ('X, enabling Y') with no evidence that X caused Y or how much.

Bad:

- `The team moved the files to one drive, enabling designers to move faster.`
- `We rebuilt the checkout form, helping customers finish in fewer steps.`

Good:

- `The valve closed and the flow stopped.`

Fix: Say what changed and by how much, or cut the clause. If the effect is real, give the measurement.

False positives: A cause the reader can verify from the sentence itself is fine ('The valve closed, stopping the flow'). Repeated use in one piece is the tell, so a single hit is shown as information only unless the profile sets device_policy to ban.

Evidence: measured: 4 finding(s) (0 error, 4 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `unnecessary-inference`

<!-- slop-lint off -->

**Unnecessary inference.** Class `evidence`, severity `warn`, kind `engine:inference`, rhetorical device (fine once, a tell when repeated).

A sentence restates the conclusion the reader already draws from the figure before it ('That means customers were happier').

Bad:

- `Complaints fell 42 percent. That means customers were having a better experience.`

Good:

- `Complaints fell 42 percent. We cut the support team's overtime budget in half.`

Fix: Delete the sentence, or replace it with a consequence the reader could not infer (a cost, a decision, a date).

False positives: An inference that adds a non-obvious step, such as what the figure implies for next quarter's budget, is fine. Judge it against the preceding sentence.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Headlines and headings

### `headline-formulas`

<!-- slop-lint off -->

**Headline formulas.** Class `pattern`, severity `warn`, kind `pattern`.

Formula headline: colon plus How/Why, numbered listicle, 'ultimate guide', gerund opener, or clickbait question.

Bad:

- `Content Strategy: How Small Teams Punch Above Their Weight`
- `7 Signs Your Onboarding Is Broken`
- `The Ultimate Guide to Meal Prep`
- `Navigating the Future of Retail`

Good:

- `Your Invoices Have No Due Date`
- `Four Fixes`

Fix: A title is two or three plain words or one literal claim (Dark Content; Content Is Data). A subtitle names the tension.

False positives: Section headings may be real reader questions ('So, why should I switch?'); the question and colon forms only apply to titles.

Sources: anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 3 of 3 must_flag cases that name it

<!-- slop-lint on -->

### `formulaic-headings`

<!-- slop-lint off -->

**Formulaic headings.** Class `house_style`, severity `warn`, kind `pattern`.

Template heading ('Why it matters', 'Key takeaways', 'Final thoughts').

Bad:

- `## Why It Matters`
- `## Key Takeaways`
- `## Final Thoughts`

Good:

- `## Review reads the diff`

Fix: Make each H2 a claim or a strong noun ('Review reads the diff').

False positives: Docs and READMEs may want 'How it works'.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `title-case-headings`

<!-- slop-lint off -->

**Title Case section headings.** Class `house_style`, severity `warn`, kind `pattern`.

Section heading in Title Case. Many house styles use sentence case for H2 and below; disable this rule in profile.json if yours does not.

Bad:

- `## Strategic Negotiations And Global Partnerships`

Good:

- `## Strategic negotiations and global partnerships`

Fix: Sentence case: 'Content with no parent costs money and invites fines'.

False positives: Only markdown files are checked: article titles are Title Case on the site, and offer names on .astro pages are product names. Headings made of proper nouns can be suppressed.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

## Rhythm

### `anaphora-runs`

<!-- slop-lint off -->

**Anaphora runs.** Class `density`, severity `warn`, kind `engine:anaphora`.

Three or more sentences in a row open on the same word.

Bad:

- `We changed the menu. We changed the hours. We changed the staff.`

Good:

- `We changed the menu, the hours and the staff, and sales did not move.`

Fix: Merge two of them or restructure one opener. Keep the repetition only if it is a deliberate list you would defend.

False positives: A run of exactly three questions ('Would X? Would Y? Would Z?') or conditions ('If A... If B... If C...') is reported as info, not a warning: it is usually a deliberate list. Read it aloud first.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is); anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 1 finding(s) (0 error, 1 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 2 of 2 must_flag cases that name it

<!-- slop-lint on -->

### `dramatic-fragmentation`

<!-- slop-lint off -->

**Dramatic fragmentation and staccato.** Class `density`, severity `warn`, kind `engine:fragment-run`.

Three or more very short fragments in a row, or 'X. And Y. And Z.' staccato.

Bad:

- `He published this. Openly. In a book. As a priest.`
- `X. And Y. And Z.`

Good:

- `He published it openly, in a book, while he was a priest.`

Fix: Use full sentences. Save a fragment for one moment that earns it.

False positives: One short line after a long sentence is voice. Dialogue lines can be short.

Sources: stop-slop (Hardik Pandya); skill-deslop and tropes.fyi (Stephen Turner, ossama.is); elithrar anti-slop tells

Evidence: measured: 2 finding(s) (0 error, 2 warning) in 60,970 words of human writing from before chat models (tests/human, default profile); flags 4 of 4 must_flag cases that name it

<!-- slop-lint on -->

### `uniform-sentence-length`

<!-- slop-lint off -->

**Uniform sentence length.** Class `density`, severity `info`, kind `engine:sentence-length-cv`.

Sentence lengths are too even (low variation). Uniform rhythm is the most measurable machine tell.

Bad:

- `(every sentence 14 to 18 words)`

Fix: Mix a four-word sentence with a thirty-word one nearby. Natural voice runs long and loose with short pivots.

False positives: Short copy and lists run even by nature; the check needs 15+ sentences.

Sources: anti-ai-slop-writing (jalaalrd); elithrar anti-slop tells

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `short-closer-density`

<!-- slop-lint off -->

**Short closers across the piece.** Class `density`, severity `info`, kind `engine:short-closers`.

Paragraphs ending on a short closer with no number or name in it, and one-line paragraphs of that kind, counted across the piece. The longform rule allows three, placed where they argue.

Fix: Run --verbose to list them. Keep the ones that carry a fact or a turn; fold the rest into the sentence before.

False positives: Each closer may be fine alone; this is a count for the human review. Not counted: closers with a number or a name (they carry a fact), scripted dialogue, decks, glance boxes and pull quotes.

Sources: anti-slop verification pass, 2026-09-24 (precision and recall findings)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

## Voice

### `profile-rejected-phrasing`

<!-- slop-lint off -->

**Rejected phrasing from the profile.** Class `pattern`, severity `warn`, kind `pattern`.

Phrasing you have already rejected (listed in profile.json under rejected_phrases). Do not reintroduce it in a rewrite.

Bad:

- `(any phrase listed in the profile's rejected_phrases)`
- `at the end of the day`
- `Balance: 40 pts`

Good:

- `Balance: 40 points`

Fix: Use the accepted replacement recorded next to the phrase in your profile notes, or rewrite the sentence.

False positives: Only the exact rejected wording and near variants are matched.

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `voice-frame-mismatch`

<!-- slop-lint off -->

**Voice and frame mismatch.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

A line attributes a framing or motive the author would not use about themselves or their work.

Bad:

- `what the sales sheet said the plan included`
- `I have been the go-to fixer on every team I joined`

Fix: Use the author's own stated framing, or ask. Read the line as a skeptical buyer would and check what it implies.

False positives: Person-specific; apply only against the author's stated framing, which lives in the profile voice notes.

<!-- slop-lint on -->

### `sterile-voiceless`

<!-- slop-lint off -->

**Sterile, voiceless prose.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Clean of tells and also of any person: no opinion, no first person where it is earned, no specific scene.

Bad:

- `The experiment produced interesting results. Some developers were impressed while others were skeptical. The implications remain unclear.`

Fix: Add the one thing the author saw that the reader has not: a number, a scene, a plain moral statement.

False positives: Memos and UI copy are meant to be plain.

Sources: humanizer skill; no-ai-slop (Peter Yang)

<!-- slop-lint on -->

### `overcorrection`

<!-- slop-lint off -->

**Overcorrection and manufactured imperfection.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Slop removal that flattens the piece, or fake mess added to seem human (random typos, forced casualness, profanity the author did not use).

Bad:

- `(a rewrite that lost the number to lose the dash)`

Fix: Restore the fact or image that was cut. Mess is never added on purpose.

False positives: Manual check. A real admission, a named mistake or a rough edge that happened is voice, not overcorrection; only invented mess is.

Sources: no-ai-slop (Peter Yang); elithrar anti-slop tells

<!-- slop-lint on -->

## Formatting

### `markdown-leak`

<!-- slop-lint off -->

**Markdown leaking into plain-text destinations.** Class `artifact`, severity `warn`, kind `pattern`.

Markdown syntax in a destination that will not render it (email, LinkedIn, commit message, plain text).

Bad:

- `**Recommended:** use the variant lane`
- `## Next steps (pasted into an email)`

Good:

- `Recommended: use the variant lane.`

Fix: Strip the markup, or convert to the destination's own format.

False positives: Only checked for .txt files and --dest=plain input.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 69 finding(s) (0 error, 69 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `bold-label-bullets`

<!-- slop-lint off -->

**Bold-label bullets.** Class `house_style`, severity `warn`, kind `pattern`.

Bullet list where every item opens with a bold label and a colon.

Bad:

- `- **Performance:** Performance has been enhanced through optimized algorithms.`

Good:

- `The update loads pages faster and encrypts data at rest.`

Fix: Write it as connected prose when the items build an argument; keep a plain list when they are truly separate.

False positives: Reference docs and glossaries use this legitimately.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 19 finding(s) (0 error, 19 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `emoji-and-hashtag-decoration`

<!-- slop-lint off -->

**Emoji decoration and hashtag stacks.** Class `house_style`, severity `warn`, kind `pattern`.

Emoji used as heading or bullet decoration, or a stack of hashtags.

Bad:

- `(rocket emoji) Launch Phase`
- `#marketing #growth #leadership #mindset`

Good:

- `Launch phase`

Fix: Remove them; let the words carry the meaning.

False positives: The non-ASCII rule also reports the emoji itself.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill; anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `linkedin-broetry`

<!-- slop-lint off -->

**LinkedIn broetry.** Class `house_style`, severity `warn`, kind `engine:broetry`.

Five or more one-sentence paragraphs in a row: the LinkedIn line-break rhythm.

Bad:

- `I got fired. /  / It was the best day of my life. /  / Here's why. /  / ...`

Fix: Join the lines into paragraphs of two or three sentences.

False positives: Dialogue scenes, and short posts where the one-line-per-sentence format was asked for.

Sources: skill-deslop and tropes.fyi (Stephen Turner, ossama.is)

Evidence: measured: 5 finding(s) (0 error, 5 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `decorative-bold`

<!-- slop-lint off -->

**Decorative bold.** Class `house_style`, severity `info`, kind `density`.

Bold used for emphasis across the body.

Bad:

- `The **key** point is that **every** asset needs a **parent**.`

Fix: Bold only a term being defined, once. Let sentence order carry emphasis.

False positives: Footnote source labels and table headers are skipped.

Sources: Wikipedia: Signs of AI writing (WikiProject AI Cleanup); humanizer skill

Evidence: measured: 0 finding(s) (0 error, 0 warning) in 60,970 words of human writing from before chat models (tests/human, default profile)

<!-- slop-lint on -->

### `bullets-where-prose`

<!-- slop-lint off -->

**Bullets where prose would read better.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

An argument chopped into bullets.

Fix: Write the connected paragraph; keep lists for truly parallel items (and tables for more than four).

False positives: Reference material and steps.

Sources: elithrar anti-slop tells

<!-- slop-lint on -->

## Visual design

### `ai-default-visual-ui`

<!-- slop-lint off -->

**AI-default visual UI tells.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Purple gradients, Inter everywhere, emoji icon tiles.

Fix: Out of scope for this linter; use the impeccable and taste-skill skills.

False positives: Manual check. A gradient, icon tile or card grid that the site's design system already uses on purpose is not a tell.

Sources: taste-skill (copy self-audit, section 9)

<!-- slop-lint on -->

## Guardrails

### `detector-guardrails`

<!-- slop-lint off -->

**Detector guardrails.** Class `pattern`, severity `info`, kind `manual` (not automated: human review checklist only).

Linter hits are candidates, and AI detectors are unreliable, with documented bias against non-native writers.

Fix: Never use this skill, its score or any detector to claim that a named person used AI.

False positives: Not a pattern. Scoring your own draft for revision is the intended use; only a claim about a named person is out.

Sources: Liang et al. 2023, GPT detectors are biased against non-native English writers (arXiv:2304.02819)

<!-- slop-lint on -->

## Sources

- Wikipedia: Signs of AI writing (WikiProject AI Cleanup)
- humanizer skill
- anti-slop verification pass, 2026-09-24 (precision and recall findings)
- SpeakHuman red team, 2026-10-02 (homoglyph and zero-width bypass under the light profile)
- no-ai-slop (Peter Yang)
- Kobak et al. 2024, excess vocabulary in academic writing (arXiv:2406.07016)
- taste-skill (copy self-audit, section 9)
- SpeakHuman red-team pass, 2026-10-02 (false positives on human essays and commit messages)
- elithrar anti-slop tells
- SpeakHuman human corpus, 2026-10-02 (Enron business email: six of eight errors were these lines)
- SpeakHuman red-team pass, 2026-10-02 (silent suppression)
- stop-slop (Hardik Pandya)
- skill-deslop and tropes.fyi (Stephen Turner, ossama.is)
- anti-slop critic pass, 2026-09-24 (missing patterns and regex fixes)
- anti-ai-slop-writing (jalaalrd)
- George Orwell, Politics and the English Language (1946)
- Liang et al. 2023, GPT detectors are biased against non-native English writers (arXiv:2304.02819)
