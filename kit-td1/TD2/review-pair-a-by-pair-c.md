# Review of Pair A's Step 1 by Pair C

Reviewed: `td2-pairA-vote.md`, `Orchestrateur.vote_k_sur_n` in `skeleton-multi-llm-en.py`, `test_vote_td2.py`, `compare-vote-td2.py` and `vote-comparison-td2.csv`, as they are on the `Pair_A` branch (commit `9dc31ec`).

## How we reviewed

We did not only read the report: we checked every claim against the data.

- We ran `python test_vote_td2.py`: **all edge-case tests pass**.
- We ran `compare-vote-td2.py` on `TD1/traces-td1.csv` and `TD1/reference-td1.csv`. The generated CSV is **byte-for-byte identical** to the submitted `vote-comparison-td2.csv`.
- We confirmed the input: 105 rows, 100 distinct (question, model) cells, all `nature = real`.
- We recomputed the summary: 2-of-3 = 15 OK / 0 WRONG / 5 abstain; 3-of-5 = 15 OK / 1 WRONG (C02) / 4 abstain. The only decision changes are C02 and C17.

## What is solid

The work is rigorous, well documented and reproducible. We would keep its structure as it is.

- **The vote follows the contract exactly.** The five rules are implemented, explained in a clear table and covered by tests. The `is not None` check (so that 0 cents counts as a real vote) is a subtle edge case, and it is handled correctly.
- **Defensive design.** Invalid `k`, empty panels and duplicate members raise a `ValueError` instead of failing silently. The function accepts both objects and dicts.
- **The vote never sees the reference.** The decision is made first and compared afterwards. This separation is the core of the exercise, and it is respected.
- **Data traceability.** Retries (HTTP 429) are listed cell by cell, the "last attempt" rule is stated, and synthetic examples are clearly kept apart from real results.
- **Every difference is explained.** Decision changes, margin changes and abstentions are each analysed with the individual votes. The point on C09 ("exactly at the threshold") shows real critical thinking.
- **The conclusions are careful.** The report does not turn 20 questions into a general error rate.

The changes below are listed from the most to the least important.

## Changes we ask for

### 1. The comparison script no longer runs (reproducibility)

Since the kit was reorganised into `TD1/`, `TD2/` and `TD3/` folders, `compare-vote-td2.py` looks for `traces-td1.csv` and `reference-td1.csv` in `TD2/` and stops with a `FileNotFoundError`. The reproduction command in section 2 therefore fails for any reader.

**Fix (two lines):** read the files from `HERE.parent / "TD1" / ...`. We checked that the output is then identical to the submitted CSV.

### 2. The paths in the report are outdated

Section 1 and the header still point to `kit-td1/skeleton-multi-llm-en.py`, `kit-td1/test_vote_td2.py` and `kit-td1/traces-td1.csv`. They should be `kit-td1/TD2/...` for the code and `kit-td1/TD1/traces-td1.csv` for the data.

### 3. The C02 explanation does not match Pair B's diagnosis

Section 5 says that the three models that return 0 on C02 "share the same misreading of 'exactly 25 years old'". Pair B's Step 2 analysis, which we reviewed and re-checked on the traces, shows the opposite: the three SQL queries are wrong in **three different ways** (wrong age interval, reversed birthday bounds, invalid date string). Each selects no customer, and `COALESCE` turns the empty sum into 0.

The key insight is therefore that **different errors can converge on the same default value**. This is a stronger argument against trusting a quorum. Both sections will sit in the same `reports/td2.md`, so we suggest keeping one explanation:

> *On C02, the three models do not make the same mistake: their queries fail in three different ways, but all of them select no customer, and the empty sum becomes 0. Agreement on a value does not mean agreement on a reasoning.*

### 4. State the consequence for the panel more explicitly

The same-family point (120B and 20B) is a valuable observation, but the report stops before the recommendation. We suggest one actionable sentence:

> *Recommendation: build the panel from distinct model families, and treat the quorum as a signal of agreement, not as a check. On age and date questions, a deterministic check (reference query or canary) must follow the vote.*

A nuance for accuracy: on C02 the two OpenAI models actually **disagree** (120B is right, 20B is wrong). The family correlation is a real risk, but it is not what causes C02.

### 5. Add the coverage / precision trade-off

The figures are already there. One line would make the trade-off measurable:

| Quorum | Coverage (decided) | Precision (correct when decided) |
|---|---:|---:|
| 2-of-3 | 15/20 = 75 % | 15/15 = 100 % |
| 3-of-5 | 16/20 = 80 % | 15/16 = 93.75 % |

A bigger panel decides more often but is not more reliable. This is the main conclusion of Step 1, summed up in one number.

## Minor points

- **Missing test for a tie.** The C10 situation (2 votes against 2, `k = 3`) is not in `test_vote_td2.py`. Suggested: `vote(P([1, 1, 2, 2, None]), 3)` must abstain with `votes = 2`.
- **Use of the `verdict` column.** `compare-vote-td2.py` decides whether a model voted from `verdict in {"correct", "incorrect"}`, a label derived from the reference. Only the fact that the query ran is used, not the correctness, so the result is right. But reading an execution status (`executed` / `sql_invalid` / `not_executed`) would make the "vote never sees the reference" guarantee easier to check.
- **Lecture link.** One reference to lecture 2 (slide 8, "the quorum exposes disagreement, it does not create truth") would anchor section 5 in the course.

## Summary

| # | Change | Why | Effort |
|---|---|---|---|
| 1 | Fix the CSV paths in `compare-vote-td2.py` | the reproduction command fails | two lines |
| 2 | Update the paths in the report | point to the new folders | small |
| 3 | One C02 explanation, aligned with Pair B | consistency of `reports/td2.md` | one paragraph |
| 4 | Explicit recommendation for the panel | the consequence is asked for, not only the facts | one sentence |
| 5 | Coverage / precision table | measures the trade-off | small table |

Overall, this is a **high-quality, reproducible and well-argued** Step 1. Changes 1 and 2 are needed for reproducibility. Changes 3 to 5 make the analysis sharper and consistent with the rest of the group report.
