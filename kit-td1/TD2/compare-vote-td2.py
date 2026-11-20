#!/usr/bin/env python3
"""TD 2, Pair A: fixed 2-of-3 panel vs 3-of-5 quorum on the twenty TD 1 questions.

Only stored traces are used (no network). The vote is decided FIRST by
Orchestrateur.vote_k_sur_n; the reference is compared afterwards.

    python3 TD2/compare-vote-td2.py                                   # from kit-td1/: markdown table + differences
    python3 TD2/compare-vote-td2.py --csv TD2/vote-comparison-td2.csv
"""
import argparse, csv, importlib.util, sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
KIT = HERE.parent                       # kit-td1/: shared skeleton
TD1 = KIT / "TD1"                       # stored TD 1 traces and reference
PANEL3 = [("groq", "openai/gpt-oss-120b"), ("openrouter", "cohere/north-mini-code:free"), ("groq", "qwen/qwen3.8-27b")]
PANEL5 = PANEL3 + [("groq", "openai/gpt-oss-20b"), ("openrouter", "dots-studio/dots-3-note-preview:free")]
SHORT = {"openai/gpt-oss-120b": "120B", "cohere/north-mini-code:free": "Cohere", "qwen/qwen3.8-27b": "Qwen",
         "openai/gpt-oss-20b": "20B", "dots-studio/dots-3-note-preview:free": "Dots"}


def load_vote():
    spec = importlib.util.spec_from_file_location("sk", KIT / "skeleton-multi-llm-en.py")
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
    return lambda props, k: mod.Orchestrateur.vote_k_sur_n(None, props, k)


def last_attempts(rows, case):
    """Last attempt of each model on `case`: last CSV row of its block, checked against date_utc."""
    best = {}
    for row in rows:
        if row["case_id"] == case and row["nature"] == "real":
            key = (row["provider"], row["model_requested"])
            if key not in best or row["date_utc"] >= best[key]["date_utc"]:
                best[key] = row
    return best


def proposals(best, panel):
    out = []
    for provider, model in panel:
        row = best.get((provider, model), {})
        value = row.get("value", "")
        # Execution status only: a query that did not run (HTTP 429 -> not_executed, or
        # sql_invalid) stays in n without a vote. The correctness label is never used.
        valid = bool(row) and row.get("verdict") not in {"not_executed", "sql_invalid"} and value not in {None, ""}
        out.append(SimpleNamespace(provider=provider, model_requested=model,
                                   value=int(value) if valid else None, verdict="executed" if valid else "error"))
    return out


def describe(props):
    return ", ".join(f"{SHORT[p.model_requested]}={p.value if p.value is not None else '×'}" for p in props)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--csv", type=Path); args = ap.parse_args()
    vote = load_vote()
    rows = list(csv.DictReader((TD1 / "traces-td1.csv").open(encoding="utf-8", newline="")))
    refs = {r["case_id"]: int(r["revenue_cents"]) for r in csv.DictReader((TD1 / "reference-td1.csv").open(encoding="utf-8"))}
    table = []
    for i in range(1, 21):
        case = f"C{i:02d}"
        best = last_attempts(rows, case)
        p3, p5 = proposals(best, PANEL3), proposals(best, PANEL5)
        d3, d5 = vote(p3, 2), vote(p5, 3)   # decided without the reference
        ref = refs[case]
        def status(d):
            if not d["consensus"]: return "abstain"
            return "OK" if d["value"] == ref else "WRONG"
        table.append(dict(case=case, ref=ref, votes3=describe(p3), d3=d3, s3=status(d3),
                          votes5=describe(p5), d5=d5, s5=status(d5)))
    fmt = lambda d: f"{d['value']} ({d['votes']}/{{n}})" if d["consensus"] else f"abstain (max {d['votes']})"
    print("| Q | Reference | 2-of-3 decision | 2-of-3 vs ref | 3-of-5 decision | 3-of-5 vs ref | Changes? |")
    print("|---|---:|---|---|---|---|---|")
    for t in table:
        a = fmt(t["d3"]).format(n=3); b = fmt(t["d5"]).format(n=5)
        changed = "yes" if (t["d3"]["consensus"], t["d3"]["value"]) != (t["d5"]["consensus"], t["d5"]["value"]) else "no"
        print(f"| {t['case']} | {t['ref']} | {a} | {t['s3']} | {b} | {t['s5']} | {changed} |")
    for name, key in (("2-of-3", "s3"), ("3-of-5", "s5")):
        c = [t[key] for t in table]
        print(f"\n{name}: OK={c.count('OK')} WRONG={c.count('WRONG')} abstain={c.count('abstain')}")
    print("\nVotes detail (x = no vote):")
    for t in table:
        print(f"{t['case']}  3: [{t['votes3']}]   5: [{t['votes5']}]   ref={t['ref']}")
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as h:
            w = csv.writer(h); w.writerow(["case", "reference", "panel3_votes", "d3_consensus", "d3_value", "d3_votes", "d3_vs_ref",
                                          "panel5_votes", "d5_consensus", "d5_value", "d5_votes", "d5_vs_ref"])
            for t in table:
                w.writerow([t["case"], t["ref"], t["votes3"], t["d3"]["consensus"], t["d3"]["value"], t["d3"]["votes"], t["s3"],
                            t["votes5"], t["d5"]["consensus"], t["d5"]["value"], t["d5"]["votes"], t["s5"]])


if __name__ == "__main__":
    main()
