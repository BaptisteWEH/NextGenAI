# TD 1 session report

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

**AI disclosure.** We wrote the script with a coding assistant (Claude). No value
comes from a model: every number is produced by executing SQL on the base and is
confirmed by two independent computations.

**Cross-check between members.** _To complete: who checked which questions._

## Step 2 onwards

_To complete: model calls, traces, comparison, summary, limitations, contributions, next steps._
