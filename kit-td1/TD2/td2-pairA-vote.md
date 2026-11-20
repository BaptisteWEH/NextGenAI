# TD 2 - Step 1 (Pair A): k-of-n vote, 2-of-3 vs 3-of-5

*Section to merge into `reports/td2.md`. All values come from the **real** TD 1 traces of 2026-10-21 ([`kit-td1/TD1/traces-td1.csv`](../TD1/traces-td1.csv), 105 rows, 100 cells). No new network call, no synthetic data in the table below. The four examples of `atelier-vote.py` are synthetic and are only used to check the contract.*

## 1. Implementation: `Orchestrateur.vote_k_sur_n`

Code: [`kit-td1/skeleton-multi-llm-en.py`](../skeleton-multi-llm-en.py) (the shared skeleton loaded by `atelier-vote.py`). Tests: [`kit-td1/TD2/test_vote_td2.py`](test_vote_td2.py) (edge cases including a 2-2 tie below `k`, no network).

| Rule of the contract | How it is implemented |
|---|---|
| 1. Only executed proposals with a value vote | `verdict == "executed" and value is not None`. The test is `is not None`, **not** truthiness: 0 cents is a real vote (needed for the wrong consensus `[0, 0, 100]`). An error stays in `n` and casts no vote. |
| 2. `n // 2 < k <= n` | `n = len(traces_question)` counts every member, voting or not. Otherwise `ValueError` (this also rejects an empty panel). |
| 3. Duplicate `(provider, model_requested)` | `ValueError`: a duplicate is not a second vote. |
| 4. A value reaches `k` | `{"consensus": True, "value": v, "votes": count, "models": [...]}`, models listed as `provider:model`. |
| 5. Otherwise | `{"consensus": False, "value": None, "votes": largest count, "models": []}`. Never invents a value. |

Since `k > n // 2`, two different values can never both reach `k`: no tie-break is needed. The vote never receives the reference; the comparison is done afterwards by `compare-vote-td2.py`.

Synthetic check (`python3 TD2/atelier-vote.py`, `nature = simulation`): agreement `[100,100,120]` -> consensus 100 (2/3); disagreement `[100,110,120]` -> abstain (max 1); unavailable `[100,None,None]` -> abstain (max 1); wrong consensus `[0,0,100]` -> consensus **0** (2/3), reference 100, so the vote cannot see that it is wrong.

## 2. Method of the comparison

- **Last attempt per model and question**: the CSV is grouped by model, not globally chronological, but attempts of one model are consecutive and ordered; the script keeps the one with the latest `date_utc` (same result as "last CSV row"). Retries matter in 5 cells: `qwen` on C16 (429, 429), C18 (429 then correct), C19 (429 then incorrect), C20 (429, 429) and `20B` on C19 (429 then correct).
- **A model that could not answer** (`not_executed` after HTTP 429, or `sql_invalid`) stays in `n` and casts no vote. Only this execution status is read from the traces; the correctness label is never passed to the vote.
- **2-of-3**: fixed panel of `atelier-vote.py` (`openai/gpt-oss-120b`, `cohere/north-mini-code:free`, `qwen/qwen3.8-27b`), `k = 2`.
- **3-of-5**: the three above plus `openai/gpt-oss-20b` and `dots-studio/dots-3-note-preview:free`, `k = 3`.
- Reproduce, from `kit-td1/`: `python3 TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv` (regenerates [`vote-comparison-td2.csv`](vote-comparison-td2.csv) byte for byte).
- We used our own driver to produce both panels in one pass; the 2-of-3 decisions were cross-checked against `python3 TD2/atelier-vote.py --traces TD1/traces-td1.csv --case Cxx` for the twenty questions (0 mismatch). The table below is a reformatted view of the script output (individual votes added).

## 3. Twenty-question table

| Q | Reference | 2-of-3 | vs ref | 3-of-5 | vs ref | Votes 120B / Cohere / Qwen / 20B / Dots (× = no vote) |
|---|---:|---|---|---|---|---|
| C01 | 792800 | 792800 (3/3) | OK | 792800 (5/5) | OK | 792800 / 792800 / 792800 / 792800 / 792800 |
| C02 | 590320 | 590320 (2/3) | OK | 0 (3/5) | WRONG | 590320 / 0 / 590320 / 0 / 0 |
| C03 | 936350 | 936350 (3/3) | OK | 936350 (5/5) | OK | 936350 / 936350 / 936350 / 936350 / 936350 |
| C04 | 2826250 | 2826250 (3/3) | OK | 2826250 (5/5) | OK | 2826250 / 2826250 / 2826250 / 2826250 / 2826250 |
| C05 | 38480 | 38480 (3/3) | OK | 38480 (5/5) | OK | 38480 / 38480 / 38480 / 38480 / 38480 |
| C06 | 0 | 0 (3/3) | OK | 0 (5/5) | OK | 0 / 0 / 0 / 0 / 0 |
| C07 | 13970 | 13970 (3/3) | OK | 13970 (5/5) | OK | 13970 / 13970 / 13970 / 13970 / 13970 |
| C08 | 605580 | 605580 (2/3) | OK | 605580 (4/5) | OK | 605580 / 1188090 / 605580 / 605580 / 605580 |
| C09 | 487980 | 487980 (2/3) | OK | 487980 (3/5) | OK | 487980 / × / 487980 / 487980 / 0 |
| C10 | 558980 | abstain (max 1) | abstain | abstain (max 2) | abstain | 558980 / × / 119410 / 558980 / 119410 |
| C11 | 446690 | abstain (max 1) | abstain | abstain (max 1) | abstain | 768850 / 0 / 446690 / 322160 / × |
| C12 | 1666490 | 1666490 (3/3) | OK | 1666490 (5/5) | OK | 1666490 / 1666490 / 1666490 / 1666490 / 1666490 |
| C13 | 107740 | 107740 (3/3) | OK | 107740 (5/5) | OK | 107740 / 107740 / 107740 / 107740 / 107740 |
| C14 | 0 | 0 (3/3) | OK | 0 (5/5) | OK | 0 / 0 / 0 / 0 / 0 |
| C15 | 168680 | abstain (max 1) | abstain | abstain (max 2) | abstain | 168680 / 314020 / 0 / 168680 / 138920 |
| C16 | 376740 | 376740 (2/3) | OK | 376740 (4/5) | OK | 376740 / 376740 / × / 376740 / 376740 |
| C17 | 258180 | abstain (max 1) | abstain | 258180 (3/5) | OK | 258180 / 197080 / 248490 / 258180 / 258180 |
| C18 | 62480 | 62480 (3/3) | OK | 62480 (5/5) | OK | 62480 / 62480 / 62480 / 62480 / 62480 |
| C19 | 1990 | abstain (max 1) | abstain | abstain (max 2) | abstain | 1990 / 0 / 83580 / 1990 / × |
| C20 | 1106090 | 1106090 (2/3) | OK | 1106090 (4/5) | OK | 1106090 / 1106090 / × / 1106090 / 1106090 |

| | OK | WRONG | Abstain |
|---|---:|---:|---:|
| 2-of-3 (`k=2`) | 15 | **0** | 5 (C10, C11, C15, C17, C19) |
| 3-of-5 (`k=3`) | 15 | **1** (C02) | 4 (C10, C11, C15, C19) |

| Quorum | Coverage (decided) | Precision (correct when decided) |
|---|---:|---:|
| 2-of-3 | 15/20 = 75 % | 15/15 = 100 % |
| 3-of-5 | 16/20 = 80 % | 15/16 = 93.75 % |

Ten questions are unanimous in both panels (C01, C03, C04, C05, C06, C07, C12, C13, C14, C18). On C18, Qwen is correct only on its second attempt, after an HTTP 429.

## 4. Commentary on every difference between 2-of-3 and 3-of-5

**Decision changes (2 questions).**

- **C02, OK becomes WRONG.** 2-of-3 returns the reference 590320 (120B and Qwen, 2/3; Cohere's 0 is outvoted). 3-of-5 returns **0 with 3 votes** (Cohere, 20B, Dots; all three `verdict = incorrect` in the traces) against 2 votes for 590320 (120B, Qwen; both `correct`): the two models added to the panel both returned the same wrong value as Cohere and flipped the majority. A bigger quorum is therefore not safer by itself. The three SQL queries are wrong in three different ways (see Pair B's analysis), but all select no customer, so the empty sum becomes 0.
- **C17, abstain becomes OK.** With 2-of-3 the three models give three different values (258180, 197080, 248490), so no value reaches 2. With 3-of-5, 20B and Dots add two votes for 258180 (the reference), which reaches `k = 3` with 120B. Cohere (197080) and Qwen (248490) are wrong (`incorrect`) and outvoted; 120B, 20B and Dots are `correct`.

**Same decision, different margin (4 questions).**

- **C08**: 605580 goes from 2/3 to 4/5; Cohere's 1188090 stays isolated. 20B and Dots (both correct) widen the margin.
- **C09**: 487980 goes from 2/3 to 3/5. Cohere has an invalid SQL statement (`syntax_error near "AS"`), so it stays in `n` with no vote; Dots votes 0 (wrong). The consensus is exactly at the threshold: one more failure would turn it into an abstention.
- **C16** and **C20**: Qwen got HTTP 429 on both attempts (no vote). 2-of-3 holds at 2/3 with no margin (120B + Cohere); 3-of-5 holds at 4/5 because 20B and Dots add two correct votes.

**Abstain in both (max votes shifts from 1 to 2).**

- **C10**: 2-of-3 has 558980 (120B), 119410 (Qwen), Cohere invalid. 3-of-5 gets 2 votes for 558980 (120B, 20B) and 2 votes for the wrong 119410 (Qwen, Dots): a 2-2 tie below `k = 3`, so it abstains. The quorum can only signal the disagreement; it cannot say which side is right (here the right value and the wrong one have the same support).
- **C15**: the reference 168680 gets 2 votes (120B, 20B), the others disagree (314020, 0, 138920), so no value reaches 3.
- **C19**: 1990 gets 2 votes (120B, and 20B on retry after a 429); Cohere 0, Qwen 83580 (after a 429 retry) and Dots invalid SQL (no vote).
- **C11** no consensus in either panel. The five answers are 768850 / 0 / 446690 / 322160 and Dots invalid (no vote). The reference 446690 gets only one vote (Qwen), so the maximum remains 1 in both configurations.

## 5. What to conclude (and not to conclude)

- Both quorums agree with the reference whenever they decide **except C02 for 3-of-5**; the 2-of-3 panel never returned a wrong value on this batch but abstained on 5 questions out of 20.
- Adding voters raises the number of decided questions (C17) but not the independence: `openai/gpt-oss-120b` and `openai/gpt-oss-20b` are the **same family**, so they are not two independent votes, but that is not what causes C02 (120B is right and 20B is wrong there). On C02, the three models do not make the same mistake: their queries fail in three different ways, but all of them select no customer, and the empty sum becomes 0. Agreement on a value does not mean agreement on a reasoning.
- Abstentions are not equivalent to errors: C10, C11, C15 and C19 are exactly the questions where a quorum signals "no decision" and where TD 3 will need a deterministic check.
- **Recommendation**: build the panel from distinct model families, and treat the quorum as a signal of agreement, not as a check ("the quorum exposes disagreement, it does not create truth", lecture 2). On age and date questions, a deterministic check (reference query or Pair B's canary) must follow the vote.
- Twenty questions on one batch support a hypothesis specific to this batch, not a general error rate nor a guarantee on quorums.
