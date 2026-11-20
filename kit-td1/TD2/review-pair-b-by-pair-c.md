# Review of Pair B's Step 2 by Pair C

Reviewed: `pair-b-td2.md`, `pair_b_wrong_consensus.py`, `delta-c02-td2.csv` and `delta-c10-td2.csv`, as they are on the `Pair_B` branch (commit `6721f75`).

## How we reviewed

We did not only read the report. We ran `python3 pair_b_wrong_consensus.py` from `kit-td1/TD2/` and compared every number in the report with the script output, with `TD1/traces-td1.csv`, `TD1/reference-td1.csv` and the questions in `TD1/questions-td1.json`. We also checked the cited lecture slides in `lectures/cm2-en.html`.

## What is solid

Most of the work holds up, and we would keep its structure as it is.

- The scan is complete: C02 and C10 are the only questions of the batch where two models or more return the same wrong value.
- The quorum verdicts are right: on C02, 2-of-3 returns the reference (590320) and 3-of-5 returns the wrong 0; on C10, both abstain.
- The C02 diagnosis is the right one. The three faulty queries are wrong in three different ways, but each selects no customer and `COALESCE` turns the empty sum into 0. This point matters for the whole group (see change 6).
- The delta tables add up exactly: six customers for 590320 on C02; 119410 + 439570 = 558980 on C10.
- The bitmask canary is a good idea: one run, and the sum tells which boundary is wrong.

The changes below are listed from the most to the least important.

## Changes we ask for

### 1. The canary is calibrated for the wrong date on C08

The canary table is built around 25 September 2026: K1 and K2 must be included, K3 and K4 excluded, so the expected sum is 300. That is right for C02 and C10 (every canary order is dated 2026-09-25).

C08 asks about the reference date **2026-09-24**. On that date the right customers are K2 (born 2000-09-26, aged 25) and K3 (born 2000-09-25, still 25 until the next day). The correct C08 query therefore returns **600**, which the script labels "off-by-one birthday boundary, REJECT". The north-mini-code query does return 1500 and is wrong, but the check that catches it is calibrated for another question.

What to change:

- either remove the C08 line from the canary section, or build a second canary for 2026-09-24 that expects 600;
- state in the report that the canary has to be rebuilt for each reference date, which is also a cost to mention in TD 3.

### 2. The lecture citation points to slides that do not exist

Section 5 cites "Lecture 2, Slides 22–23 & 26". Lecture 2 has 21 slides. The ideas the report relies on are on:

- slide 8, "The quorum exposes disagreement, it does not create truth";
- slide 9, the four safeguards, including the deterministic check;
- slide 11, the judge model and its limits (why calling a stronger model is not a check).

Suggested wording: *"(Lecture 2, slides 8, 9 and 11)"*.

### 3. The synthetic DEMO-VOTE case carries the names of real models

In the script output, the `[0, 0, 100]` example is printed as a vote of `groq:openai/gpt-oss-120b` and `openrouter:cohere/north-mini-code:free`. These values are invented teaching material, and the assignment asks us never to present them as model outputs. A reader of the output could take them for real answers.

What to change in `pair_b_wrong_consensus.py`: label the three proposals `synthetic:P1`, `synthetic:P2`, `synthetic:P3`, and add one line in section 4 of the report saying they are constructed and not counted with the batch results.

### 4. The consequence for the choice of panel is missing

The assignment asks to "draw the consequence for the choice of panel and of checking". The report shows the facts but does not state the conclusion. Suggested paragraph, to add after section 3:

> **Consequence for the panel.** On C02, the fixed 2-of-3 panel is right only because the three models that return 0 are not all in it. Widening it to 3-of-5 adds gpt-oss-20b and dots, which make the same mistake, and the wrong value wins. Adding voters also adds their errors, so a larger k is not safer by itself. On C10 the 2–2 tie shows that a quorum can only abstain; it cannot tell which side is right. For age questions, the vote has to be followed by an independent check, not replaced by a bigger panel.

### 5. The canary is presented as a guarantee, its limits are not written

The assignment says that a different panel or an escalation is "a candidate check, not a guarantee", and the same holds for the canary. Suggested list, at the end of section 5:

> **Limits.** The canary only tests the age window around one date, with four boundary customers. A query with a wrong join, a wrong amount, a wrong period or duplicated rows can still return the expected sum. It was designed after seeing the errors of this batch, on two question families only. It needs one canary table per question type and per reference date (see C08), written and checked by a person. For a customer figure or a payout, the reference query of the family remains the check that decides.

### 6. Keep one vote for the whole group, and align with Pair A

The script reimplements the vote (`run_k_of_n`) instead of calling `Orchestrateur.vote_k_sur_n`, which is the Step 1 deliverable. Both follow the same contract and give the same verdicts on C02 and C10 (we checked), so nothing is wrong today. But a grader cannot know that two implementations agree. Two options:

- load `vote_k_sur_n` from `kit-td1/skeleton-multi-llm-en.py` once Pair A's vote is merged, keeping the local function only as a fallback;
- or keep the local function and write in the report that it follows the same contract and was checked against Pair A's table of twenty decisions.

Linked to this: Pair A's section currently explains C02 as "the same misreading of 'exactly 25 years old'" by the three models. Pair B's diagnosis (three different errors, one shared default value) is the correct one, and the two sections will sit in the same `reports/td2.md`. Pair B should tell Pair A so that only one explanation remains.

## Minor points

- **C10 is not a wrong consensus in the sense of the assignment.** No declared quorum accepts 119410; both abstain. The report says so in its table, but the section titles put C02 and C10 on the same level. One sentence would help: *"Only C02 is a wrong consensus, and only for the 3-of-5 quorum. C10 is a shared wrong value that both quorums refuse."*
- **Give the source of DEMO-SQL-C11.** "Historical pilot" is not enough for the reader: say who supplied it (instructor case) and that it is kept apart from the batch counts.
- **The Files table links to the report itself.** The `pair-b-td2.md` line can be removed.

## Summary

| # | Change | Why | Effort |
|---|---|---|---|
| 1 | Canary for C08 (date 2026-09-24, expected 600) | a check calibrated for another question | small |
| 2 | Lecture citation: slides 8, 9 and 11 | slides 22–26 do not exist | one line |
| 3 | `synthetic:P1–P3` labels in DEMO-VOTE | invented values shown as real model outputs | small |
| 4 | Paragraph "consequence for the panel" | explicitly asked by the assignment | one paragraph |
| 5 | Limits of the canary | "a candidate check, not a guarantee" | one paragraph |
| 6 | One vote for the group, one C02 explanation | consistency of `reports/td2.md` | small, with Pair A |

With changes 1 to 5, Step 2 covers everything the assignment asks for. Change 6 is about the group report as a whole rather than Pair B's work alone.
