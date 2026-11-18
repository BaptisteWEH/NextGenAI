#!/usr/bin/env python3
"""TD 2, Pair C: exact TD 1 rates per question family, read from the 100 cells.

No model call. Everything is recomputed from the TD 1 files:
  ../TD1/questions-td1.json            question id -> type
  ../TD1/model-question-comparison-en.csv  one row per (model, question), last attempt

For each family it prints, per model, correct / cells with the failing cells, and
what two quorums would have decided on the same cells:
  - 2-of-3 on the fixed panel of atelier-vote.py (gpt-oss-120b, north-mini-code, qwen3.8-27b)
  - 3-of-5 on the five TD 1 models

The small vote below follows the contract of Step 1 (failed calls stay in n without a
vote, strict majority, abstain when no value reaches k). It is only used here to read
the TD 1 cells; the graded implementation is Pair A's vote_k_sur_n.

Usage: python3 pair_c_family_rates.py [--csv family-rates-td2.csv]
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

TD1 = Path(__file__).resolve().parent.parent / "TD1"

FAMILY_OF_TYPE = {
    "period": "F1",
    "age on a reference date": "F2",
    "age at the time of the order": "F2b",
    "product list": "F3",
}
FAMILY_ORDER = ["F1", "F2", "F2b", "F3", "combined"]

SHORT = {
    "groq:openai/gpt-oss-120b": "gpt-oss-120b",
    "groq:openai/gpt-oss-20b": "gpt-oss-20b",
    "openrouter:cohere/north-mini-code:free": "north-mini-code",
    "groq:qwen/qwen3.8-27b": "qwen3.8-27b",
    "openrouter:dots-studio/dots-3-note-preview:free": "dots-3-note",
}
FIXED_PANEL = ["gpt-oss-120b", "north-mini-code", "qwen3.8-27b"]


def family(question_type):
    if " + " in question_type:
        return "combined"
    return FAMILY_OF_TYPE[question_type]


def vote(values, k):
    """values: one entry per panel member, None when the call failed or the SQL was invalid."""
    n = len(values)
    if not n // 2 < k <= n:
        raise ValueError(f"k={k} is not a strict majority of n={n}")
    counts = Counter(v for v in values if v is not None)
    if counts:
        value, votes = counts.most_common(1)[0]
        if votes >= k:
            return value
    return None


def load():
    questions = json.loads((TD1 / "questions-td1.json").read_text(encoding="utf-8"))["questions"]
    fam = {q["id"]: family(q["type"]) for q in questions}
    cells = {}
    with open(TD1 / "model-question-comparison-en.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            value = int(row["value_cents"]) if row["value_cents"] else None
            cells[(SHORT[row["model_id"]], row["case_id"])] = {
                "status": row["status"], "value": value, "reference": int(row["reference_cents"])}
    return fam, cells


def quorum_outcome(cells, case, panel, k):
    values = [cells[(m, case)]["value"] if cells[(m, case)]["status"] in ("correct", "incorrect")
              else None for m in panel]
    decided = vote(values, k)
    if decided is None:
        return "abstain"
    return "right" if decided == cells[(panel[0], case)]["reference"] else f"WRONG ({decided})"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", help="also write the per-model rates to this CSV file")
    args = parser.parse_args()
    fam, cells = load()
    models = list(SHORT.values())
    rows = []
    for f in FAMILY_ORDER:
        cases = sorted(c for c, x in fam.items() if x == f)
        print(f"\n== {f}: {len(cases)} questions ({' '.join(cases)}) ==")
        total_ok = 0
        for m in models:
            ok = [c for c in cases if cells[(m, c)]["status"] == "correct"]
            bad = [f"{c}:{cells[(m, c)]['status']}" for c in cases if c not in ok]
            total_ok += len(ok)
            print(f"  {m:16s} {len(ok)}/{len(cases)}  {' '.join(bad) or '-'}")
            rows.append({"family": f, "model": m, "correct": len(ok), "cells": len(cases),
                         "rate": f"{len(ok)}/{len(cases)}", "cases": " ".join(cases),
                         "not_correct": " ".join(bad)})
        print(f"  family total     {total_ok}/{len(cases) * len(models)}")
        q23 = {c: quorum_outcome(cells, c, FIXED_PANEL, 2) for c in cases}
        q35 = {c: quorum_outcome(cells, c, models, 3) for c in cases}
        print("  2-of-3 fixed panel: " + " ".join(f"{c}={v}" for c, v in q23.items()))
        print("  3-of-5 all models:  " + " ".join(f"{c}={v}" for c, v in q35.items()))
    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
