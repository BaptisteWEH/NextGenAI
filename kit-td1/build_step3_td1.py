"""TD 1 step 3: consolidate the five raw traces and complete the summaries.

Written with coding assistance (Claude), disclosed. Explanations below were read from the SQL
and error fields of the traces; each cites the evidence. Rerunnable: rows already present
in the comparison file are kept, only missing model/question rows are added.

Outputs (in kit-td1/):
- traces-td1.csv: every attempt of traces-A..E.csv under one header (sources kept);
- model-question-comparison-en.csv: one final row per model/question (last attempt);
- five-model-summary-en.csv: rows of models C, D, E filled, row B price corrected;
- model-question-pivot-td1.csv: models x questions matrix of final statuses (plenary view).
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPERATORS = "ABCDE"
CASES = [f"C{i:02d}" for i in range(1, 21)]
FAMILIES = {  # same split as the rows already filled by the sub-group
    "period_results": ["C01", "C04", "C05", "C06", "C07", "C20"],
    "age_results": ["C02", "C08", "C09", "C10", "C11"],
    "product_results": ["C03", "C12", "C13", "C14"],
    "combined_results": ["C15", "C16", "C17", "C18", "C19"],
}

# (model, case) -> (explanation for the comparison CSV, short cause for the summary)
CAUSES = {
    # C: cohere/north-mini-code:free
    ("cohere/north-mini-code:free", "C02"): (
        "Age convention: anniversary comparisons inverted, date(birth,'+25 years') > D AND "
        "date(birth,'+26 years') <= D; impossible condition, so 0", "inverted anniversaries, 0"),
    ("cohere/north-mini-code:free", "C08"): (
        "Age convention: birth_date > date(D,'-26 years') AND birth_date <= D keeps every customer aged 0 to 25, "
        "no 25-year lower bound", "age 0-25 window"),
    ("cohere/north-mini-code:free", "C09"): (
        "SQL error: column alias 'AS age_year' inside a WHERE expression, syntax error near \"AS\"; "
        "the expression also computes the birth year, not an age", "alias inside WHERE"),
    ("cohere/north-mini-code:free", "C10"): (
        "SQL error: malformed strftime/CAST call mixing '+N years', 'unixepoch' and ' days', "
        "syntax error near \",\"", "malformed strftime call"),
    ("cohere/north-mini-code:free", "C11"): (
        "Question misread: birth_date between '2026-11-24' and '2026-11-25' instead of an age filter, plus an "
        "invented order period 2026-12-01 to 2027-01-01; no row, so 0", "invented birth date and period, 0"),
    ("cohere/north-mini-code:free", "C15"): (
        "Age convention: birth_date > date('2026-09-25','-26 years') AND <= '2026-09-25' keeps customers aged "
        "0 to 25, no 25-year lower bound", "age 0-25 window"),
    ("cohere/north-mini-code:free", "C17"): (
        "Age convention: birthday test compares substr(month)||'-'||substr(year), e.g. '09-2001', with '09-25'; "
        "the year is used in place of the day, so the age is wrong for part of the customers", "month-year vs month-day"),
    ("cohere/north-mini-code:free", "C19"): (
        "Age convention: date('2026-09-25', '-25-01-01') is not a valid SQLite modifier, it returns NULL; "
        "the comparison is never true, so 0", "invalid date modifier, 0"),
    # D: qwen/qwen3.8-27b (already in the comparison file; short causes for the summary)
    ("qwen/qwen3.8-27b", "C10"): ("", "second branch is age 23"),
    ("qwen/qwen3.8-27b", "C15"): ("", "month-day only, 0"),
    ("qwen/qwen3.8-27b", "C17"): ("", "off by one day on the birthday"),
    ("qwen/qwen3.8-27b", "C19"): ("", "year compared with a full date"),
    # E: dots-studio/dots-3-note-preview:free
    ("dots-studio/dots-3-note-preview:free", "C02"): (
        "Age convention: anniversary built from the year difference ('25-09-25') instead of birth year + 25; "
        "strftime returns NULL on that string, no row, so 0", "anniversary from year difference, 0"),
    ("dots-studio/dots-3-note-preview:free", "C09"): (
        "Question misread: keeps customers whose birth_date equals '2026-09-26', the reference date itself; "
        "no such customer, so 0", "birth date = reference date, 0"),
    ("dots-studio/dots-3-note-preview:free", "C10"): (
        "Age convention: keeps year difference = 25 with birthday reached only; misses year difference = 26 "
        "with birthday not reached (still 25). Same wrong value 119410 as qwen/qwen3.8-27b",
        "misses year diff 26 before birthday"),
    ("dots-studio/dots-3-note-preview:free", "C11"): (
        "SQL error: the answer keeps a draft expression and reasoning in SQL comments before the correct "
        "condition, syntax error near \"date\"", "draft expression left in SQL"),
    ("dots-studio/dots-3-note-preview:free", "C15"): (
        "Age convention: year difference = 25 AND birth month-day <= '09-25' keeps only customers born in 2001; "
        "misses those born in 2000 after 09-25, who are 25", "only born 2001 before 09-25"),
    ("dots-studio/dots-3-note-preview:free", "C19"): (
        "SQL error: misplaced parenthesis, CAST((strftime('%Y','2026-09-25') AS INTEGER), syntax error near \"AS\"",
        "misplaced parenthesis in CAST"),
}
ACCESS = ("Access failure, not a wrong answer: HTTP 429 on both attempts, Groq free-tier limit of 1000 output "
          "tokens per minute (OTPM); no SQL returned, retry budget used")


def read(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def merge_traces():
    header, merged = None, []
    for op in OPERATORS:
        fields, rows = read(HERE / f"traces-{op}.csv")
        assert header in (None, fields), f"traces-{op}.csv: header differs"
        header = fields
        merged += rows
    fingerprints = defaultdict(set)
    for row in merged:
        fingerprints[row["case_id"]].add(row["prompt_sha256"])
    assert all(len(s) == 1 for s in fingerprints.values()), "a question has several prompt fingerprints"
    write(HERE / "traces-td1.csv", header, merged)
    print(f"traces-td1.csv: {len(merged)} attempts from {len(OPERATORS)} files, one prompt fingerprint per question")


def final_cells():
    """operator -> model -> case -> last attempt row, and per-operator raw rows."""
    finals, raw = {}, {}
    for op in OPERATORS:
        _, rows = read(HERE / f"traces-{op}.csv")
        raw[op] = rows
        last = {}
        for row in rows:  # call order: the last line of a cell is its final attempt
            last[row["case_id"]] = row
        finals[op] = last
    return finals, raw


def explanation(row):
    attempt = f"last attempt {row['attempts']}"
    if row["verdict"] == "correct":
        return f"Value equals reference; {attempt}" + (" (first attempt HTTP 429)" if row["attempts"] == "2" else "")
    if row["verdict"] == "not_executed":
        return f"{ACCESS}; {attempt}"
    return f"{CAUSES[(row['model_requested'], row['case_id'])][0]}; {attempt}"


def complete_comparison(finals):
    path = HERE / "model-question-comparison-en.csv"
    fields, rows = read(path)
    present = {(r["model_id"], r["case_id"]) for r in rows}
    added = 0
    for op in OPERATORS:
        for case_id in CASES:
            t = finals[op][case_id]
            model_id = f"{t['provider']}:{t['model_requested']}"
            if (model_id, case_id) in present:
                continue
            rows.append({"case_id": case_id, "model_id": model_id, "trace_file": f"traces-{op}.csv",
                         "cell_id": t["cell_id"], "nature": t["nature"], "status": t["verdict"],
                         "value_cents": t["value"], "reference_cents": t["reference"],
                         "explanation": explanation(t)})
            added += 1
    write(path, fields, rows)
    print(f"model-question-comparison-en.csv: {added} rows added, {len(rows)} rows in total")
    return rows


def family_text(op, last, cases):
    counts = Counter(last[c]["verdict"] for c in cases)
    ok = [c for c in cases if last[c]["verdict"] == "correct"]
    wrong = [c for c in cases if last[c]["verdict"] in ("incorrect", "sql_invalid", "sql_rejected")]
    access = [c for c in cases if last[c]["verdict"] in ("not_executed", "access_error")]
    evaluated = len(cases) - len(access)
    parts = [f"{len(ok)}/{evaluated} correct"]
    if wrong:
        model = last[cases[0]]["model_requested"]
        parts[0] += " (" + "; ".join(f"{c} {last[c]['verdict']}: {CAUSES[(model, c)][1]}" for c in wrong) + ")"
    parts.append(f"{len(access)} access failures" + (f" ({' '.join(access)}: HTTP 429 twice)" if access else ""))
    parts.append(f"{counts['not_executed']} not executed (traces-{op}.csv)")
    return "; ".join(parts)


def complete_summary(finals, raw):
    path = HERE / "five-model-summary-en.csv"
    fields, rows = read(path)
    by_model = {r["model_id"]: r for r in rows}

    # Row B: Groq Developer price of the exact same model is documented in methode-cout-en.md
    b = by_model["openai/gpt-oss-20b"]
    b.update(paid_route_same_model="groq openai/gpt-oss-20b, Groq Developer plan (billed per token)",
             input_usd_per_million="0.075", output_usd_per_million="0.3", price_date="2026-10-05",
             price_source="methode-cout-en.md, step 2 (https://console.groq.com/docs/models, checked 2026-10-05)")

    # Row C: the template still named the 28 September model; the 14 October selection and the traces use Cohere
    template_c = by_model.pop("inclusionai/ling-3.0-flash-sante:free", None)
    if template_c is not None:
        template_c["model_id"] = "cohere/north-mini-code:free"
        by_model["cohere/north-mini-code:free"] = template_c
    b["limits"] = b["limits"].replace("; no documented paid price",
                                      "; paid price: Groq Developer route of the same model (methode-cout-en.md)")

    fixed = {
        "C": dict(public_index="N/A", index_date="N/A",
                  index_source="N/A: model absent from portefeuille-modeles-2026-09-28.csv (snapshot before the 14 October selection)",
                  paid_route_same_model="N/A: OpenRouter catalogue checked 2026-10-14 documents a free route only, no matching paid route (methode-cout-en.md)",
                  input_usd_per_million="N/A", output_usd_per_million="N/A", price_date="2026-10-14",
                  price_source="methode-cout-en.md, step 2 (https://openrouter.ai/api/v1/models)"),
        "D": dict(public_index="33.7", index_date="2026-09-28",
                  index_source="portefeuille-modeles-2026-09-28.csv (aggregator public rankings, recorded 2026-09-28)",
                  paid_route_same_model="groq qwen/qwen3.8-27b, Groq Developer plan (billed per token)",
                  input_usd_per_million="0.8", output_usd_per_million="4", price_date="2026-10-05",
                  price_source="methode-cout-en.md, step 2 (https://console.groq.com/docs/models, checked 2026-10-05)"),
        "E": dict(public_index="N/A", index_date="N/A",
                  index_source="N/A: model absent from portefeuille-modeles-2026-09-28.csv (snapshot before the 14 October selection)",
                  paid_route_same_model="N/A: OpenRouter catalogue checked 2026-10-14 documents a free route only, no matching paid route (methode-cout-en.md)",
                  input_usd_per_million="N/A", output_usd_per_million="N/A", price_date="2026-10-14",
                  price_source="methode-cout-en.md, step 2 (https://openrouter.ai/api/v1/models)"),
    }
    limits = {
        "C": ("One run per cell at temperature 0 on {day}; no variability measured; the template row named "
              "inclusionai/ling-3.0-flash-sante:free (28 September list), replaced by the 14 October required model "
              "actually called; 2 sql_invalid answers (C09, C10)"),
        "D": ("One run per cell at temperature 0 on {day}; Groq Free limit of 1000 output tokens per minute "
              "(OTPM) reached with a 3 s pause: 6 HTTP 429 over 4 cells (C16, C18, C19, C20), "
              "C16 and C20 not executed after two 429, so 18 cells evaluated; "
              "no variability measured"),
        "E": ("One run per cell at temperature 0 on {day}; no variability measured; slowest model "
              "(mean latency {latency} ms); 2 sql_invalid answers (C11, C19)"),
    }
    for op in "CDE":
        last, attempts = finals[op], raw[op]
        model = last["C01"]["model_requested"]
        row = by_model[model]
        day = min(r["date_utc"] for r in attempts)[:10]
        retries = sum(r["attempts"] == "2" for r in attempts)
        native = {r["cost_native"] for r in attempts}
        latencies = [float(r["latency_ms"]) for r in attempts if r["http_status"] == "200" and r["latency_ms"]]
        plan = ("Groq Free plan" if last["C01"]["provider"] == "groq"
                else "OpenRouter free route (:free, max_price 0)")
        cost = "native cost 0 on every call" if native == {"0"} else "no native cost returned"
        row.update(fixed[op])
        row["access_used"] = (f"{plan}, personal key of member {op}; 20 cells, {len(attempts)} real calls on {day}, "
                              f"{retries} retries; {cost}")
        for family, cases in FAMILIES.items():
            row[family] = family_text(op, last, cases)
        total = sum(last[c]["verdict"] == "correct" for c in CASES)
        row["combined_results"] += f"; combined questions counted only here, not in the single-family views; total {total}/20"
        row["trace_files"] = f"traces-{op}.csv; state-{op}.jsonl"
        row["limits"] = limits[op].format(day=day, latency=round(sum(latencies) / len(latencies)))
    write(path, fields, rows)  # rows are updated in place: order A..E of the template is kept
    print("five-model-summary-en.csv: rows C, D, E filled; row B paid price set from methode-cout-en.md")


def pivot(finals):
    short = {"correct": "ok", "incorrect": "X", "sql_invalid": "inv", "sql_rejected": "rej",
             "not_executed": "429", "access_error": "acc"}
    rows = []
    for op in OPERATORS:
        last = finals[op]
        model = f"{last['C01']['provider']}:{last['C01']['model_requested']}"
        row = {"operator": op, "model_id": model}
        row.update({c: last[c]["verdict"] for c in CASES})
        ok = sum(last[c]["verdict"] == "correct" for c in CASES)
        row["correct"] = f"{ok}/20"
        rows.append(row)
        print(f"{op} {model:<48} " + " ".join(f"{short[last[c]['verdict']]:>3}" for c in CASES) + f"  {ok}/20")
    write(HERE / "model-question-pivot-td1.csv", ["operator", "model_id"] + CASES + ["correct"], rows)
    print(" " * 51 + " ".join(f"{c[1:]:>3}" for c in CASES))


def main():
    merge_traces()
    finals, raw = final_cells()
    complete_comparison(finals)
    complete_summary(finals, raw)
    pivot(finals)


if __name__ == "__main__":
    main()
