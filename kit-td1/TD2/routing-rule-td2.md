# Routing rule, DIA3-3 (TD 2, Pair C)

Built only on the 100 TD 1 cells: five free models, twenty questions, one run per cell at
temperature 0 (21 October 2026). Twenty questions are enough for a hypothesis about this batch,
not for an error rate. Rates come from [pair_c_family_rates.py](pair_c_family_rates.py) and are
saved in [family-rates-td2.csv](family-rates-td2.csv).

## 1. What TD 1 measured (correct / cells, last attempt)

| Family | Questions | gpt-oss-120b | gpt-oss-20b | north-mini-code | qwen3.8-27b | dots-3-note | Family |
|---|---|---|---|---|---|---|---|
| F1 period | C01 C04 C05 C06 C07 C20 | 6/6 | 6/6 | 6/6 | 5/6 (C20: HTTP 429) | 6/6 | 29/30 |
| F2 age at a date | C02 C08 C09 C11 | 3/4 (C11) | 2/4 (C02 C11) | 0/4 | **4/4** | 1/4 | 10/20 |
| F2b age at order | C10 | **1/1** | **1/1** | 0/1 (invalid SQL) | 0/1 | 0/1 | 2/5 |
| F3 product list | C03 C12 C13 C14 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 20/20 |
| Combined | C15 C16 C17 C18 C19 | **5/5** | **5/5** | 2/5 | 1/5 (C16: HTTP 429) | 3/5 | 16/25 |

The denominator is the number of cells. The two HTTP 429 cells of qwen are counted as "not correct",
but they are access failures, not wrong answers.

## 2. The rule

| Family | First route (cheapest correct in TD 1) | Internal dashboard | Customer-facing figure | Payout | If the first route is unavailable |
|---|---|---|---|---|---|
| F1 | gpt-oss-20b#groq | none | 2-of-3 | reference + review | gpt-oss-120b#groq, then north-mini-code, then wait for refill, then abstain |
| F3 | gpt-oss-20b#groq | none | 2-of-3 | reference + review | same as F1 |
| F2 | qwen3.8-27b#groq (only 4/4) | 2-of-3 | 2-of-3 + reference | reference + review | no second route at 4/4: wait for the Groq refill if the request can wait, otherwise the senior subscription with the reference check (never for a payout), otherwise abstain |
| F2b | gpt-oss-20b#groq | reference | reference | reference + review | gpt-oss-120b#groq, then wait, then abstain |
| Combined | gpt-oss-20b#groq | 2-of-3, reference if it abstains | reference | reference + review | gpt-oss-120b#groq, then wait, then abstain |

"2-of-3" is the fixed panel gpt-oss-120b, north-mini-code and qwen3.8-27b (three makers). The format
check (one row, integer euro cents, read-only SQL) always runs and is not listed.

**Cheapest.** All five routes cost 0 USD on their free tier. We break the tie with the cost of the
same request (2,000 tokens in, 500 out) on the paid route of the same model: gpt-oss-20b 0.0003 USD
(Groq, 0.075 / 0.30 per million), gpt-oss-120b 0.0006 USD (OpenRouter, 0.15 / 0.60), qwen3.8-27b
0.0036 USD (Groq, 0.80 / 4.00). north-mini-code and dots have no paid route, so they come last.

## 3. Why these checks

- **"none" only for F1 and F3 dashboards.** No model made an error on these two families (the only
  missing cell is an HTTP 429), and gpt-oss-20b scored 100 % on both. Everywhere else, the family had
  at least one TD 1 error or the figure leaves the company, so a quorum or a deterministic check is required.
- **F2: 2-of-3, not 3-of-5.** The fixed panel gets C02, C08 and C09 right and abstains on C11
  (768850, 0, 446690). With all five models, gpt-oss-20b, north-mini-code and dots all return 0 on C02,
  so 3-of-5 accepts 0 against a reference of 590320. A bigger k did not make the answer more true.
- **F2b: reference straight away.** On C10 both quorums abstain (558980 from the two gpt-oss models,
  119410 from qwen and dots, invalid SQL from north-mini-code). A vote gives no answer here. This
  family rests on a single question, so it is the weakest line of the rule.
- **Combined: free models are not enough for a customer.** 2-of-3 abstains on C15, C17 and C19. The
  only two models at 5/5 are gpt-oss-120b and gpt-oss-20b, same maker, so their agreement is not two
  independent votes. The reference has to do the work, and that is the checking cost we carry into TD 3.
- **Payout: reference + review whatever the family.** A model that was never tested in TD 1
  (claude-fable-5-1) can run in shadow next to the panel, but never delivers a paid amount.

**What "reference" means outside the lab.** The lab reference values do not exist in production.
Here, the reference is the validated exact query of the family (one schema per closed question type),
run read-only by code. The model's value is delivered only if it equals that value. Same input, same
output, and the vote never sees it. For F2 and F2b, Pair B's canary test is a second deterministic check
that needs no reference value. It runs the model's SQL on four synthetic customers born around the
reference date, and only the exact age window returns 300 cents. It rejects the 0 of C02 (gpt-oss-20b,
north-mini-code, dots) and the 100 of C10 (qwen, dots) before the vote (`pair_b_wrong_consensus.py`,
section 6). It is built for 2026-09-25, so the four birth dates must be rebuilt for each question date.

## 4. Fixed in advance (policy `pair-c-v1`)

- At most 10 attempts per route, one minute apart. After that, the next route of the table, then wait
  or abstain.
- A failed or timed-out check means no delivery, and the check belongs to the request, not to the route.
- One vote per maker in a quorum: the same model twice, or two models of the same maker, is refused.
  Failed calls stay in n, and retries are not votes.
- A question outside these five families is refused or passed to a person.
- Every decision is logged with the policy id, the attempts, the check and its result.

All of this is coded in [atelier-routage.py](atelier-routage.py).
