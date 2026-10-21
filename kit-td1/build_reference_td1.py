"""Build reference-td1.csv: twenty reference queries, executed and independently checked.

Written with coding assistance (Claude), disclosed; every query and value is checked here
by two computations that share no code with the reference SQL:

1. reference: the SQL stored in reference-td1.csv, run on data/boutique.sqlite opened read-only;
2. check A: pure Python on the CSV files (csv + datetime, no SQL, own age function);
3. check B: a second SQL formulation on the base (age from year difference corrected by
   month-day, products and periods written with other operators).

The file is written only if the three values agree for all twenty questions.

Conventions (consigne-etudiante section 1):
- period "from S to E": date >= S AND date < E (closed left, open right);
- completed age 25 on day D: 25th anniversary <= D < 26th anniversary (month and day count);
  "at the time of the order": D is the calendar day of the order timestamp;
- revenue excluding VAT: SUM(quantity_product * price), integer cents;
- 0, not NULL, when nothing matches.
"""
import csv
import hashlib
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "reference-td1.csv"

BASE = ("SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents "
        "FROM orders o JOIN product p ON p.product_id = o.product_id")
WITH_CUSTOMER = BASE + " JOIN customers c ON c.customer_id = o.customer_id"


def period(start, end):
    return f"o.date >= '{start}' AND o.date < '{end}'"


def age25_on(day):
    return f"date(c.birth_date, '+25 years') <= '{day}' AND date(c.birth_date, '+26 years') > '{day}'"


AGE25_AT_ORDER = ("date(c.birth_date, '+25 years') <= date(o.date) "
                  "AND date(c.birth_date, '+26 years') > date(o.date)")


def products(*ids):
    return "o.product_id IN (" + ", ".join(f"'{i}'" for i in ids) + ")"


def query(*conditions):
    needs_customer = any("c." in c for c in conditions)
    sql = WITH_CUSTOMER if needs_customer else BASE
    return sql + (" WHERE " + " AND ".join(conditions) if conditions else "")


# Each case: reference SQL + parameters for the independent checks.
# params: start/end (period), age_day (age on a reference date), at_order (age at order), products
CASES = {
    "C01": dict(start="2026-03-01 00:00:00", end="2026-06-01 00:00:00"),
    "C02": dict(age_day="2026-09-25"),
    "C03": dict(products=("a", "b", "c"), start="2026-01-01 00:00:00", end="2026-07-01 00:00:00"),
    "C04": dict(start="2026-01-01 00:00:00", end="2026-10-01 00:00:00"),
    "C05": dict(start="2026-06-01 00:00:00", end="2026-06-02 00:00:00"),
    "C06": dict(start="2025-01-01 00:00:00", end="2026-01-01 00:00:00"),
    "C07": dict(start="2026-05-31 00:00:00", end="2026-06-01 00:00:00"),
    "C08": dict(age_day="2026-09-24"),
    "C09": dict(age_day="2026-09-26"),
    "C10": dict(at_order=True),
    "C11": dict(age_day="2026-12-01"),
    "C12": dict(products=("a", "b", "c")),
    "C13": dict(products=("a", "c"), start="2026-04-01 00:00:00", end="2026-05-01 00:00:00"),
    "C14": dict(products=("a", "b", "c"), start="2026-10-01 00:00:00", end="2026-12-01 00:00:00"),
    "C15": dict(start="2026-03-01 00:00:00", end="2026-06-01 00:00:00", age_day="2026-09-25"),
    "C16": dict(products=("a", "b", "c"), age_day="2026-09-25"),
    "C17": dict(products=("a", "b", "c"), start="2026-01-01 00:00:00", end="2026-07-01 00:00:00",
                age_day="2026-09-25"),
    "C18": dict(start="2026-05-01 00:00:00", end="2026-06-01 00:00:00", at_order=True),
    "C19": dict(products=("d",), start="2026-09-01 00:00:00", end="2026-10-01 00:00:00",
                age_day="2026-09-25"),
    "C20": dict(start="2026-06-01 00:00:00", end="2026-09-01 00:00:00"),
}


def reference_sql(p):
    conditions = []
    if "start" in p:
        conditions.append(period(p["start"], p["end"]))
    if "age_day" in p:
        conditions.append(age25_on(p["age_day"]))
    if p.get("at_order"):
        conditions.append(AGE25_AT_ORDER)
    if "products" in p:
        conditions.append(products(*p["products"]))
    return query(*conditions)


def check_b_sql(p):
    """Second SQL formulation: age = year difference - (month-day not reached yet)."""
    def age(day_expr):
        return (f"(CAST(strftime('%Y', {day_expr}) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER)"
                f" - (strftime('%m-%d', {day_expr}) < strftime('%m-%d', c.birth_date))) = 25")
    where = []
    if "start" in p:
        where.append(f"NOT (o.date < '{p['start']}') AND o.date < '{p['end']}'")
    if "age_day" in p:
        where.append(age(f"'{p['age_day']}'"))
    if p.get("at_order"):
        where.append(age("substr(o.date, 1, 10)"))
    if "products" in p:
        where.append("(" + " OR ".join(f"o.product_id = '{i}'" for i in p["products"]) + ")")
    return ("SELECT IFNULL(SUM(o.quantity_product * (SELECT price FROM product WHERE product_id = o.product_id)), 0) "
            "FROM orders o LEFT JOIN customers c USING (customer_id)"
            + (" WHERE " + " AND ".join(where) if where else ""))


def completed_age(birth: date, day: date) -> int:
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def check_a_python(p, orders, prices, births):
    total = 0
    start = datetime.fromisoformat(p["start"]) if "start" in p else None
    end = datetime.fromisoformat(p["end"]) if "end" in p else None
    age_day = date.fromisoformat(p["age_day"]) if "age_day" in p else None
    for line in orders:
        when = datetime.strptime(line["date"], "%Y-%m-%d %H:%M:%S")
        if start is not None and not (start <= when < end):
            continue
        birth = births[line["customer_id"]]
        if age_day is not None and completed_age(birth, age_day) != 25:
            continue
        if p.get("at_order") and completed_age(birth, when.date()) != 25:
            continue
        if "products" in p and line["product_id"] not in p["products"]:
            continue
        total += int(line["quantity_product"]) * prices[line["product_id"]]
    return total


def verify_fingerprints():
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["csv_sha256"].items():
        actual = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
        assert actual == expected, f"{name}: sha256 differs from manifest"
    actual = hashlib.sha256((DATA / "boutique.sqlite").read_bytes()).hexdigest()
    assert actual == manifest["sqlite_file_sha256"], "boutique.sqlite: sha256 differs from manifest"


def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    verify_fingerprints()
    orders = read_csv("orders.csv")
    prices = {r["product_id"]: int(r["price"]) for r in read_csv("product.csv")}
    births = {r["customer_id"]: date.fromisoformat(r["birth_date"]) for r in read_csv("customers.csv")}

    db = sqlite3.connect(f"file:{(DATA / 'boutique.sqlite').as_posix()}?mode=ro", uri=True)
    rows, failures = [], []
    for case_id, p in CASES.items():
        sql = reference_sql(p)
        cursor = db.execute(sql)
        result = cursor.fetchall()
        assert len(result) == 1 and len(result[0]) == 1, f"{case_id}: not one row / one column"
        assert cursor.description[0][0] == "revenue_cents", f"{case_id}: column name"
        value = result[0][0]
        b = db.execute(check_b_sql(p)).fetchone()[0]
        a = check_a_python(p, orders, prices, births)
        status = "OK" if value == a == b and isinstance(value, int) else "MISMATCH"
        if status != "OK":
            failures.append(case_id)
        print(f"{case_id}  sql={value:>9}  python_csv={a:>9}  sql_alt={b:>9}  {status}")
        rows.append({"case_id": case_id, "sql": sql, "revenue_cents": value})
    db.close()

    if failures:
        raise SystemExit(f"Not written: mismatch on {failures}")
    with open(OUT, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "sql", "revenue_cents"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n{OUT.name} written: {len(rows)} rows, all three computations agree.")


if __name__ == "__main__":
    main()
