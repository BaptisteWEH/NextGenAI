# TD 1 session report

**Class:** DIA 3 · **Sub-group:** DIA3-3 · **Session:** 21 October 2026

| Role | Member | Work |
|---|---|---|
| A | Edgar Merceron | Batch `groq:openai/gpt-oss-120b` ([traces-A.csv](../kit-td1/traces-A.csv)) |
| B | Baptiste Wehry | Batch `groq:openai/gpt-oss-20b` ([traces-B.csv](../kit-td1/traces-B.csv)) |
| C | Leo Garcia (Inès) | Batch `openrouter:cohere/north-mini-code:free` ([traces-C.csv](../kit-td1/traces-C.csv)) |
| D | Nils Demougeot | Batch `groq:qwen/qwen3.8-27b` ([traces-D.csv](../kit-td1/traces-D.csv)) |
| E | Sacha Sommier | Batch `openrouter:dots-studio/dots-3-note-preview:free` ([traces-E.csv](../kit-td1/traces-E.csv)) |
| F | Maxence Milleker | Cross-check, consolidation of the traces and summaries (_to detail_) |
| G | Timothée Barselo | Cross-check, consolidation of the traces and summaries (_to detail_) |

The sub-group has seven members, so there is no role H.

**In short.** The reference equals the answer key (20/20). We ran 100 cells on five
free models: 105 real calls, including 5 retries. All five models answer every period and
product question correctly. **Every failure is on the completed-age convention.** Three models
agree on the same wrong value for C02.

All rows are **real** calls made on 2026-10-21. This report uses no replayed or synthetic example.

## Step 1 - Reference values

**Result.** [reference-td1.csv](../kit-td1/reference-td1.csv) holds twenty queries,
each with its value. All twenty values equal the published reference values
(reference-values-td1-en, 18 October 2026): **20/20, no difference, so there was no cause to correct.**

**Method.** The values come from our own queries, run on `data/boutique.sqlite`
opened read-only. The published table was used only afterwards, for the comparison.
[build_reference_td1.py](../kit-td1/build_reference_td1.py) does the following:

1. It checks the SHA-256 fingerprints of the base and the CSV files against `data/manifest.json`.
2. It runs the reference query for each question. It checks that each query returns
   one row and one column named `revenue_cents`.
3. It recomputes each value two other ways:
   - **check A:** pure Python on the CSV files (no SQL), with its own completed-age function;
   - **check B:** a second SQL formulation. Age is the year difference minus 1 when
     the birthday (month-day) has not yet been reached. Products use `OR` and the
     period uses `NOT (date < start)`.
4. It writes the CSV only if the reference query, check A and check B agree on all
   twenty questions. Then it compares the values with the published table.

**Conventions applied** (consigne-etudiante, section 1):

| Convention | Rule in our queries | Edge case in the base that tests it |
|---|---|---|
| Period | `o.date >= start AND o.date < end` | Lines at `2026-03-01 00:00:00` (in C01) and `2026-06-01 00:00:00` (out of C01/C07, in C05/C20) |
| Age on a reference date D | `date(birth,'+25 years') <= D AND date(birth,'+26 years') > D` | Customers born 2001-09-24 / 25 / 26: C02, C08 and C09 differ |
| Age at the time of the order | Same rule with D = `date(o.date)` | C008 (born 2001-05-15) orders on 2026-05-15, on their 25th birthday: counted (C10, C18) |
| Product list | `o.product_id IN (...)` | C13 (`a`, `c`), C19 (`d` only) |
| Amount | `COALESCE(SUM(quantity_product * price), 0)`, cents excl. VAT | C06 and C14: no order in the period, so 0, not NULL |

**Cross-check between members.** _To complete: who checked which questions._

## Step 2 - The five models

Every call used the same parameters: one request in flight at a time, 3 s between requests,
temperature 0, 1 024 output tokens at most, a 45 s timeout and at most one retry per cell.
Each operator kept their state file (`state-X.jsonl`) to enforce the retry limit.

| Op. | Model | Calls (cells + retries) | HTTP 429 | Mean latency | Tokens in / out |
|---|---|---:|---:|---:|---|
| A | `groq:openai/gpt-oss-120b` | 20 (20 + 0) | 0 | 1 006 ms | 12 814 / 5 270 |
| B | `groq:openai/gpt-oss-20b` | 21 (20 + 1) | 1 | 820 ms | 12 814 / 5 528 |
| C | `openrouter:cohere/north-mini-code:free` | 20 (20 + 0) | 0 | 2 190 ms | 11 194 / 2 170 |
| D | `groq:qwen/qwen3.8-27b` | 24 (20 + 4) | 6 | 539 ms | 11 348 / 2 488 |
| E | `openrouter:dots-studio/dots-3-note-preview:free` | 20 (20 + 0) | 0 | 3 140 ms | 11 858 / 3 593 |

All attempts are merged under one header in [traces-td1.csv](../kit-td1/traces-td1.csv)
and [traces-td1.jsonl](../kit-td1/traces-td1.jsonl) (105 rows each, the JSONL concatenates
`state-A..E.jsonl`). The source CSV and JSONL files are kept next to them.

**Prompt, as used.** We did not change it. It is the `SYSTEM_PROMPT` and the
`USER_PROMPT_TEMPLATE` of [skeleton-multi-llm-en.py](../kit-td1/skeleton-multi-llm-en.py#L104-L122),
identical for all models, written out in [prompts-en.md](../kit-td1/prompts-en.md) with the
fingerprint of each question. We checked that every question has one single `prompt_sha256`
across the 105 calls, and that recomputing it from the text gives the recorded value.

**Extra run, outside the batch.** Operator C first ran the Dots model by mistake (wrong
`--models` value): 20 real OpenRouter calls on 2026-10-21, 13:57 to 13:59 UTC. They are kept in
[extra-runs/](../kit-td1/extra-runs/) and are not counted in the 100 cells or in any result.
The Cohere batch was then run with new files.

## Step 3 - Results

Final status per model and question (last attempt). The data is in
[model-question-pivot-td1.csv](../kit-td1/model-question-pivot-td1.csv), and the long form with one
explanation per cell is in [model-question-comparison-en.csv](../kit-td1/model-question-comparison-en.csv).

| Model | C02 | C08 | C09 | C10 | C11 | C15 | C16 | C17 | C19 | C20 | Correct |
|---|---|---|---|---|---|---|---|---|---|---|---:|
| A gpt-oss-120b | ok | ok | ok | ok | **X** | ok | ok | ok | ok | ok | 19/20 |
| B gpt-oss-20b | **X** | ok | ok | ok | **X** | ok | ok | ok | ok | ok | 18/20 |
| C north-mini-code | **X** | **X** | inv | inv | **X** | **X** | ok | **X** | **X** | ok | 12/20 |
| D qwen3.8-27b | ok | ok | ok | **X** | ok | **X** | 429 | **X** | **X** | 429 | 14/20 |
| E dots-3-note | **X** | ok | **X** | **X** | inv | **X** | ok | ok | inv | ok | 14/20 |

Legend: X = wrong value, inv = invalid SQL, 429 = access failure (not evaluated).
The other ten questions (C01, C03-C07, C12-C14, C18) are correct for all five models.

**By family** (correct / evaluated). Combined questions are counted only in the last column.

| Model | Period (6) | Age (5) | Product (4) | Combined (5) |
|---|---|---|---|---|
| A gpt-oss-120b | 6/6 | 4/5 | 4/4 | 5/5 |
| B gpt-oss-20b | 6/6 | 3/5 | 4/4 | 5/5 |
| C north-mini-code | 6/6 | 0/5 | 4/4 | 2/5 |
| D qwen3.8-27b | 5/5 (+1 access failure) | 4/5 | 4/4 | 1/4 (+1 access failure) |
| E dots-3-note | 6/6 | 1/5 | 4/4 | 3/5 |

The details, with index, prices and access for each model, are in
[five-model-summary-en.csv](../kit-td1/five-model-summary-en.csv).

### Causes of failure, read from the SQL of the traces

We found one cause per failed cell. The full wording of each is in the comparison file.

- **Age window without a lower bound** (C C08, C C15; A C11). For example,
  `birth_date > date(D,'-26 years') AND birth_date <= D` keeps every customer aged 0 to 25.
- **Year difference without the month-day correction, or with a wrong correction**
  (D C10, E C10, E C15, D C17). D C17 is off by one day on the birthday. It excludes C001
  (born 2001-09-25, exactly 25: 80 190) and includes C004 (born 2000-09-25, 26: 70 500). The
  difference is 9 690, which is exactly the observed gap.
- **Malformed date expressions that give NULL, so 0** (C C19: invalid modifier `'-25-01-01'`;
  E C02: anniversary built from the year difference; D C19: a year compared with a full date).
- **Impossible or misread conditions, so 0** (C C02: inverted anniversaries; D C15: month-day
  only; E C09: birth date = reference date; C C11: invented birth date and order period;
  B C02: birth date taken as a date of the last year).
- **Invalid SQL** (C C09: alias inside WHERE; C C10: malformed `strftime`; E C11: draft
  expression left in the answer; E C19: misplaced parenthesis in `CAST`).

**Access failures are not wrong answers.** Qwen (D) hit the Groq Free limit of 1 000 output
tokens per minute (OTPM): 6 HTTP 429 over 4 cells. C18 and C19 succeeded on retry. C16 and C20
failed twice and are `not_executed`, so Qwen is evaluated on 18 cells. B had one transient 429
on C19, and the retry succeeded.

### Several models agree on a wrong value

- **C02: three models out of five return 0** (B, C, E), each for a different reason. Only A
  and D return 590 320. **A 3-of-5 majority vote would select the wrong value.**
- **C10:** D and E both return **119 410** with different SQL: both keep only "year difference
  = 25 and birthday reached". A and B return the reference, 558 980, and C is invalid. A vote
  would be a 2-2 tie.
- **C11:** five different outcomes. Only D is correct, so no majority exists.

Agreement between models is therefore not evidence of correctness. These cases prepare the vote of TD 2.

### Routing hypothesis (for this batch only)

- **Period and product questions:** every model is enough. Choose the cheapest or fastest
  route. Qwen was the fastest, but its free tier is limited in output tokens per minute.
- **Age questions:** gpt-oss-120b is the most reliable here (9/10 on age and combined
  questions), and it still fails C11. Age questions need a check or a vote.

## Limitations

- One run per cell at temperature 0. We did not measure variability, so these are observations,
  not error rates. The accidental second run of Dots ([extra-runs/](../kit-td1/extra-runs/))
  hints at it: same prompt, 13/20 instead of 14/20, five questions change verdict (C08, C11,
  C17, C18, C19). Two runs are not enough to measure a rate.
- Qwen was evaluated on 18 cells, not 20, because of access failures.
- The summary template named `inclusionai/ling-3.0-flash-sante:free` for model C (28 September
  list). The model actually called is `cohere/north-mini-code:free`, from the 14 October selection.
- Cohere and Dots have no public index in the 28 September portfolio and no documented paid route
  of the same model, so we wrote N/A in the summary.
- Real spend is 0: free routes only. OpenRouter returned a native cost of 0, and Groq returned none.

## Next steps (TD 2)

- Implement `vote_k_sur_n` and test it on C02 (wrong majority), C10 (tie) and C11 (no majority).
- Decide what the system answers when the models disagree: abstain rather than pick a value.
- Plan Groq calls around the OTPM limit, for example with a longer pause for Qwen.

## Code and AI disclosure

- [build_reference_td1.py](../kit-td1/build_reference_td1.py) builds the reference with its two
  independent checks.
- [build_step3_td1.py](../kit-td1/build_step3_td1.py) merges the traces and completes the
  comparison, the summary and the pivot.
- We wrote both scripts with a coding assistant (Claude). We read and checked the code and the
  explanations against the SQL and error fields of the traces. No reference value comes from a model.
