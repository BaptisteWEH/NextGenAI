# Code & Engineering Cross-Review — Step 3 (Pair C) reviewed by Pair B

**Class:** DIA 3 · **Sub-group:** DIA3-3 · **Session:** TD 2 (18 November 2026)  
**Reviewed branch / commit:** `Pair_C` (`23694d8` — *TD2 step 3 (Pair C): routing rule, family rates and adapted simulator*)  
**Authors of Step 3 (Pair C):** Nils Demougeot, Edgar Merceron, Sacha Sommier  
**Reviewers (Pair B — Step 2):** Timothée Barselo & Pair B teammate  

---

## 1. Replay & Reproducibility Check (Executed Locally by Pair B)

We checked out branch `Pair_C` and re-ran all three commands documented in [pair-c-td2.md](pair-c-td2.md):

```bash
python3 kit-td1/TD2/pair_c_family_rates.py
python3 kit-td1/TD2/atelier-routage.py | diff -u kit-td1/TD2/simulator-after-td2.jsonl -
python3 kit-td1/TD2/atelier-routage.py --rule kit | diff -u kit-td1/TD2/simulator-kit-rule-td2.jsonl -
```

- **Result:** Zero diff (`exit code 0`) on both JSONL simulator outputs (`13/13` scenarios reproduced identically) and exact match with [family-rates-td2.csv](family-rates-td2.csv).
- **No network / no secrets:** Standard library only (`argparse`, `csv`, `json`, `collections`, `pathlib`); no API calls or hardcoded keys.

---

## 2. Verification of TD 1 Family Accuracy Rates & Consistency with Pair B (Step 2)

We cross-checked the rates computed by [pair_c_family_rates.py](pair_c_family_rates.py) against our independent scan of [../TD1/traces-td1.csv](../TD1/traces-td1.csv) in `pair_b_wrong_consensus.py`:

| Family | Questions | Pair C computed rates ([family-rates-td2.csv](family-rates-td2.csv)) | Cross-check against Pair B (Step 2) & TD 1 traces | Verdict |
|---|---|---|---|---|
| **F1** (period) | `C01 C04 C05 C06 C07 C20` | `29/30` (`gpt-oss-120b`, `gpt-oss-20b`, `north-mini-code`, `dots-3-note` at `6/6`; `qwen3.8-27b` at `5/6` due to `C20:not_executed` HTTP 429) | Matches `traces-td1.csv`. Pair C properly distinguishes Qwen's `HTTP 429` access failure on `C20` from a reasoning error (Lecture 2, Slide 6). | **PASS** |
| **F2** (completed age at a date) | `C02 C08 C09 C11` | `10/20` (`qwen3.8-27b` `4/4`, `gpt-oss-120b` `3/4`, `gpt-oss-20b` `2/4`, `dots-3-note` `1/4`, `north-mini-code` `0/4`) | Exact agreement with Pair B's Case 1 (`C02`): Pair C correctly notes that **2-of-3 gets `C02` right (`590320`) while 3-of-5 falls into the wrong consensus `0`** (`gpt-oss-20b`, `north-mini-code`, `dots-3-note`), justifying why F2 uses `2-of-3` rather than `3-of-5`. | **PASS** |
| **F2b** (age at order) | `C10` | `2/5` (`gpt-oss-120b` `1/1`, `gpt-oss-20b` `1/1`, `north-mini-code` `0/1 sql_invalid`, `qwen3.8-27b` `0/1`, `dots-3-note` `0/1`) | Exact agreement with Pair B's Case 2 (`C10`): both `2-of-3` and `3-of-5` abstain (`558980` vs shared wrong value `119410`), which justifies why Pair C routes `F2b` to a deterministic check (`reference`) rather than relying on a quorum that abstains. | **PASS** |
| **F3** (product list) | `C03 C12 C13 C14` | `20/20` (all 5 models at `4/4`) | Matches `traces-td1.csv`. | **PASS** |
| **Combined** | `C15 C16 C17 C18 C19` | `16/25` (`gpt-oss-120b` `5/5`, `gpt-oss-20b` `5/5`, `dots-3-note` `3/5`, `north-mini-code` `2/5`, `qwen3.8-27b` `1/5`) | Pair C rightly identifies that the only two `5/5` models (`gpt-oss-120b` and `gpt-oss-20b`) belong to the **same maker (`openai`)**, so they cannot form an independent 2-of-3 majority on their own. | **PASS** |

---

## 3. Verification of Step 3 Assignment Rules & Lecture 2 Policies

We audited [routing-rule-td2.md](routing-rule-td2.md) and [atelier-routage.py](atelier-routage.py) against every requirement of the TD 2 specification (`Pack 2026-11-18-students-5`) and the Lecture 2 slides:

1. **Strict separation of *Difficulty* and *Stakes* (Lecture 2, Slide 26):**
   - In `atelier-routage.py` (`evidence()` lines 131–146 and `required_check()` lines 149–159), question `family` (difficulty/evidence) selects the eligible model route, while `use` (`dashboard`, `customer`, `payout` = stakes) selects the check in `CHECKS`. A bigger model is never used as a substitute for a check.
2. **Consistency constraint on `check = "none"` (Step 3 specification):**
   - In `CHECKS` (lines 77–85), `"none"` is restricted strictly to `("F1", "dashboard")` and `("F3", "dashboard")` when served by a TD 1 route that scored 100 % (`6/6` or `4/4`).
   - Furthermore, line 154 (`if chosen is not None and chosen["td1"] is None:`) ensures that if all free routes are down and even an `F1` dashboard request falls back to an untested route (`claude-fable-5-1`), `"none"` is automatically upgraded to `REFERENCE`.
3. **Price tie-breaking among free routes:**
   - `cost_key(r)` (lines 162–164) breaks ties between `$0` free-tier routes using the dated API-equivalent cost (`paid_route_usd`) for 2,000 input + 500 output tokens (`gpt-oss-20b`: `$0.0003` < `gpt-oss-120b`: `$0.0006` < `qwen3.8-27b`: `$0.0036` < `north-mini-code`: `None / inf`). This cleanly justifies why `gpt-oss-20b#groq` is called first on `F1`, `F3`, `F2b` and `combined`, while `qwen3.8-27b#groq` (the only `4/4` route on `F2`) is called first on `F2`.
4. **Versioned Retry & Incident Policy (`POLICY = "pair-c-v1"`, Lecture 2, Slides 17, 32, 37–39):**
   - **Panel diversity check (`check_panel()`, lines 121–128):** Executed at startup (`main()` line 339); raises `ValueError` if a route appears twice or if two panel members share a `maker`.
   - **Retry policy (`route()`, lines 226–251):** Implements at most `10` attempts per resource, `1` minute apart (`elapsed += max_attempts * pause`), deducts elapsed retry time from `deadline_minutes`, and falls back to the next eligible route after 10 failures (verified in scenarios `transient 429` and `retries exhausted`).
   - **Check gate (`route()`, lines 254–260):** Fixes the Lecture 2 Slide 37 incident. The check belongs to the request, and `decision["delivered"] = (check_result == "pass")`. Both `"fail"` (scenario `check failed`) and `"timeout"` (scenario `check timeout`) set `"delivered": false` and log `"value withheld and logged (pair-c-v1)"`.
   - **Shadow-only policy for untested models on payouts (Lecture 2, Slides 33–34):** Line 138 (`if request["use"] == "payout": return False, "... shadow only for a payout"`) prevents `claude-fable-5-1` (`td1: None`) from ever deciding a payout.
5. **Analysis of `choose()` priority order (`subscription` vs `defer` for free refill):**
   - [pair-c-td2.md](pair-c-td2.md#L134-L164) clearly explains the 4 reasons behind the kit's default order (`cash == 0` sunk cost, immediate latency, refill time is a promise not a fact, and identical capability level in the kit) and implements the reversal in `choose()` lines 195–206: waiting 1 minute for a TD 1-validated free route (`qwen3.8-27b#groq`, `4/4` on `F2`) before spending subscription quota on an untested route (`claude-fable-5-1#claude`) when `can_wait` is true (`deferrable` vs `cannot wait`).

---

## 4. Constructive Link with Pair B's Work (For Final Consolidation in `reports/td2.md`)

- **How Pair B's deterministic check complements Pair C's routing table:**
  In [routing-rule-td2.md](routing-rule-td2.md#L56-L59), Pair C notes that on `F2` (`customer`), `F2b` and `combined`, when a quorum abstains or can be wrong, the rule requires a deterministic code check (`reference`). Pair B's **4-row Binary-Bitmask Canary Check (`canary_age_bitmask_v1` in `pair_b_wrong_consensus.py`)** provides an exact pre-quorum deterministic check for `F2` and `F2b` that requires **no ground-truth answer on `boutique.sqlite`**: by testing each model's generated SQL on 4 synthetic boundary customers (`100, 200, 400, 800` cents), it filters out empty-set queries (`C02` $\rightarrow 0$) and single-cohort queries (`C10` $\rightarrow 100 \neq 300$) before the vote even runs.

**Overall Cross-Review Verdict by Pair B:** **APPROVED** — All calculations,TD 1 cell citations, simulator scenarios and Lecture 2 policies are verified and reproducible.
