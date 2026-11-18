#!/usr/bin/env python3
"""TD 2 and TD 3: read the decisions of a routing rule, then adapt it to your own.

Synthetic resources, no API call, no key.

Costs are fictional USD excluding tax per request, with a fixed token envelope.
Capability levels 1/2/3 describe eligibility for this exercise, not model IQ.
Quota availability is supplied as a scenario, not measured from a provider.

TD 2, Pair C (DIA3-3) adaptation
--------------------------------
The kit version is kept as choose_kit() so both rules can be replayed on the same
scenarios (--rule kit). The sub-group rule is choose(). What changed:

* RESOURCES are the routes we actually used in TD 1 (Groq and OpenRouter free tiers),
  plus the G1 senior model of the portfolio through a subscription and through a paid
  API. Each TD 1 route carries the cells it failed, per family.
* Eligibility comes from TD 1 when we have it: a TD 1 route is eligible on a family
  only if it was correct on every cell of that family. A route we never tested falls
  back on its portfolio level (G1 = level 3) and is never used alone for a payout
  (shadow only, Lecture 2).
* The check depends on the use (dashboard, customer, payout) and on the family, as
  written in routing-rule-td2.md. "none" only survives for a dashboard figure, on a
  family with no TD 1 error, served by a route that scored 100 % on it.
* Priority: a route validated in TD 1 that refills before the deadline is waited for
  before spending subscription allocation on an untested model. The kit order
  (subscription first) is kept when no validated route can come back in time.
* POLICY (pair-c-v1), applied by route(): at most 10 attempts per resource, one minute
  apart, then the next eligible route; a check that fails or times out means the value
  is not delivered. The policy id, the attempts and the check result are in every output.
* The quorum panel must have one model per maker (check_panel, run at start-up).

Every reason string quotes the TD 1 cells it relies on.

Cost envelope: 2,000 input tokens and 500 output tokens per request. The paid
senior route (claude-fable-5-1 via OpenRouter, 10 / 50 USD per million tokens)
costs 2000*10e-6 + 500*50e-6 = 0.045 USD. paid_route_usd is what the same request
would cost on the paid route of the same model once the free quota is gone; it is
only used to break ties between free routes.
"""
import argparse
import json

# TD 1 families (questions-td1.json). "difficulty" is the level an untested route needs:
# 1 when all five TD 1 models were right on every cell, 3 when TD 1 showed errors.
FAMILIES = {
    "F1": {"label": "period", "cases": "C01 C04 C05 C06 C07 C20",
           "td1": "29/30 cells correct, the missing one is an HTTP 429", "errors": False, "difficulty": 1},
    "F2": {"label": "completed age at a date", "cases": "C02 C08 C09 C11",
           "td1": "10/20 cells correct", "errors": True, "difficulty": 3},
    "F2b": {"label": "age at the time of the order", "cases": "C10",
            "td1": "2/5 cells correct", "errors": True, "difficulty": 3},
    "F3": {"label": "product list", "cases": "C03 C12 C13 C14",
           "td1": "20/20 cells correct", "errors": False, "difficulty": 1},
    "combined": {"label": "period, age and product combined", "cases": "C15 C16 C17 C18 C19",
                 "td1": "16/25 cells correct", "errors": True, "difficulty": 3},
}

# Versioned policy, copied into every decision so a trace says which rule produced it.
# Retry values are the ones of Lecture 2. A check that fails or times out blocks delivery.
POLICY = {
    "id": "pair-c-v1",
    "max_attempts_per_resource": 10,
    "minutes_between_attempts": 1,
    "after_max_attempts": "next eligible route, then defer or abstain",
    "check_failed_or_timeout": "no delivery, failure logged",
}

# Quorum panel: one vote per maker, so that two models of the same maker cannot
# carry a shared mistake (checked at start-up by check_panel).
PANEL_IDS = ["gpt-oss-120b#groq", "north-mini-code#openrouter", "qwen3.8-27b#groq"]

# Checks of routing-rule-td2.md, per family and use. The format check (integer euro
# cents, one row, read-only SQL) always runs and is not listed.
PANEL = "2-of-3 quorum on gpt-oss-120b, north-mini-code, qwen3.8-27b (three makers)"
REFERENCE = "reference: value must equal the validated query of the family, run by code"
CHECKS = {
    "F1": {"dashboard": "none", "customer": PANEL, "payout": REFERENCE + " + human review"},
    "F3": {"dashboard": "none", "customer": PANEL, "payout": REFERENCE + " + human review"},
    "F2": {"dashboard": PANEL, "customer": PANEL + " + " + REFERENCE,
           "payout": REFERENCE + " + human review"},
    "F2b": {"dashboard": REFERENCE, "customer": REFERENCE, "payout": REFERENCE + " + human review"},
    "combined": {"dashboard": PANEL + ", reference when it abstains", "customer": REFERENCE,
                 "payout": REFERENCE + " + human review"},
}
CHECK_EVIDENCE = {
    "F1": "no TD 1 error on F1, 2-of-3 and 3-of-5 right on all 6 cells",
    "F3": "no TD 1 error on F3, 2-of-3 and 3-of-5 right on all 4 cells",
    "F2": "2-of-3 right on C02 C08 C09 and abstains on C11; 3-of-5 accepts the wrong 0 on C02",
    "F2b": "both quorums abstain on C10 (558980 vs 119410)",
    "combined": "2-of-3 abstains on C15 C17 C19; only the two gpt-oss models (same maker) are 5/5",
}

RESOURCES = [
    {"id": "gpt-oss-20b#groq", "maker": "openai", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None, "paid_route_usd": 0.0003,
     "td1": {"F1": [], "F2": ["C02", "C11"], "F2b": [], "F3": [], "combined": []}},
    {"id": "gpt-oss-120b#groq", "maker": "openai", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None, "paid_route_usd": 0.0006,
     "td1": {"F1": [], "F2": ["C11"], "F2b": [], "F3": [], "combined": []}},
    {"id": "qwen3.8-27b#groq", "maker": "qwen", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None, "paid_route_usd": 0.0036,
     "td1": {"F1": ["C20 (HTTP 429)"], "F2": [], "F2b": ["C10"], "F3": [],
             "combined": ["C15", "C16 (HTTP 429)", "C17", "C19"]}},
    # Free only: no paid route of the same model, so it sorts after the Groq routes.
    {"id": "north-mini-code#openrouter", "maker": "cohere", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None, "paid_route_usd": None,
     "td1": {"F1": [], "F2": ["C02", "C08", "C09 (invalid SQL)", "C11"], "F2b": ["C10 (invalid SQL)"],
             "F3": [], "combined": ["C15", "C17", "C19"]}},
    # dots-3-note (6/6 on F1, 4/4 on F3) is left out: free only and never the cheapest
    # validated route; it would not change any decision below.
    {"id": "claude-fable-5-1#claude", "maker": "anthropic", "level": 3, "access": "subscription",
     "available": True, "cash": 0.0, "allocation": 0.045, "reset_minutes": None,
     "paid_route_usd": 0.045, "td1": None},
    {"id": "claude-fable-5-1#openrouter", "maker": "anthropic", "level": 3, "access": "tokens",
     "available": True, "cash": 0.045, "allocation": 0.045, "reset_minutes": None,
     "paid_route_usd": 0.045, "td1": None},
]


def check_panel(resources=RESOURCES, panel_ids=PANEL_IDS):
    """Refuse a quorum panel with the same route twice or two models of the same maker."""
    by_id = {r["id"]: r for r in resources}
    if len(set(panel_ids)) != len(panel_ids):
        raise ValueError(f"same route twice in the panel: {panel_ids}")
    makers = [by_id[i]["maker"] for i in panel_ids]
    if len(set(makers)) != len(makers):
        raise ValueError(f"two panel members share a maker: {dict(zip(panel_ids, makers))}")


def evidence(resource, request):
    """Return (eligible, text). The text goes into the reason string."""
    family = request["family"]
    if family not in FAMILIES:
        return False, f"{family} is not a TD 1 family"
    cases = FAMILIES[family]["cases"].split()
    if resource["td1"] is None:
        if request["use"] == "payout":
            return False, f"{resource['id']} not measured in TD 1, shadow only for a payout"
        ok = resource["level"] >= FAMILIES[family]["difficulty"]
        return ok, f"{resource['id']} not measured in TD 1, level {resource['level']} from portfolio group G1"
    failed = resource["td1"][family]
    good = len(cases) - len(failed)
    if not failed:
        return True, f"{resource['id']} {good}/{len(cases)} on {family} in TD 1 ({' '.join(cases)})"
    return False, f"{resource['id']} {good}/{len(cases)} on {family} in TD 1, failed {' '.join(failed)}"


def required_check(request, chosen):
    family, use = request["family"], request["use"]
    if family not in FAMILIES:
        return "refuse or pass to a person: no schema for this question type"
    check = CHECKS[family][use]
    if chosen is not None and chosen["td1"] is None:
        # "none" needs a route that scored 100 % on the family, and an untested route is
        # only reached when the free panel is down, so the quorum cannot run either.
        # The deterministic reference is the check that is still available.
        check = REFERENCE + " (untested route, the free panel is unavailable)"
    return f"{check} [{CHECK_EVIDENCE[family]}]"


def cost_key(r):
    paid = r["paid_route_usd"] if r["paid_route_usd"] is not None else float("inf")
    return (r["allocation"], paid, r["id"])


def choose(request, resources):
    """Sub-group rule: TD 1 evidence first, then included capacity, waiting, money, abstention.

    Difficulty picks the route, the use picks the check: the two are never mixed.
    At wake-up, availability must be measured again.
    """
    family = request["family"]
    scored = [(r, *evidence(r, request)) for r in resources]
    eligible = [(r, why) for r, ok, why in scored if ok]
    measured = [(r, why) for r, why in eligible if r["td1"] is not None]
    untested = [(r, why) for r, why in eligible if r["td1"] is None]
    case_note = f"{family}: {FAMILIES[family]['td1']} in TD 1" if family in FAMILIES else "no TD 1 cell"

    def run(r, why, reason):
        return {"action": "run", "resource": r["id"], "cash": r["cash"],
                "checks": required_check(request, r), "reason": f"{reason}: {why}"}

    def defer(r, why, reason):
        return {"action": "defer", "resource": r["id"], "cash": 0,
                "checks": required_check(request, r),
                "reason": f"{reason}: {why}; recheck availability at wake-up",
                "wake_in_minutes": r["reset_minutes"]}

    def can_refill(r):
        return (not r["available"] and r["cash"] == 0 and r["reset_minutes"] is not None
                and 0 < r["reset_minutes"] <= request["deadline_minutes"])

    # 1. A route validated on this family in TD 1, available, at no new cost.
    ready = sorted((x for x in measured if x[0]["available"] and x[0]["cash"] == 0), key=lambda x: cost_key(x[0]))
    if ready:
        return run(*ready[0], "cheapest free route validated in TD 1")
    # 2. Reversed priority: wait for a validated route rather than spend allocation on an untested one.
    waiting = sorted((x for x in measured if can_refill(x[0])), key=lambda x: x[0]["reset_minutes"])
    if waiting and request["can_wait"]:
        return defer(*waiting[0], "only validated routes are exhausted and refill before the deadline")
    # 3. Included capacity of an untested route (subscription), as in the kit rule.
    included = sorted((x for x in untested if x[0]["available"] and x[0]["cash"] == 0), key=lambda x: cost_key(x[0]))
    if included:
        return run(*included[0], f"no validated route available in time ({case_note}); included capacity")
    waiting = sorted((x for x in untested if can_refill(x[0])), key=lambda x: x[0]["reset_minutes"])
    if waiting and request["can_wait"]:
        return defer(*waiting[0], "included capacity refills before the deadline")
    # 4. New spending within the authorised budget.
    paid = sorted((x for x in eligible if x[0]["available"] and 0 < x[0]["cash"] <= request["budget"]),
                  key=lambda x: (x[0]["cash"], x[0]["id"]))
    if paid:
        return run(*paid[0], f"no free or included route in time ({case_note}); paid route within budget")
    if family not in FAMILIES:
        detail = f"{family} is not a TD 1 family, no route has been tested on it"
    else:
        parts = [why for _, ok, why in scored if not ok]
        parts += [f"{r['id']} unavailable" for r, _ in eligible if not r["available"]]
        parts += [f"{r['id']} over budget ({r['cash']} > {request['budget']})"
                  for r, _ in eligible if r["available"] and r["cash"] > request["budget"]]
        detail = "; ".join(parts)
    return {"action": "abstain", "resource": None, "cash": 0, "checks": required_check(request, None),
            "reason": f"no eligible route within deadline and budget ({case_note}); {detail}"}


def route(request, resources, check_result="pass"):
    """Apply POLICY around choose(): retries, fallback after max attempts, check gate.

    A resource may carry "simulated_429": the number of attempts it answers with
    HTTP 429 before it answers. After max_attempts_per_resource failures the route is
    dropped and choose() runs again with the time already spent taken off the deadline.
    check_result is the outcome of the required check, given by the scenario
    ("pass", "fail" or "timeout"). Only "pass" delivers.
    """
    pool = [dict(r) for r in resources]
    attempts, elapsed = [], 0
    max_attempts, pause = POLICY["max_attempts_per_resource"], POLICY["minutes_between_attempts"]
    while True:
        decision = choose({**request, "deadline_minutes": request["deadline_minutes"] - elapsed}, pool)
        if decision["action"] != "run":
            break
        resource = next(r for r in pool if r["id"] == decision["resource"])
        failures = resource.get("simulated_429", 0)
        if failures < max_attempts:
            attempts.append({"resource": resource["id"], "attempts": failures + 1,
                             "last": "answer", "minutes": elapsed + failures * pause})
            break
        elapsed += max_attempts * pause
        attempts.append({"resource": resource["id"], "attempts": max_attempts,
                         "last": "HTTP 429", "minutes": elapsed})
        resource.update(available=False, reset_minutes=None)
    decision["policy"] = POLICY["id"]
    decision["attempts"] = attempts
    if decision["action"] == "run":
        decision["check_result"] = check_result
        decision["delivered"] = check_result == "pass"
        if not decision["delivered"]:
            decision["reason"] += f"; check {check_result}: value withheld and logged ({POLICY['id']})"
    else:
        decision["delivered"] = False
    return decision


def choose_kit(request, resources):
    """The kit rule, unchanged, kept to replay it on the same scenarios (--rule kit)."""
    eligible = [r for r in resources if r["level"] >= request["difficulty"]]
    checks = "source verification and human review" if request["high_impact"] else "read-only execution and value check"
    included = [r for r in eligible if r["available"] and r["cash"] == 0]
    if included:
        chosen = min(included, key=lambda r: (r["allocation"], r["level"], r["id"]))
        return {"action": "run", "resource": chosen["id"], "cash": 0,
                "checks": checks, "reason": "eligible included capacity"}
    waiting = [r for r in eligible if not r["available"] and r["cash"] == 0
               and r["reset_minutes"] is not None
               and 0 < r["reset_minutes"] <= request["deadline_minutes"]]
    if waiting and request["can_wait"]:
        chosen = min(waiting, key=lambda r: r["reset_minutes"])
        return {"action": "defer", "resource": chosen["id"], "cash": 0,
                "checks": checks, "reason": "recheck availability at wake-up",
                "wake_in_minutes": chosen["reset_minutes"]}
    paid = [r for r in eligible if r["available"] and r["cash"] <= request["budget"]]
    if paid:
        chosen = min(paid, key=lambda r: (r["cash"], r["allocation"], r["id"]))
        return {"action": "run", "resource": chosen["id"], "cash": chosen["cash"],
                "checks": checks, "reason": "available route within the authorised budget"}
    return {"action": "abstain", "resource": None, "cash": 0,
            "checks": checks, "reason": "no eligible resource within deadline and budget"}


def scenarios():
    base = {"family": "F1", "use": "dashboard", "can_wait": True,
            "deadline_minutes": 120, "budget": 0.30}
    # Groq Free resets output tokens per minute: TD 1 saw 6 HTTP 429 on qwen3.8-27b.
    groq_down = [dict(r, available=False, reset_minutes=1) if r["id"].endswith("#groq") else dict(r)
                 for r in RESOURCES]
    all_free_down = [dict(r, available=False, reset_minutes=1) if r["access"] == "free" else dict(r)
                     for r in RESOURCES]
    included_down = [dict(r, available=False, reset_minutes=60) if r["access"] == "subscription" else dict(r)
                     for r in groq_down]
    # TD 1: qwen3.8-27b answered C18 and C19 after HTTP 429 on the first attempt.
    qwen_429_twice = [dict(r, simulated_429=2) if r["id"] == "qwen3.8-27b#groq" else dict(r)
                      for r in RESOURCES]
    small_never = [dict(r, simulated_429=99) if r["id"] == "gpt-oss-20b#groq" else dict(r)
                   for r in RESOURCES]
    # Each entry: name, request, resources, result of the required check (scenario input).
    return [
        ("simple", base, RESOURCES, "pass"),
        ("complex", {**base, "family": "F2"}, RESOURCES, "pass"),
        ("provider unavailable", base, groq_down, "pass"),
        ("deferrable", {**base, "family": "F2"}, groq_down, "pass"),
        ("cannot wait", {**base, "family": "F2", "can_wait": False, "deadline_minutes": 5}, groq_down, "pass"),
        ("urgent", {**base, "family": "combined", "use": "customer", "can_wait": False,
                    "deadline_minutes": 5}, [dict(r, available=False, reset_minutes=60)
                                             if r["access"] == "subscription" else dict(r)
                                             for r in all_free_down], "pass"),
        ("budget exhausted", {**base, "family": "F2", "can_wait": False, "budget": 0}, included_down, "pass"),
        ("high impact", {**base, "family": "F2", "use": "payout"}, RESOURCES, "pass"),
        ("unknown capability", {**base, "family": "F4 (age at first order)"}, RESOURCES, "pass"),
        ("transient 429", {**base, "family": "F2"}, qwen_429_twice, "pass"),
        ("retries exhausted", base, small_never, "pass"),
        ("check failed", {**base, "family": "F2", "use": "customer"}, RESOURCES, "fail"),
        ("check timeout", {**base, "family": "combined"}, RESOURCES, "timeout"),
    ]


def kit_request(request):
    """Translate a sub-group request into the fields the kit rule reads."""
    family = FAMILIES.get(request["family"])
    return {**request, "difficulty": family["difficulty"] if family else 4,
            "high_impact": request["use"] != "dashboard"}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", help="show only the named scenario")
    parser.add_argument("--rule", choices=["td2", "kit"], default="td2",
                        help="td2: sub-group rule (default); kit: the original choose")
    args = parser.parse_args()
    check_panel()
    found = False
    for name, request, resources, check_result in scenarios():
        if args.scenario and name != args.scenario:
            continue
        found = True
        if args.rule == "td2":
            result = route(request, resources, check_result)
        else:
            result = choose_kit(kit_request(request), resources)
        print(json.dumps({"scenario": name, "nature": "simulation", "rule": args.rule,
                          "request": request, "result": result}))
    if not found:
        parser.error("unknown scenario")


if __name__ == "__main__":
    main()
