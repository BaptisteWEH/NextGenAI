#!/usr/bin/env python3
"""Edge-case tests of Orchestrateur.vote_k_sur_n (TD 2, Pair A). No network."""
import importlib.util, sys
from pathlib import Path
from types import SimpleNamespace as NS

spec = importlib.util.spec_from_file_location("sk", Path(__file__).resolve().parent.parent / "skeleton-multi-llm-en.py")
mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
vote = lambda props, k: mod.Orchestrateur.vote_k_sur_n(None, props, k)

def P(values):
    return [NS(provider="p", model_requested=f"m{i}", value=v,
               verdict="executed" if v is not None else "error") for i, v in enumerate(values)]

def raises(props, k):
    try: vote(props, k)
    except ValueError: return True
    return False

# 1. error stays in n, casts no vote
assert vote(P([100, None, None]), 2) == {"consensus": False, "value": None, "votes": 1, "models": []}
# 2. strict majority: k <= n//2 and k > n refused (n=3 -> k in {2,3}; n=5 -> k in {3,4,5})
assert raises(P([1, 1, 1]), 1) and raises(P([1, 1, 1]), 4)
assert raises(P([1] * 5), 2) and not raises(P([1] * 5), 3) and raises(P([]), 1)
# 3. duplicate (provider, model) refused
dup = [NS(provider="p", model_requested="m", value=1, verdict="executed")] * 2 + P([1])[:1]
assert raises(dup, 2)
# 4. 0 cents is a real vote (wrong consensus [0,0,100] must still be returned)
assert vote(P([0, 0, 100]), 2)["value"] == 0 and vote(P([0, 0, 100]), 2)["consensus"] is True
# 5. an 'error' proposal never votes even if it carries a value
bad = P([5, 5, 5]); bad[1].verdict = "error"; bad[2].verdict = "error"
assert vote(bad, 2)["consensus"] is False and vote(bad, 2)["votes"] == 1
# 6. 3-of-5 with two unavailable members: 3 identical votes still win, 2 do not
assert vote(P([7, 7, 7, None, None]), 3)["consensus"] is True
assert vote(P([7, 7, 8, None, None]), 3) == {"consensus": False, "value": None, "votes": 2, "models": []}
# 7. dict proposals accepted too
assert vote([{"provider": "a", "model_requested": "x", "value": 3, "verdict": "executed"},
             {"provider": "b", "model_requested": "y", "value": 3, "verdict": "executed"}], 2)["value"] == 3
# 8. tie below k (C10 shape, 2 votes against 2 with k = 3): abstain, votes = 2
assert vote(P([1, 1, 2, 2, None]), 3) == {"consensus": False, "value": None, "votes": 2, "models": []}
print("all vote_k_sur_n tests passed")
