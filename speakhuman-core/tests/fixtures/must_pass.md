---
title: "Why the postcard took ten weeks"
description: "A regional printer waited on one approval step for six of ten weeks, and the fix cost nothing."
---

<!-- Plain, specific human writing. run_tests.py asserts this whole file produces
zero errors and zero warnings (info-level density figures are allowed). Each
section covers a different destination: article prose, email, commit and PR
text, chat replies, instructions, UI strings and edge cases where a stricter
rule would misfire. Write your own approved samples into your profile fixtures. -->

### Article prose

A regional printer told us a holiday postcard would take ten weeks. We assumed the printing was slow. It was not: the presses ran for two days, and the other 68 days were spent waiting for approvals.

I pulled the ticket history for the last 40 jobs and timed each stage. Intake took a day. Design took five. Legal review took a median of 31 days, and in nine cases it took longer than the whole production run. Nobody had set a deadline for legal, so nothing pushed the work forward.

We gave review a clock. Any piece that sat for more than five working days went to the requester's manager with the ticket number, and the manager decided whether to wait or reassign it. Over the next quarter the median review time fell from 31 days to 6, and the printer's ten weeks became three.

That is a process finding, and a small one. It says nothing about whether the postcard was a good idea, and we did not measure response rates until the following year, when the number was 1.8 percent against a 1.1 percent baseline.

The reviewers pushed back at first. Two of them told me the clock would make them rush, and a third said the real problem was staffing. They were partly right. We added one reviewer in March, and the median stayed at six days with the extra person, which suggests the clock was doing most of the work.

I should say what I got wrong. I assumed the delay was legal's fault, and for the first month I wrote the report that way. When I read the tickets again, half of the waiting happened before legal ever received the piece, because requesters attached the wrong file version and the ticket bounced back.

### Email

Hi Dana,

Thanks for sending the draft. I read it twice and have three changes: move the budget table above the timeline, cut the second paragraph on vendors, and add the March 3 review date to the first page.

I can turn comments around by Thursday if you send the file by end of day Tuesday. If Wednesday is easier for the board, tell me and I will plan around it.

Best,
Jordan

### Commit and pull request text

Cap review at five working days and escalate to the manager. Reviews that sit longer are reassigned. The escalation list lives in config/review.yml, and the job runs nightly at 02:00.

Fix the duplicate ticket created when a requester re-attaches a file. The intake form now checks the filename and version before it creates a new ticket, and the old tickets were merged by hand.

### Chat replies

Use the second option. It keeps the existing review path and adds the clock, so you do not have to retrain anyone.

Yes, the export works for both formats. CSV opens in Excel without changes; JSON needs the column names set in the config first.

The total is $48,000 over two years, which is $2,000 a month. The vendor quote said $44,000, and the difference is the setup fee.

### Instructions

1. Open Settings and choose Review rules.
2. Set the limit to five working days.
3. Pick the manager list and save.

### UI strings and labels

Review limit

Saved. The new limit applies to tickets opened from now on.

This ticket has been waiting 6 days. Assign it or ask the manager to decide.

Delete this ticket? Its comments are deleted with it.

### Edge cases where stricter rules misfire

<!-- slop-ok: linkedin-broetry -->
The branch is open Monday, Wednesday and Friday.

Note: figures are as of Q2 2026.

The Tier 1 leverage ratio stayed above 9 percent through the cycle.

It costs exactly $250 a year to keep.

The company is licensed in Texas, not Delaware, so the Texas filing applies.

These were estimates reported by the vendor, not an audit of individual accounts.

Customers can unlock the card from the app after a fraud alert.

What exactly changed in the contract? The renewal term moved from one year to three.

Ready? Let's go. Open the first file and start at line 12.

### Short lines that carry a fact

The pilot ran six weeks. The Denver office produced 22 of the 31 referrals.

We kept the old form for one office as a control. It converted at 1.1 percent.

The second vendor missed the date by nine days. We paid the late fee ourselves.

### Blind-test additions: plain writing

We switched the nightly export to run at 2 a.m. after the 9 p.m. run kept colliding with the billing job. The collision cost us about forty minutes of API time each night, and the 2 a.m. window has been clean for three weeks.

The invoice was wrong by $312 because the discount applied twice. Finance reissued it on Tuesday and we added a check so a discount can only apply once per order.

I disagree with the second recommendation. The vendor's own uptime page shows two outages longer than an hour since June, and the contract has no credit for either.

Maria asked whether we should migrate before the audit or after. After: the migration touches the ledger tables, and the auditors want the old structure on file until they sign off.

The team is small, six people, and two of them are part time. That limits what we can promise for Q4.

Open the project, select the Reports tab, and export the March file as CSV.

The store sells 14 flavors of ice cream and only one of them, pistachio, has ever been returned.

I was wrong about the cause. The timeout was not in the client at all; the proxy was dropping connections after 30 seconds.

Thanks for the quick turnaround. I will send the signed copy tomorrow morning.

The bridge reopens in November, but the north lane stays closed through January.

The warehouse moved to a four-day week in May, and shipping errors dropped from 3.1 percent to 1.9 percent by August.

Priya's team found the bug in the retry logic: failed jobs were requeued without a backoff, so one bad record could fill the queue in minutes.

Two of the five vendors did not respond to the RFP, so the comparison below covers three.

I would not sign this contract as written. Clause 9 lets them raise the fee at any time, and clause 14 makes us pay for the audit.

After the merger the support queue doubled, from about 400 to 810 tickets a week, and the median reply time went from 5 hours to 19.

The recipe needs 300 grams of flour, two eggs and a pinch of salt. Rest the dough for twenty minutes before rolling it out.

We lost the Denver account in March. The buyer left, and her replacement wanted a vendor she already knew.

The school board meets on the second Tuesday of each month at 7 p.m. in the library.

My first draft claimed the lift came from the new headline. When I split the traffic by device, nearly all of it came from mobile.

The patch is small: it adds a null check in parse_header and a test that feeds it an empty file.

Please send the revised budget by Friday, and copy Marcus so he can update the forecast.

As a seasoned developer, I keep functions short and name them for what they return.

Most days the clinic sees 40 patients. The busiest day this year saw 61.

The Great Lakes always freeze by February in a cold year.

It helps the seedlings grow two inches a week under the lamp.
