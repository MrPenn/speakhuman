<!-- Every case line ends with an expect comment naming the rule ids that may
catch it (any one is enough), or "any". run_tests.py asserts each case line gets
at least one error or warning on that line, and one of the named ids when ids
are given. The cases are synthetic: written to exercise each family of slop
(closers, X-not-Y, setup lines, house words, CTAs, claims, structure, residue)
without quoting any one writer's rejected lines. Add your own rejected phrasings
to your profile fixtures, not to this file. Each case is its own paragraph, so
it is also the last sentence of a paragraph. -->


clever closers, stingers and tails

The vendor shipped late, and it is most of the job. <!-- expect: tacked-on-tail-clause -->

Procurement approved the spend and nobody read the contract. <!-- expect: faux-insight-nobody-framing -->

The team built the report. The report built nothing. <!-- expect: echo-stinger -->

Costs fell. Trust fell faster. <!-- expect: echo-stinger -->

That instinct backfires. <!-- expect: aphoristic-capper -->

This is where the risk lives. <!-- expect: aphoristic-capper, locative-payoff-closer -->

That gap is where the growth is hiding. <!-- expect: locative-payoff-closer -->

Clarity compounds. <!-- expect: standalone-aphorism -->

Good data needs an owner. <!-- expect: standalone-aphorism -->

And that is the whole point. <!-- expect: aphoristic-capper, banned-intensifiers -->

It was never about the software. <!-- expect: x-not-y-contrast -->

The rest is execution. <!-- expect: aphoristic-capper -->

The contract renews in March -- which is when the price goes up, and nobody is watching it. <!-- expect: dash-clause, dramatized-absence, faux-insight-nobody-framing -->


content after a dash

It's not a staffing problem, it's a scheduling problem. <!-- expect: x-not-y-strict -->


X, not Y and its cousins

This isn't about the tool. It's about the habit. <!-- expect: x-not-y-strict -->

The page is a form, not a flyer. <!-- expect: x-not-y-contrast -->

One is a pilot with an end date. The other is a permanent team. <!-- expect: x-not-y-contrast -->

Not a dashboard. Not a report. A decision. <!-- expect: dramatic-fragmentation, negative-listing -->

We do not sell software, we sell outcomes. <!-- expect: x-not-y-strict -->

The goal is not more content but better content. <!-- expect: x-not-y-strict -->

Not just faster, but cheaper. <!-- expect: x-not-y-strict -->


reframe pairs, metaphors asserted as definitions, stock images

Most firms treat the audit as a checkbox. The audit is an early warning system. <!-- expect: reframe-pair -->

A pricing page is a handshake that never ends. <!-- expect: metaphor-definition -->

Your inbox is a river that never stops. <!-- expect: metaphor-definition -->

Data is the lifeblood of the modern firm. <!-- expect: metaphor-overreach -->

A rich tapestry of stakeholders shaped the outcome. <!-- expect: ai-lexicon-cluster, metaphor-overreach -->


system copy, flavor and reassurance

THE VAULT AWAITS. <!-- expect: dramatized-system-copy -->

Your journey begins here! <!-- expect: exclamation-point, generic-value-proposition -->

Your account is safe with us, don't worry. <!-- expect: saas-cutesy-copy -->

Don't worry, we've got you. <!-- expect: saas-cutesy-copy -->

The system takes notice. <!-- expect: false-agency-personification, standalone-aphorism -->

Welcome to the next chapter of your financial journey. <!-- expect: generic-value-proposition -->

Here's the thing: nobody reads the footnotes. <!-- expect: announcing-setup-lines -->


setup lines, intensifiers and house words

Worth saying: the contract has a termination clause. <!-- expect: announcing-setup-lines -->

The point is that costs rose. <!-- expect: announcing-setup-lines -->

Let's dive in. <!-- expect: announcing-setup-lines -->

It's important to note that the sample was small. <!-- expect: announcing-setup-lines -->

That is the whole point. <!-- expect: aphoristic-capper, banned-intensifiers -->

That is exactly the problem. <!-- expect: banned-intensifiers -->

Honestly, the numbers surprised me. <!-- expect: banned-intensifiers -->

We leverage a seamless platform to unlock robust growth. <!-- expect: house-banned-vocabulary -->

Let's delve into the landscape of holistic solutions. <!-- expect: house-banned-vocabulary -->

This is a game-changer for the industry. <!-- expect: ai-lexicon-cluster -->

Navigating the evolving landscape requires a multifaceted approach. <!-- expect: ai-lexicon-cluster, house-banned-vocabulary -->

We can ship this in about two weeks, and that's where the real work begins. <!-- expect: soft-cta-closer -->

Feel free to reach out if you'd like to chat. <!-- expect: stock-email-courtesy -->


soft calls to action and chatbot wrappers

Let me know if you have any questions. <!-- expect: stock-email-courtesy -->

I hope this helps! <!-- expect: stock-email-courtesy, exclamation-point -->

Great question! The answer is yes. <!-- expect: chatbot-residue, exclamation-point -->

Would you like me to draft the email as well? <!-- expect: offer-closer -->

In conclusion, the data supports acting now. <!-- expect: summary-recap-ending -->

At the end of the day, it comes down to people. <!-- expect: filler-phrases -->

Studies show that 73% of teams fail at this. <!-- expect: weasel-attribution -->

Many experts agree that this approach is best. <!-- expect: weasel-attribution -->


endings, unsourced claims and grand predictions

A recent study found that firms that invest in data grow faster. <!-- expect: fabricated-specificity -->

This will fundamentally reshape the industry for years to come. <!-- expect: grandiose-prediction -->

Whether you are a CFO, a COO or a CMO, data matters. <!-- expect: correlative-bloat -->

The tool is fast, reliable, and secure. <!-- expect: manufactured-rule-of-three -->

From onboarding to offboarding, from marketing to finance, the platform covers it all. <!-- expect: false-ranges -->

Despite these challenges, the program continues to thrive. <!-- expect: despite-challenges-formula -->

## Unlocking the Power of Your Data <!-- expect: b2b-buzzwords, headline-formulas, house-banned-vocabulary, title-case-headings -->

## 7 Ways to Fix Your Pricing Page <!-- expect: headline-formulas, title-case-headings -->

# The Ultimate Guide to Pricing <!-- expect: headline-formulas -->


padded counts, headings and formulas

Excited to announce our launch! #growth #leadership <!-- expect: exclamation-point -->

I'm humbled to share that I've joined a new team. <!-- expect: false-vulnerability -->

I got fired. And it was the best thing that ever happened to me. <!-- expect: false-vulnerability -->

In a world where every click counts, one team stood alone. <!-- expect: generic-opener -->

As a savvy leader, you already know this. <!-- expect: reader-flattery -->


Posts, openers and tone

Great leaders know that trust is built slowly. <!-- expect: thought-leader-formulas -->

We changed the menu. We changed the hours. We changed the staff. <!-- expect: anaphora-runs -->

No dashboards. No reports. No meetings. <!-- expect: anaphora-runs, dramatic-fragmentation, negative-listing -->

Faster. Cheaper. Better. <!-- expect: dramatic-fragmentation -->

The open questions are the ones above. <!-- expect: hunt-for-referent -->

Dear [Name], thank you for your time. <!-- expect: placeholder-text -->

The report is strong.:contentReference[oaicite:2]{index=2} <!-- expect: citation-markup-artifacts -->

As an AI language model, I cannot verify this. <!-- expect: chatbot-residue -->

Here is the revised version of your email: <!-- expect: chatbot-residue -->


Rhythm, fragments and referents

Several teams reported improvements. <!-- expect: weasel-attribution -->

The result? Faster approvals. <!-- expect: rhetorical-question-setups -->

What does that mean? It means you wait. <!-- expect: rhetorical-question-setups -->


Editing residue and placeholders

Think of it as a thermostat for your pipeline. <!-- expect: patronizing-analogy -->

A shiver ran down her spine. <!-- expect: fiction-sensory-cliches -->

Her heart pounded in her chest. <!-- expect: fiction-sensory-cliches -->

The team ran the pilot for six weeks across three offices and measured every referral that came through the new form, then compared the totals against the prior quarter before presenting them to the board. Most of the lift came from one office. The rest was noise. <!-- expect: closer-without-fact -->

Blind-test additions: lines written after the rules, kept as regression cases

Retention is not a marketing metric. It is a product metric wearing a marketing hat. <!-- expect: glossary-needing-jargon, x-not-y-strict -->

Your calendar is a battlefield where meetings win by default. <!-- expect: metaphor-definition -->

We spent months building it, and the result speaks for itself. <!-- expect: filler-phrases -->

Our approach combines cutting-edge analytics with deep industry expertise to deliver best-in-class results. <!-- expect: ai-lexicon-cluster, b2b-buzzwords -->

Success isn't about working harder. It's about working on the right things. <!-- expect: x-not-y-strict -->

The data does not lie. People do. <!-- expect: false-agency-personification -->

This is more than a rebrand. It's a new chapter for everyone who believes work can feel human. <!-- expect: x-not-y-strict -->

Think of your onboarding flow as a first date: you want to impress without overwhelming. <!-- expect: patronizing-analogy -->

Why does this matter? Because every minute your team spends searching is a minute not spent selling. <!-- expect: rhetorical-question-setups -->

At its core, the issue is one of alignment. <!-- expect: filler-phrases -->

Here's why that matters: trust takes years to build and seconds to lose. <!-- expect: announcing-setup-lines -->

The sprint ended. The backlog did not. <!-- expect: echo-stinger -->

Hiring is slow. Firing is slower. Regret is slowest. <!-- expect: dramatic-fragmentation -->

In today's fast-paced world, businesses need agile solutions that scale. <!-- expect: generic-opener -->

Spoiler: it didn't work. <!-- expect: rhetorical-question-setups -->

And that, in the end, is what leadership really means. <!-- expect: filler-phrases -->

Teams that communicate well tend to outperform teams that do not, which makes communication a strategic imperative. <!-- expect: corporate-jargon -->

I've been thinking a lot about failure lately. Here are three lessons I learned the hard way. <!-- expect: manufactured-rule-of-three -->

Pricing is where strategy goes to be tested. <!-- expect: locative-payoff-closer -->

Great managers don't micromanage; they empower their people to thrive. <!-- expect: house-banned-vocabulary, thought-leader-formulas -->

Every email you send is a tiny contract with your future self. <!-- expect: metaphor-definition -->

The meeting could have been an email. The email could have been nothing. <!-- expect: echo-stinger -->

We built this platform from the ground up to unlock your team's full potential. <!-- expect: generic-value-proposition, house-banned-vocabulary -->

Remote work isn't going away. It's evolving. <!-- expect: x-not-y-strict -->

It turns out the best code is the code you never write. <!-- expect: interpretive-metadiscourse -->

Your brand is a promise you make every single day. <!-- expect: metaphor-definition -->

Silence from a customer is not satisfaction. It is a quiet exit. <!-- expect: x-not-y-strict -->

The numbers tell a compelling story about where the market is headed. <!-- expect: false-agency-personification -->

Let's unpack why onboarding fails and what you can do about it. <!-- expect: announcing-setup-lines -->

You can't automate trust, but you can design for it. <!-- expect: thought-leader-formulas -->

Behind every dashboard is a human being who just wants to go home on time. <!-- expect: thought-leader-formulas -->

So what's the takeaway? Start small, measure everything, and iterate. <!-- expect: rhetorical-question-setups -->

Culture eats strategy for breakfast, and lunch, and dinner. <!-- expect: dying-metaphors-cliches -->

The pilot was a success. The rollout was a lesson. <!-- expect: aphoristic-capper -->

Whether you're a startup or an enterprise, security is a journey, not a destination. <!-- expect: correlative-bloat, x-not-y-contrast -->

The best part? It takes five minutes. <!-- expect: rhetorical-question-setups -->

And just like that, the quarter was over. <!-- expect: dying-metaphors-cliches -->

Innovation lives at the intersection of curiosity and discipline. <!-- expect: dying-metaphors-cliches -->
As a busy parent, you already know mornings are chaos. <!-- expect: reader-flattery -->
Most developers ship features. The few who last write tests first. <!-- expect: thought-leader-formulas -->
Great nurses always listen first. <!-- expect: thought-leader-formulas -->
We help families thrive. <!-- expect: generic-value-proposition -->
