# Review of Pair A work by Pair B (TD2 step 1)

We reviewed the commit "pair a" (9dc31ec) on the Pair_A branch. We only used the files on that branch and the TD1 traces (TD1/traces-td1.csv and TD1/reference-td1.csv). We read the code, ran the tests and the scripts, and compared everything with the step 1 instructions.

## Overall

The vote method is correct and the 20-question table is right. We regenerated it ourselves after fixing the paths and got the exact same CSV. Totals are also correct: 2-of-3 gives 15 OK, 0 wrong, 5 abstain, and 3-of-5 gives 15 OK, 1 wrong (C02), 4 abstain.

The main issue is that the scripts don't run from the repo right now, so someone else can't reproduce the results. It's mostly a path problem, probably because of the folder reorganisation into TD1/TD2/TD3.

## Problem 1: atelier-vote.py doesn't use your method

atelier-vote.py (line 26) loads kit-td1/skeleton-multi-llm-en.py, the one in the parent folder. But you completed the method in a copy in TD2/. The original file still has the NotImplementedError at line 628, so when we run:

    python3 TD2/atelier-vote.py
    python3 TD2/atelier-vote.py --traces TD1/traces-td1.csv --case C02

both just print "vote_k_sur_n: to implement in TD 2". These are the two commands asked in the statement, so it's important.

Also the TD2 copy seems to come from the old skeleton (before the reorg), so its RESOURCES paths point to files that are not in TD2/. And TD2/sandbox_sqlite.py is just a duplicate of the one in kit-td1/.

Fix: put the vote_k_sur_n body (lines 627 to 667) in kit-td1/skeleton-multi-llm-en.py, delete the two copies in TD2/, and make compare-vote-td2.py and test_vote_td2.py load the skeleton from the parent folder like atelier-vote.py does. We tried it on a copy and the 4 synthetic examples and C02 give exactly what you wrote in the report.

## Problem 2: compare-vote-td2.py crashes

Lines 56 and 57 open traces-td1.csv and reference-td1.csv in TD2/, but they are in TD1/. So we get a FileNotFoundError. Just use HERE.parent / "TD1" / ... and it works.

## The vote method

We checked the 5 rules of the contract and they are all respected:

- only executed proposals with a value vote, errors stay in n
- n // 2 < k <= n otherwise ValueError (also refuses n = 0)
- duplicate provider/model gives ValueError
- consensus returns value, votes and models
- no consensus returns value None, the max votes and an empty list

Good point: you used "is not None" and not a truth test, so 0 cents counts as a real vote. Without that C02 would be wrong. Your comment that two values can't both reach k when k > n // 2 is also a nice argument for the oral.

Small things, not blocking: k is not checked to be an int (k = 2.0 or k = True pass), and "5" and 5 would count as different values. It's fine here since the scripts convert to int.

## The comparison script

The last attempt rule is ok and handles the 5 retry rows (qwen on C16, C18, C19, C20 and 20B on C19). You wrote your own script instead of rerunning atelier-vote.py for the 20 questions, which is fine since the decisions are the same and the vote is still done by vote_k_sur_n, but maybe say it in the report.

The table in the report is not exactly what the script prints (different columns), so either change the script or say you reformatted it. Also the code is a bit hard to read with the one-line statements and the lambdas, which could be annoying during the cross-review.

## The report (td2-pairA-vote.md)

All the values and verdicts we checked are correct. Some things to change:

- The paths are old: it says kit-td1/skeleton-multi-llm-en.py, kit-td1/test_vote_td2.py and kit-td1/traces-td1.csv. And the skeleton in kit-td1/ is the one that is not implemented.
- The reproduce command on line 27 crashes (problem 2).
- C10, line 74: you say "with k = 2 the wrong value would have been as eligible". But with n = 5, k = 2 is not allowed by the contract (it needs k >= 3), so this sentence is a bit confusing.
- Line 82 says the 3 models on C02 "share the same misreading", but line 63 says the queries are different. They actually make 3 different mistakes (cohere has two conditions that can never be true together, 20B takes customers aged 0, dots builds a date strftime can't read). They only have in common that they select no row, so COALESCE turns it into 0.
- For C02 and C17 you give the values but not the verdicts from the traces, and the statement asks for both.
- Maybe add one line about the 10 unanimous questions (3/3 to 5/5) and C18, where qwen is only correct after a 429.
- The section still needs to be merged into reports/td2.md.

## What to do (around 15 min)

1. Move the method into kit-td1/skeleton-multi-llm-en.py and delete the TD2 copies.
2. Fix the paths in compare-vote-td2.py and test_vote_td2.py.
3. Rerun from kit-td1/ and check with git diff that the CSV didn't change:

       python3 TD2/test_vote_td2.py
       python3 TD2/atelier-vote.py
       python3 TD2/atelier-vote.py --traces TD1/traces-td1.csv --case C02
       python3 TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv

4. Fix the report (paths, C10, line 82, verdicts for C02 and C17).
5. Merge it into reports/td2.md.

Really good job overall, the logic is very solid, it's mainly about making it run from the repo.
