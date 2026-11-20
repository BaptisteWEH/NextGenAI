# TD 2 - The quorum, then the routing rule

Session of 18 November 2026. Statement: [enonce-td2-en](enonce-td2-en.html). Group report:
[reports/td2.md](../../reports/td2.md).

TD 2 makes no new model call. Everything starts from the stored TD 1 results:
[`../TD1/traces-td1.csv`](../TD1/traces-td1.csv) and [`../TD1/reference-td1.csv`](../TD1/reference-td1.csv).
The three steps were split between three pairs. Each step uses the result of the previous one:

```
TD 1 traces ──► Step 1: vote on the 20 questions ──► Step 2: why the vote can be wrong (C02)
                (Pair A)                              (Pair B)
                         └──────────────┬──────────────────────┘
                                        ▼
                    Step 3: routing rule per family, tested on the simulator (Pair C)
```

## Step 1 - The k-of-n vote (Pair A)

Detailed section: [td2-pairA-vote.md](td2-pairA-vote.md).

| File | Role |
|---|---|
| [`../skeleton-multi-llm-en.py`](../skeleton-multi-llm-en.py) | `Orchestrateur.vote_k_sur_n` is completed in the shared skeleton |
| [test_vote_td2.py](test_vote_td2.py) | Edge-case tests: agreement, disagreement, unavailable members, duplicates, 0 as a vote, tie |
| `atelier-vote.py` | Kit workshop: four synthetic examples, then the real traces of one question |
| [compare-vote-td2.py](compare-vote-td2.py) | Our driver: fixed 2-of-3 panel and 3-of-5 on the twenty questions |
| [vote-comparison-td2.csv](vote-comparison-td2.csv) | **Output:** the table of the twenty decisions |

**Result carried forward:** 2-of-3 is never wrong but abstains 5 times; 3-of-5 decides once more
but returns a wrong consensus on **C02**.

## Step 2 - The wrong consensus (Pair B)

Detailed section: [pair-b-td2.md](pair-b-td2.md).

| File | Role |
|---|---|
| [pair_b_wrong_consensus.py](pair_b_wrong_consensus.py) | Finds shared wrong values, replays the quorums with the Step 1 vote, runs the SQL diagnosis and the canary check |
| [delta-c02-td2.csv](delta-c02-td2.csv), [delta-c10-td2.csv](delta-c10-td2.csv) | **Output:** customer-by-customer gap between the reference and the wrong queries |

**Result carried forward:** three different SQL errors give the same 0 on C02. A quorum is not a
check, so the age questions need a deterministic check (reference query or canary).

## Step 3 - The routing rule (Pair C)

Detailed section: [pair-c-td2.md](pair-c-td2.md).

| File | Role |
|---|---|
| [pair_c_family_rates.py](pair_c_family_rates.py) | Rate per question family and model, from the TD 1 cells |
| [family-rates-td2.csv](family-rates-td2.csv) | **Output:** those rates |
| [routing-rule-td2.md](routing-rule-td2.md) | **The one-page rule**: first route, check per use, fallback, each line citing its TD 1 cells |
| `atelier-routage.py` | Simulator adapted to our rule (the kit rule is kept as `--rule kit`) |
| [simulator-before-td2.jsonl](simulator-before-td2.jsonl) | **Before:** kit simulator, unchanged |
| [simulator-after-td2.jsonl](simulator-after-td2.jsonl) | **After:** our rule |
| [simulator-kit-rule-td2.jsonl](simulator-kit-rule-td2.jsonl) | The kit rule on our inputs, for comparison |

## Cross-reviews

Each pair was reviewed by the two others, and the requested changes were applied:
`review-pairA-par-pairB.md`, `review-pair-a-by-pair-c.md`, `review-pair-b-by-pair-a.md`,
`review-pair-b-by-pair-c.md`, `review-pair-c-by-pair-a.md`, `review-pair-c-by-pair-b.md`.

## Replay

Standard library only, no network, no key. From `kit-td1/`:

```bash
python TD2/test_vote_td2.py
python TD2/atelier-vote.py
python TD2/atelier-vote.py --traces TD1/traces-td1.csv --case C02
python TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv
cd TD2
python pair_b_wrong_consensus.py --export-csv
python pair_c_family_rates.py --csv family-rates-td2.csv
python atelier-routage.py > simulator-after-td2.jsonl
python atelier-routage.py --rule kit > simulator-kit-rule-td2.jsonl
```

Each command regenerates its output file identically.

**Next:** TD 3 prices the checks that this rule requires (reference query, canary, quorum calls) and
chooses a configuration for a named use case.
