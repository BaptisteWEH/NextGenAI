# TD 2 session report

**Class:** DIA 3 · **Sub-group:** DIA3-3 · **Session:** 18 November 2026 · **Pack:** 2026-10-14-students-1

| Pair | Members | Step | Detailed section |
|---|---|---|---|
| A | Leo Garcia (Inès), Maxence Milleker | Step 1: k-of-n vote, twenty decisions | [td2-pairA-vote.md](../kit-td1/TD2/td2-pairA-vote.md) |
| B | Timothée Barselo, Baptiste Wehry | Step 2: wrong consensus, SQL diagnosis, canary check | [pair-b-td2.md](../kit-td1/TD2/pair-b-td2.md) |
| C | Nils Demougeot, Edgar Merceron, Sacha Sommier | Step 3: routing rule and simulator | [pair-c-td2.md](../kit-td1/TD2/pair-c-td2.md), [routing-rule-td2.md](../kit-td1/TD2/routing-rule-td2.md) |

Each pair's work was cross-reviewed by the two other pairs; the reviews are in
[`kit-td1/TD2/`](../kit-td1/TD2/) (`review-*.md`) and their requests were applied.

**In short.** The vote is implemented in the shared skeleton and follows the five rules of the
contract. On the twenty TD 1 questions, the fixed 2-of-3 panel decides 15 (all correct) and abstains
on 5. The 3-of-5 quorum decides 16 but returns one **wrong consensus: C02**, where three models
return 0 against a reference of 590320 cents. Their three queries are wrong in three different ways,
but all select no customer, so `COALESCE` turns the empty sum into 0. The routing rule sends each
family to the cheapest route that was right on all its TD 1 cells, and adds a quorum or a
deterministic check according to the cost of an error.

**Nature of the data.** All the vote decisions, the wrong consensus C02 and the shared wrong value on
C10 come from the **real** TD 1 traces of 2026-10-21 ([traces-td1.csv](../kit-td1/TD1/traces-td1.csv)).
No new network call was made in TD 2. Three things are **not** measured on our batch and are labelled as such:
the four synthetic examples of `atelier-vote.py` and the `DEMO-VOTE` toy table (`simulation`), the
instructor-supplied historical case `DEMO-SQL-C11` (September 2026 pilot), and every simulator run
(fictitious resources and availabilities; only the 0.045 USD paid route comes from portfolio prices).

## Step 1 - The k-of-n vote (Pair A)

**Done.** `Orchestrateur.vote_k_sur_n` is completed in
[skeleton-multi-llm-en.py](../kit-td1/skeleton-multi-llm-en.py), the shared file that
`atelier-vote.py` loads. Only executed proposals with a value vote, using `is not None` so that 0 cents
counts. A failed member stays in `n`. A `k` that is not a strict majority, or a duplicate
`(provider, model)` pair, raises `ValueError`. Without a value at `k`, the method abstains and never
invents a value. Edge cases are tested in [test_vote_td2.py](../kit-td1/TD2/test_vote_td2.py):
agreement, disagreement, unavailable members, duplicate routes, 0 as a real vote, and a 2-2 tie below `k`.

**Declared panels.** Fixed 2-of-3 panel of the kit (`groq:openai/gpt-oss-120b`,
`openrouter:cohere/north-mini-code:free`, `groq:qwen/qwen3.8-27b`, `k = 2`). For comparison, 3-of-5
with all five TD 1 models (`k = 3`). Last attempt per model and question. Driver:
[compare-vote-td2.py](../kit-td1/TD2/compare-vote-td2.py). Table:
[vote-comparison-td2.csv](../kit-td1/TD2/vote-comparison-td2.csv). The 2-of-3 decisions match
`atelier-vote.py --case Cxx` on all twenty questions.

| Quorum | OK | Wrong | Abstain | Coverage | Precision when decided |
|---|---:|---:|---:|---:|---:|
| 2-of-3 | 15 | 0 | 5 (C10, C11, C15, C17, C19) | 75 % | 100 % |
| 3-of-5 | 15 | 1 (C02) | 4 (C10, C11, C15, C19) | 80 % | 93.75 % |

Two decisions change between the panels: C02 (OK → wrong) and C17 (abstain → OK). The detail of each
difference is in [td2-pairA-vote.md](../kit-td1/TD2/td2-pairA-vote.md#4-commentary-on-every-difference-between-2-of-3-and-3-of-5).

## Step 2 - The wrong consensus (Pair B)

**Case `C02` (real batch).** "Revenue of customers exactly 25 years old on 2026-09-25". The
independent reference is **590320** cents ([reference-td1.csv](../kit-td1/TD1/reference-td1.csv)).
`gpt-oss-20b`, `north-mini-code:free` and `dots-3-note-preview:free` all return **0**
([traces-td1.csv](../kit-td1/TD1/traces-td1.csv) lines 23, 44 and 88, `verdict = incorrect`).

| Quorum | Result on C02 |
|---|---|
| Fixed 2-of-3 (`k=2`, `n=3`) | 590320, 2/3 votes (120B, Qwen): the wrong 0 of Cohere is outvoted |
| 3-of-5 (`k=3`, `n=5`) | **0, 3/5 votes: wrong consensus** |

**Cause in the SQL.** There are three different faults: `gpt-oss-20b` tests customers aged 0,
`north-mini-code` inverts both birthday bounds (an empty set), and `dots` builds a 2-digit year date
that `strftime` turns into `NULL`. Each one selects no customer. A delta query on `boutique.sqlite`
reconciles the full 590320-cent gap ([delta-c02-td2.csv](../kit-td1/TD2/delta-c02-td2.csv)).

**Second case, refused by the vote.** On `C10`, `qwen3.8-27b` and `dots` both return 119410 against
558980 ([delta-c10-td2.csv](../kit-td1/TD2/delta-c10-td2.csv)). Both quorums abstain (2-2 tie in
3-of-5), so the vote does not deliver the wrong value, but it cannot say which side is right either.

**Check that detects it.** This is a binary-bitmask **canary**: the model's SQL runs on four synthetic
customers built around the reference date, and only the exact age window returns 300 cents. It
rejects the three C02 queries (0) and the two C10 queries (100). It is a targeted check: it must be
rebuilt for each question date and does not catch join or amount errors. For a customer figure or a
payout, the validated reference query of the family decides. Code:
[pair_b_wrong_consensus.py](../kit-td1/TD2/pair_b_wrong_consensus.py). `DEMO-VOTE` and `DEMO-SQL-C11`
are explained separately in [pair-b-td2.md §4](../kit-td1/TD2/pair-b-td2.md) and are not counted with the batch.

**Consequence for the panel.** Adding voters adds their errors. A quorum exposes disagreement; it
does not establish truth. The panel should use distinct makers (the two gpt-oss models are not two
independent votes), and on age questions the vote must be followed by a deterministic check.

## Step 3 - The routing rule (Pair C)

**Rule:** [routing-rule-td2.md](../kit-td1/TD2/routing-rule-td2.md). Each line cites its TD 1 cells,
recomputed by [pair_c_family_rates.py](../kit-td1/TD2/pair_c_family_rates.py)
([family-rates-td2.csv](../kit-td1/TD2/family-rates-td2.csv)).

| Family | First route | Dashboard | Customer | Payout |
|---|---|---|---|---|
| F1 period | gpt-oss-20b (6/6) | none | 2-of-3 | reference + review |
| F3 product list | gpt-oss-20b (4/4) | none | 2-of-3 | reference + review |
| F2 age at a date | qwen3.8-27b (only 4/4) | 2-of-3 | 2-of-3 + reference | reference + review |
| F2b age at the order | gpt-oss-20b (1/1) | reference | reference | reference + review |
| Combined | gpt-oss-20b (5/5) | 2-of-3, reference if it abstains | reference | reference + review |

The fallback order when a route is unavailable is: next route correct on the family, then wait for
the refill if the request can wait, then abstain. Untested senior routes are only used with a
reference check and never for a payout.

**Simulator.** Before: the kit file on its seven scenarios
([simulator-before-td2.jsonl](../kit-td1/TD2/simulator-before-td2.jsonl)). After: `RESOURCES` and
`choose` are adapted to our rule, with each reason carrying its TD 1 cells and a versioned policy
`pair-c-v1` (retries, check results). Outputs: [simulator-after-td2.jsonl](../kit-td1/TD2/simulator-after-td2.jsonl),
and the kit rule replayed on the same inputs ([simulator-kit-rule-td2.jsonl](../kit-td1/TD2/simulator-kit-rule-td2.jsonl)).
The seven kit scenarios are kept, plus six added ones.

## Commands

From `kit-td1/`, standard library only, no network, no key:

```bash
python3 TD2/test_vote_td2.py                                   # vote edge cases
python3 TD2/atelier-vote.py                                    # four synthetic examples
python3 TD2/atelier-vote.py --traces TD1/traces-td1.csv --case C02
python3 TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv
cd TD2
python3 pair_b_wrong_consensus.py --export-csv                 # step 2, delta CSVs
python3 pair_c_family_rates.py --csv family-rates-td2.csv      # step 3, family rates
python3 atelier-routage.py                                     # our rule
python3 atelier-routage.py --rule kit                          # kit rule, same scenarios
```

## Prompts

Unchanged since TD 1: [prompts-en.md](../kit-td1/TD1/prompts-en.md). No model was called in TD 2.

## What failed or stays open

- After the kit was reorganised into `TD1/`, `TD2/` and `TD3/` (commit `f256bbb`), Pair A's first
  version did not run from the repository. The method was in a copy of the skeleton, and the
  comparison script read the traces from the wrong folder. Both cross-reviews caught it. The method
  was moved into the shared skeleton, the copies were removed and the paths were fixed. The table is
  regenerated byte for byte.
- F2b rests on a single question (C10), so its line in the rule is the least supported.
- No free model is enough on its own for the age families and the combined questions. The price of the
  reference check carries over to TD 3.

## Limits

Twenty questions, one run per cell, one batch: these results support a hypothesis about this batch,
not a general error rate, a permanent ranking of the models or a guarantee on quorums. The
availabilities and levels of the simulator are fictitious. The canary was designed after seeing this
batch's errors.

## Next steps (TD 3)

- Cost the checks: reference query, canary and quorum calls, per use.
- Shadow-test a senior route on the twenty questions before it can deliver anything other than a
  reference-checked figure.
- Re-run the age families a few times to see whether qwen3.8-27b's 4/4 on F2 holds.
- Add a remaining-allocation counter to the simulator.

## AI assistance

A coding assistant helped with parts of the scripts and the wording. Each pair checked its figures
against the traces and the database, and every figure above can be replayed with the commands.
