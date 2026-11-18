# TD 2, Pair C: routing rule and simulator

Section of `reports/td2.md` for Step 3, written by Pair C (Nils Demougeot, Edgar Merceron and Sacha Sommier). No model was called in
this step. The rates are recomputed from the TD 1 traces. The simulator runs are **synthetic**: the
resources, their availability and the costs are scenario inputs, and only the 0.045 USD of the paid
senior route comes from portfolio prices.

## Files

| File | What it is |
|---|---|
| [routing-rule-td2.md](routing-rule-td2.md) | The one-page rule, with the TD 1 cells behind every line |
| [pair_c_family_rates.py](pair_c_family_rates.py) | Recomputes the rate per family and model from the 100 TD 1 cells, plus what 2-of-3 and 3-of-5 would have decided on those cells |
| [family-rates-td2.csv](family-rates-td2.csv) | Output of the script above |
| [atelier-routage.py](atelier-routage.py) | Simulator with our `RESOURCES` and `choose`; the kit rule is kept as `choose_kit` |
| [simulator-before-td2.jsonl](simulator-before-td2.jsonl) | Kit simulator, untouched, on the kit scenarios |
| [simulator-after-td2.jsonl](simulator-after-td2.jsonl) | Our rule on our scenarios |
| [simulator-kit-rule-td2.jsonl](simulator-kit-rule-td2.jsonl) | Kit rule replayed on our resources and scenarios (`--rule kit`) |

To replay:

```
python3 pair_c_family_rates.py --csv family-rates-td2.csv
python3 atelier-routage.py                # our rule
python3 atelier-routage.py --rule kit     # kit rule, same scenarios
python3 atelier-routage.py --scenario deferrable
```

The kit version of `atelier-routage.py` is the one in commit `f256bbb`, which produced
`simulator-before-td2.jsonl`.

## Rates per family

Rates are given in [routing-rule-td2.md](routing-rule-td2.md#1-what-td-1-measured-correct--cells-last-attempt).
The point that shaped the whole rule: F1 and F3 are solved by every model (29/30 and 20/20, the missing
cell is an HTTP 429), while every family with an age in it falls apart (F2 10/20, F2b 2/5, combined 16/25).
The age families are also where no free model is good enough on its own across the board: qwen3.8-27b is the
only one at 4/4 on F2 but 0/1 on F2b and 1/5 on combined, and gpt-oss-20b is the reverse.

What a vote would have done on the same cells (script output):

| Family | 2-of-3, fixed panel | 3-of-5, five models |
|---|---|---|
| F1 | 6 right | 6 right |
| F2 | C02 C08 C09 right, C11 abstain | C08 C09 right, C11 abstain, **C02 wrong (0)** |
| F2b | C10 abstain | C10 abstain |
| F3 | 4 right | 4 right |
| Combined | C16 C18 right, C15 C17 C19 abstain | C16 C17 C18 right, C15 C19 abstain |

Neither quorum is "the stronger one". 3-of-5 delivers one more combined question but accepts the
wrong 0 on C02. That is why the rule uses 2-of-3 on distinct makers and adds the reference where a
wrong figure would reach a customer.

## The kit simulator, before

`python3 atelier-routage.py` on the kit file ([simulator-before-td2.jsonl](simulator-before-td2.jsonl)):

| Scenario | Decision | Resource | Cash | Reason given |
|---|---|---|---|---|
| simple | run | small-free | 0 | eligible included capacity |
| complex | run | senior-subscription | 0 | eligible included capacity |
| deferrable | defer 60 min | senior-subscription | 0 | recheck availability at wake-up |
| urgent | run | senior-api | 0.30 | available route within the authorised budget |
| budget exhausted | abstain | - | 0 | no eligible resource within deadline and budget |
| high impact | run | senior-subscription | 0 | eligible included capacity |
| unknown capability | abstain | - | 0 | no eligible resource within deadline and budget |

How we read it. `choose` filters on `level >= difficulty`, then tries, in this order: an available
resource with `cash == 0` (cheapest allocation first), waiting for a resource with `cash == 0` that
refills before `deadline_minutes`, a paid resource within `budget`, and finally abstention.
In "deferrable" the subscription is exhausted, small-free is not eligible (level 1 < 3), and senior-api
is available, but waiting 60 minutes comes before paying 0.30. In "urgent" the deadline is 5 minutes,
shorter than the 60-minute reset, so it pays.

Three things we did not like:

- The check only depends on `high_impact`. There are two strings in total, and nothing about the
  question family.
- The reasons do not say which data the decision rests on. The two abstentions give the same reason,
  although one is a budget problem and the other a capability problem.
- The levels are given, not measured. Nothing ties "level 1" to a test.

## Our version, after

What changed in [atelier-routage.py](atelier-routage.py):

- `RESOURCES` are the routes we used in TD 1 (gpt-oss-20b, gpt-oss-120b and qwen3.8-27b on Groq Free,
  north-mini-code on OpenRouter), plus claude-fable-5-1 from the portfolio, once through the
  subscription and once through the paid OpenRouter route (0.045 USD per request). Each TD 1 route lists
  the cells it failed, per family.
- A TD 1 route is eligible on a family only if it got every cell of that family right. An untested
  route falls back on its portfolio level (G1 = level 3), and is never eligible for a payout.
- The route depends on the family, the check depends on the use. The check table is the one in the rule,
  and each check string ends with the TD 1 cells that justify it.
- Requests carry `family` and `use` instead of `difficulty` and `high_impact`. Scenarios keep the kit
  names, plus "provider unavailable" and "cannot wait", which were missing to see the fallback and
  the subscription branch, and four scenarios for the policy below.
- A versioned policy, `pair-c-v1`, is applied around `choose` by `route()`:
  - at most 10 attempts per route, one minute apart (the values of Lecture 2), then the next eligible
    route, with the time already spent taken off the deadline;
  - the required check has a result (given by the scenario), and only "pass" delivers. A failure or a
    timeout keeps the value back and logs it. This is the fix for the Lecture 2 incident, where a check
    that timed out after 3 s let the answer through;
  - every output carries the policy id, each attempt and the check result.
- The quorum panel is checked at start-up: the same route twice, or two models of the same maker
  (gpt-oss-120b with gpt-oss-20b, for example), raises a `ValueError`.

Results ([simulator-after-td2.jsonl](simulator-after-td2.jsonl)), with the kit rule replayed on the
same inputs ([simulator-kit-rule-td2.jsonl](simulator-kit-rule-td2.jsonl)):

| Scenario | Request | Our rule | Kit rule on the same inputs |
|---|---|---|---|
| simple | F1, dashboard | run gpt-oss-20b, check none (6/6 on C01 C04 C05 C06 C07 C20) | run gpt-oss-120b (tie broken on the id) |
| complex | F2, dashboard | run qwen3.8-27b, 2-of-3 (4/4 on C02 C08 C09 C11) | run claude-fable-5-1 subscription, never tested |
| provider unavailable | F1, Groq down | run north-mini-code (6/6 on F1) | same |
| deferrable | F2, Groq down, can wait | **defer 1 min** for qwen3.8-27b | run claude-fable-5-1 subscription |
| cannot wait | F2, Groq down, 5 min | run claude-fable-5-1 subscription, reference check | same route, generic check |
| urgent | combined, customer, free and subscription down | run claude-fable-5-1 paid, 0.045 USD, reference check | same route |
| budget exhausted | F2, budget 0 | abstain, lists each refused route and why | abstain, generic reason |
| high impact | F2, payout | run qwen3.8-27b, reference + review | run claude-fable-5-1 subscription for a payout |
| unknown capability | "age at first order" | abstain, not a TD 1 family | abstain |
| transient 429 | F2, qwen3.8-27b answers on attempt 3 (as for C18 and C19 in TD 1) | run qwen3.8-27b, 3 attempts, delivered | run claude-fable-5-1 subscription |
| retries exhausted | F1, gpt-oss-20b answers 429 on every attempt | 10 attempts in 10 min, then run gpt-oss-120b (6/6 on F1), delivered | run gpt-oss-120b |
| check failed | F2, customer, the check fails | run qwen3.8-27b, **not delivered**, failure logged | run claude-fable-5-1 subscription, no notion of check result |
| check timeout | combined, dashboard, the check times out | run gpt-oss-20b, **not delivered**, failure logged | run claude-fable-5-1 subscription, no notion of check result |

In our rule, every decision is delivered only if `delivered` is `true`. A `defer` or an `abstain` never
delivers anything.

The kit rule is not wrong on its own terms. It just has no way to know that, on our data, the free
qwen3.8-27b is the only route that was right on all of F2, while the senior model has never been
tested on our questions.

## Why `choose` takes the subscription before waiting, and when to reverse it

**The kit priority.** In the kit `choose`, any available resource with `cash == 0` is taken before
waiting, and that includes a subscription with `allocation > 0`. So a free resource that ran out and
comes back before the deadline loses to a subscription that is available now. The reasons we see:

1. `cash == 0` means no new spending. The subscription is already paid, so a call only uses up included
   allocation. This is what the docstring calls "already paid capacity is preferred before new spending".
2. Running now gives an answer now. Waiting delays it by `reset_minutes` for nothing, as long as both
   resources are rated as good enough.
3. A refill time is a promise, not a measurement. At wake-up the free resource may still answer 429,
   and then the time is lost. The kit docstring says availability has to be measured again at wake-up.
4. For the kit, both resources are equally good, since `level >= difficulty` is the only quality filter.
   The only difference left between them is time, and the subscription wins on time.

**When to reverse it.** The priority should flip when waiting costs little and the subscription is
worth more than the time saved:

- **The free resource has better evidence on this family.** This is our case, and the one we implemented.
  On F2, qwen3.8-27b was right on 4/4 cells (C02 C08 C09 C11) and claude-fable-5-1 was never tested. If the
  request can wait and the Groq limit resets before the deadline (one minute for the output tokens per
  minute limit we hit in TD 1), we defer instead of using the subscription. See "deferrable" vs "cannot wait".
- **The allocation is scarce.** Suppose only a few requests are left on the subscription before its own
  reset, and harder or higher-stakes requests are queued that only the senior model can serve (combined
  questions for a customer, for example). Then spending it on a deferrable dashboard question pushes
  those later requests onto the paid route or into abstention. Our simulator has no counter for the
  remaining allocation, so this case is described here but not coded. That is for TD 3, with the costs.

The kit order still holds when the request cannot wait, when the refill is after the deadline, or when
no validated route is coming back. In those cases our `choose` also takes the subscription.

## Limits

- Twenty questions and one run per cell. F2b is a single question (C10), so its line in the rule is
  the least supported. The accidental second Dots run in TD 1 changed five verdicts out of twenty,
  so a model at 4/4 today could be at 3/4 tomorrow.
- "Cheapest" is a tie-break between free routes, based on the price of the paid route of the same model.
  On the free tier, the real constraint is the rate limit, not the price.
- The panel availability is not simulated separately from the route. When Groq is down, the 2-of-3
  panel cannot run either, so we fall back on the reference check for untested routes.
- The reference check assumes we have a validated query for each family. That holds for the five TD 1
  families and nothing else.

## Next steps

- Shadow-test claude-fable-5-1 (or another senior route) on the twenty questions before it can deliver
  anything other than a reference-checked figure.
- Re-run the age families a few times to see if the 4/4 of qwen3.8-27b on F2 holds.
- Add a remaining-allocation counter to the simulator to code the second reversal case (TD 3).

## Code and AI disclosure

A coding assistant (Claude) helped us with parts of the scripts and with the wording. We checked every
rate and every quorum outcome ourselves against `TD1/model-question-comparison-en.csv`, and both
simulator outputs can be replayed with the commands above.
