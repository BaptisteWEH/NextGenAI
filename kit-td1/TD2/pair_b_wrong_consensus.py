#!/usr/bin/env python3
"""TD 2 - Step 2 (Pair B): Wrong consensus & shared wrong value verification.

Reads `../TD1/traces-td1.csv`, `../TD1/reference-td1.csv` and `../data/boutique.sqlite` (read-only).
No network call, no API key.

1. Scans all 100 cells of the TD 1 batch across the 5 models to find every question
   where at least two models return the same wrong value (`verdict == 'incorrect'`).
2. Evaluates both the fixed 2-of-3 panel (`atelier-vote.py`) and the 3-of-5 panel
   (all 5 TD 1 models) on each identified case (`C02` and `C10`). Uses Pair A's
   `Orchestrateur.vote_k_sur_n` when available, with the local contract implementation
   as fallback, and verifies they agree.
3. Executes the reference SQL, the faulty model SQL queries and the delta diagnostic
   SQL queries on `data/boutique.sqlite` for:
   - Case 1 (Real batch, wrong consensus in 3-of-5): C02 (shared wrong value 0 vs reference 590320 cents)
   - Case 2 (Real batch, shared wrong value refused by both quorums): C10 (119410 vs reference 558980 cents)
   - Instructor-supplied historical pilot case: DEMO-SQL-C11 (shared wrong value 0 vs reference 446690 cents)
4. Executes the DEMO-VOTE one-row toy table boundary illustration (`>` vs `>=`) using
   synthetic proposal labels (`synthetic:P1`, `synthetic:P2`, `synthetic:P3`).
5. Demonstrates a targeted binary-bitmask canary check (100, 200, 400, 800 cents),
   calibrated per reference date (`2026-09-25` for C02/C10 and `2026-12-01` for DEMO-SQL-C11).

Usage from `kit-td1/TD2/` (or from repo root):
    python3 pair_b_wrong_consensus.py --export-csv
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parent
DB_PATH = KIT_ROOT / "data" / "boutique.sqlite"
TRACES_PATH = KIT_ROOT / "TD1" / "traces-td1.csv"
REF_PATH = KIT_ROOT / "TD1" / "reference-td1.csv"

PANEL_3 = [
    ("groq", "openai/gpt-oss-120b"),
    ("openrouter", "cohere/north-mini-code:free"),
    ("groq", "qwen/qwen3.8-27b"),
]

PANEL_5 = [
    ("groq", "openai/gpt-oss-120b"),
    ("groq", "openai/gpt-oss-20b"),
    ("openrouter", "cohere/north-mini-code:free"),
    ("groq", "qwen/qwen3.8-27b"),
    ("openrouter", "dots-studio/dots-3-note-preview:free"),
]


def connect_ro(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only = 1")
    conn.row_factory = sqlite3.Row
    return conn


def run_k_of_n_fallback(proposals: list[dict], k: int) -> dict:
    """Strict majority k-of-n vote matching the TD 2 Step 1 contract."""
    n = len(proposals)
    if not (n // 2 < k <= n):
        raise ValueError(f"k={k} is not a strict majority of n={n}")
    seen_models = set()
    votes_by_val: dict[int, list[str]] = defaultdict(list)
    for p in proposals:
        pair = (p["provider"], p["model_requested"])
        if pair in seen_models:
            raise ValueError(f"Duplicate provider/model pair: {pair}")
        seen_models.add(pair)
        if p["verdict"] == "executed" and p["value"] is not None:
            votes_by_val[int(p["value"])].append(f"{pair[0]}:{pair[1]}")

    if not votes_by_val:
        return {"consensus": False, "value": None, "votes": 0, "models": []}

    best_val, best_models = max(votes_by_val.items(), key=lambda item: len(item[1]))
    max_votes = len(best_models)
    if max_votes >= k:
        return {
            "consensus": True,
            "value": best_val,
            "votes": max_votes,
            "models": best_models,
        }
    return {"consensus": False, "value": None, "votes": max_votes, "models": []}


def run_k_of_n(proposals: list[dict], k: int) -> dict:
    """Use Pair A's Orchestrateur.vote_k_sur_n if available in TD2 or kit root, else fallback."""
    expected = run_k_of_n_fallback(proposals, k)
    for candidate in (HERE / "skeleton-multi-llm-en.py", KIT_ROOT / "skeleton-multi-llm-en.py"):
        if not candidate.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location("pair_a_skeleton", candidate)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            ns_props = [
                SimpleNamespace(
                    provider=p["provider"],
                    model_requested=p["model_requested"],
                    value=p["value"],
                    verdict=p["verdict"],
                )
                for p in proposals
            ]
            res = module.Orchestrateur.vote_k_sur_n(None, ns_props, k)
            assert res == expected, f"Mismatch between Pair A vote_k_sur_n ({res}) and contract ({expected})"
            return res
        except NotImplementedError:
            continue
    return expected


def build_panel_proposals(latest_by_cell: dict, case_id: str, panel: list[tuple[str, str]]) -> list[dict]:
    proposals = []
    for provider, model in panel:
        row = latest_by_cell.get((provider, model, case_id), {})
        val_str = row.get("value", "")
        valid = row.get("verdict") in {"correct", "incorrect"} and val_str not in {None, ""}
        proposals.append({
            "provider": provider,
            "model_requested": model,
            "value": int(val_str) if valid else None,
            "verdict": "executed" if valid else "error",
            "raw_verdict": row.get("verdict", "missing"),
            "csv_line": row.get("_csv_line"),
        })
    return proposals


def build_canary_db(ref_date: str, k1_birth: str, k2_birth: str, k3_birth: str, k4_birth: str) -> sqlite3.Connection:
    """Create a 4-row binary-bitmask canary database calibrated for a specific reference date."""
    canary = sqlite3.connect(":memory:")
    canary.executescript(f"""
        CREATE TABLE product (product_id TEXT PRIMARY KEY, price INTEGER NOT NULL);
        CREATE TABLE customers (customer_id TEXT PRIMARY KEY, insert_date TEXT NOT NULL, birth_date TEXT NOT NULL);
        CREATE TABLE orders (date TEXT NOT NULL, order_id TEXT NOT NULL, customer_id TEXT NOT NULL, product_id TEXT NOT NULL, quantity_product INTEGER NOT NULL);
        INSERT INTO product VALUES ('a', 1);
        -- Bit 0 (100 cts) K1: turns 25 on ref_date (Cohort 1)     -> MUST INCLUDE
        -- Bit 1 (200 cts) K2: turns 26 day after ref_date (Coh 2) -> MUST INCLUDE
        -- Bit 2 (400 cts) K3: turns 26 on ref_date (aged 26)      -> MUST EXCLUDE
        -- Bit 3 (800 cts) K4: turns 25 day after ref_date (24)    -> MUST EXCLUDE
        INSERT INTO customers VALUES
            ('K1', '2025-01-01 00:00:00', '{k1_birth}'),
            ('K2', '2025-01-01 00:00:00', '{k2_birth}'),
            ('K3', '2025-01-01 00:00:00', '{k3_birth}'),
            ('K4', '2025-01-01 00:00:00', '{k4_birth}');
        INSERT INTO orders VALUES
            ('{ref_date} 12:00:00', 'O1', 'K1', 'a', 100),
            ('{ref_date} 12:00:00', 'O2', 'K2', 'a', 200),
            ('{ref_date} 12:00:00', 'O3', 'K3', 'a', 400),
            ('{ref_date} 12:00:00', 'O4', 'K4', 'a', 800);
    """)
    return canary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-csv", action="store_true", help="Write delta-c02-td2.csv and delta-c10-td2.csv in TD2/")
    args = parser.parse_args()

    with TRACES_PATH.open(encoding="utf-8", newline="") as f:
        raw_rows = list(csv.DictReader(f))
    with REF_PATH.open(encoding="utf-8", newline="") as f:
        references = {r["case_id"]: r for r in csv.DictReader(f)}

    latest_by_cell = {}
    for line_no, r in enumerate(raw_rows, start=2):
        if r["nature"] == "real":
            r["_csv_line"] = line_no
            latest_by_cell[(r["provider"], r["model_requested"], r["case_id"])] = r

    print("=" * 78)
    print("1. SCAN OF ALL 100 TD 1 CELLS FOR SHARED WRONG VALUES (verdict = incorrect)")
    print("=" * 78)
    by_case = defaultdict(list)
    for (_, _, cid), r in latest_by_cell.items():
        by_case[cid].append(r)

    for cid in sorted(by_case.keys()):
        wrong_counts = Counter(r["value"] for r in by_case[cid] if r["verdict"] == "incorrect")
        shared = {val: cnt for val, cnt in wrong_counts.items() if cnt >= 2}
        if shared:
            ref_val = int(references[cid]["revenue_cents"])
            print(f"\nCase {cid} (independent reference = {ref_val} cents):")
            for val, cnt in shared.items():
                models = [
                    f"{r['provider']}:{r['model_requested']} (TD1/traces-td1.csv:L{r['_csv_line']})"
                    for r in by_case[cid]
                    if r["verdict"] == "incorrect" and r["value"] == val
                ]
                print(f"  Shared wrong value = {val} cents ({cnt}/5 models): {', '.join(models)}")

            p3 = build_panel_proposals(latest_by_cell, cid, PANEL_3)
            p5 = build_panel_proposals(latest_by_cell, cid, PANEL_5)
            res_2_of_3 = run_k_of_n(p3, 2)
            res_3_of_5 = run_k_of_n(p5, 3)
            print(f"  Fixed 2-of-3 panel (atelier-vote.py) -> {json.dumps(res_2_of_3)}")
            print(f"  Full  3-of-5 panel (all 5 TD1 models) -> {json.dumps(res_3_of_5)}")

    conn = connect_ro(DB_PATH)

    print("\n" + "=" * 78)
    print("2. DELTA DIAGNOSTIC SQL ON data/boutique.sqlite - CASE C02 (Real Batch)")
    print("=" * 78)
    q_c02_delta = """
    SELECT c.customer_id,
           c.birth_date,
           COUNT(o.order_id) AS order_lines,
           COALESCE(SUM(o.quantity_product * p.price), 0) AS customer_revenue_cents
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    JOIN product p ON p.product_id = o.product_id
    WHERE date(c.birth_date, '+25 years') <= '2026-09-25'
      AND date(c.birth_date, '+26 years') > '2026-09-25'
    GROUP BY c.customer_id, c.birth_date
    ORDER BY c.customer_id;
    """
    c02_rows = conn.execute(q_c02_delta).fetchall()
    for r in c02_rows:
        print(f"  {r['customer_id']} | birth_date={r['birth_date']} | lines={r['order_lines']:2d} | revenue={r['customer_revenue_cents']:6d} cents")
    c02_sum = sum(r["customer_revenue_cents"] for r in c02_rows)
    print(f"  TOTAL MISSED BY B, C, E = {c02_sum} cents (Reference = 590320, Shared wrong = 0, Delta = {590320 - 0})")
    assert c02_sum == 590320

    if args.export_csv:
        with (HERE / "delta-c02-td2.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["customer_id", "birth_date", "order_lines", "customer_revenue_cents", "status_in_B_C_E"])
            for r in c02_rows:
                w.writerow([r["customer_id"], r["birth_date"], r["order_lines"], r["customer_revenue_cents"], "missed_by_B_C_E"])

    print("\n" + "=" * 78)
    print("3. DELTA DIAGNOSTIC SQL ON data/boutique.sqlite - CASE C10 (Real Batch)")
    print("=" * 78)
    q_c10_delta = """
    SELECT c.customer_id,
           c.birth_date,
           MIN(date(o.date)) AS first_order_date,
           MAX(date(o.date)) AS last_order_date,
           (CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER)) AS year_diff,
           COUNT(o.order_id) AS order_lines,
           SUM(o.quantity_product * p.price) AS customer_revenue_cents,
           CASE
               WHEN (CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER)) = 25
                    AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)
               THEN 'COUNTED_BY_D_AND_E'
               ELSE 'MISSED_BY_D_AND_E'
           END AS status_in_faulty_queries
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN product p ON o.product_id = p.product_id
    WHERE date(c.birth_date, '+25 years') <= date(o.date)
      AND date(c.birth_date, '+26 years') > date(o.date)
    GROUP BY c.customer_id, c.birth_date, year_diff
    ORDER BY status_in_faulty_queries, c.customer_id;
    """
    c10_rows = conn.execute(q_c10_delta).fetchall()
    counted_sum = 0
    missed_sum = 0
    for r in c10_rows:
        print(
            f"  {r['customer_id']} | birth={r['birth_date']} | orders={r['first_order_date']}..{r['last_order_date']} "
            f"| year_diff={r['year_diff']} | lines={r['order_lines']:2d} | rev={r['customer_revenue_cents']:6d} | {r['status_in_faulty_queries']}"
        )
        if r["status_in_faulty_queries"] == "COUNTED_BY_D_AND_E":
            counted_sum += r["customer_revenue_cents"]
        else:
            missed_sum += r["customer_revenue_cents"]
    print(f"  Sum counted by D & E = {counted_sum} cents (matches shared wrong value 119410)")
    print(f"  Sum missed  by D & E = {missed_sum} cents (exact delta: 558980 - 119410 = {558980 - 119410})")
    print(f"  Total reference      = {counted_sum + missed_sum} cents (matches reference 558980)")
    assert counted_sum == 119410 and missed_sum == 439570

    if args.export_csv:
        with (HERE / "delta-c10-td2.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["customer_id", "birth_date", "first_order_date", "last_order_date", "year_diff", "order_lines", "customer_revenue_cents", "status_in_D_and_E"])
            for r in c10_rows:
                w.writerow([
                    r["customer_id"], r["birth_date"], r["first_order_date"], r["last_order_date"],
                    r["year_diff"], r["order_lines"], r["customer_revenue_cents"], r["status_in_faulty_queries"]
                ])

    print("\n" + "=" * 78)
    print("4. INSTRUCTOR-SUPPLIED HISTORICAL CASE: DEMO-SQL-C11 ON data/boutique.sqlite")
    print("=" * 78)
    q_m1 = """
    SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN product p ON o.product_id = p.product_id
    WHERE c.birth_date = '2001-12-01';
    """
    q_m2 = """
    SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN product p ON o.product_id = p.product_id
    WHERE CAST(strftime('%Y-%m-%d', '2026-12-01') AS TEXT) >= c.birth_date
      AND CAST(strftime('%Y-%m-%d', '2026-12-01', '+1 year') AS TEXT) <= c.birth_date;
    """
    v_m1 = conn.execute(q_m1).fetchone()["revenue_cents"]
    v_m2 = conn.execute(q_m2).fetchone()["revenue_cents"]
    print(f"  M1 (gpt-oss-20b historical pilot) result = {v_m1} cents")
    print(f"  M2 (north-mini-code historical pilot) result = {v_m2} cents")
    q_c11_delta = """
    SELECT c.customer_id,
           c.birth_date,
           COUNT(o.order_id) AS order_lines,
           COALESCE(SUM(o.quantity_product * p.price), 0) AS customer_revenue_cents
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    JOIN product p ON p.product_id = o.product_id
    WHERE date(c.birth_date, '+25 years') <= '2026-12-01'
      AND date(c.birth_date, '+26 years') > '2026-12-01'
    GROUP BY c.customer_id, c.birth_date
    ORDER BY c.customer_id;
    """
    c11_rows = conn.execute(q_c11_delta).fetchall()
    for r in c11_rows:
        print(f"  {r['customer_id']} | birth_date={r['birth_date']} | lines={r['order_lines']:2d} | revenue={r['customer_revenue_cents']:6d} cents")
    c11_sum = sum(r["customer_revenue_cents"] for r in c11_rows)
    print(f"  TOTAL MISSED BY M1 & M2 = {c11_sum} cents (Reference C11 = 446690, Shared wrong = 0, Delta = {446690 - 0})")
    assert v_m1 == 0 and v_m2 == 0 and c11_sum == 446690

    print("\n" + "=" * 78)
    print("5. MECHANISM ILLUSTRATION: DEMO-VOTE (One-row toy table, nature=simulation)")
    print("=" * 78)
    toy = sqlite3.connect(":memory:")
    toy.execute("CREATE TABLE sales (sale_date TEXT NOT NULL, amount_cents INTEGER NOT NULL);")
    toy.execute("INSERT INTO sales (sale_date, amount_cents) VALUES ('2026-01-01', 100);")
    v_wrong = toy.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM sales WHERE sale_date > '2026-01-01' AND sale_date < '2026-01-02';"
    ).fetchone()[0]
    v_right = toy.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) FROM sales WHERE sale_date >= '2026-01-01' AND sale_date < '2026-01-02';"
    ).fetchone()[0]
    # Constructed teaching proposals labeled synthetic:P1..P3, never mixed with real model outputs
    demo_proposals = [
        {"provider": "synthetic", "model_requested": "P1", "value": v_wrong, "verdict": "executed"},
        {"provider": "synthetic", "model_requested": "P2", "value": v_wrong, "verdict": "executed"},
        {"provider": "synthetic", "model_requested": "P3", "value": v_right, "verdict": "executed"},
    ]
    print(f"  Variant 1 (`sale_date >  '2026-01-01'`): {v_wrong} cents (excludes boundary sale on 2026-01-01)")
    print(f"  Variant 2 (`sale_date >= '2026-01-01'`): {v_right} cents (includes boundary sale on 2026-01-01)")
    print(f"  2-of-3 quorum on [{v_wrong}, {v_wrong}, {v_right}] -> {json.dumps(run_k_of_n(demo_proposals, 2))} vs reference = 100")

    print("\n" + "=" * 78)
    print("6. TARGETED CHECK: BINARY-BITMASK CANARY TEST (100, 200, 400, 800 cents)")
    print("=" * 78)
    canary_0925 = build_canary_db("2026-09-25", "2001-09-25", "2000-09-26", "2000-09-25", "2001-09-26")
    canary_1201 = build_canary_db("2026-12-01", "2001-12-01", "2000-12-02", "2000-12-01", "2001-12-02")

    bitmask_diagnosis = {
        300: "PASS (K1+K2 = 300: exact completed-age window)",
        0: "REJECT [0]: empty-set bug (all 4 boundary customers excluded)",
        100: "REJECT [K1 only = 100]: single-day or missed Cohort 2 (K2 born 26y ago before birthday)",
        600: "REJECT [K2+K3 = 600]: off-by-one birthday boundary (missed K1, included K3 aged 26)",
        1100: "REJECT [K1+K2+K4 = 1100]: missing lower age bound (included K4 aged 24)",
        1500: "REJECT [K1+K2+K3+K4 = 1500]: missing lower age bound (included all customers <= 25)",
    }

    print("  [Canary calibrated for reference/order date 2026-09-25: C02 & C10]")
    for label, cid, mod_key in [
        ("C02 Reference SQL", "C02", None),
        ("C02 B (gpt-oss-20b)", "C02", ("groq", "openai/gpt-oss-20b")),
        ("C02 C (north-mini-code)", "C02", ("openrouter", "cohere/north-mini-code:free")),
        ("C02 E (dots-3-note)", "C02", ("openrouter", "dots-studio/dots-3-note-preview:free")),
        ("C10 Reference SQL", "C10", None),
        ("C10 D (qwen3.8-27b)", "C10", ("groq", "qwen/qwen3.8-27b")),
        ("C10 E (dots-3-note)", "C10", ("openrouter", "dots-studio/dots-3-note-preview:free")),
    ]:
        sql_to_test = references[cid]["sql"] if mod_key is None else latest_by_cell[(mod_key[0], mod_key[1], cid)]["sql"]
        got = canary_0925.execute(sql_to_test).fetchone()[0]
        diag = bitmask_diagnosis.get(got, f"REJECT (got {got} != 300)")
        print(f"    {label:24s} -> canary={got:4d} -> {diag}")

    print("\n  [Canary calibrated for reference date 2026-12-01: DEMO-SQL-C11]")
    for label, sql_to_test in [
        ("C11 Reference SQL", references["C11"]["sql"]),
        ("C11 Pilot M1 (20b)", q_m1),
        ("C11 Pilot M2 (cohere)", q_m2),
    ]:
        got = canary_1201.execute(sql_to_test).fetchone()[0]
        diag = bitmask_diagnosis.get(got, f"REJECT (got {got} != 300)")
        print(f"    {label:24s} -> canary={got:4d} -> {diag}")


if __name__ == "__main__":
    main()
