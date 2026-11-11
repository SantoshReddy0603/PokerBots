"""Regression checks for shared size buckets and independent public context fixes."""
import runpy
import sys

b = runpy.run_path(sys.argv[1] if len(sys.argv) > 1 else "checkpoints/review-1109-combined.py")
np = b["np"]
def event(street, actor, action, amount=None):
    d = dict(street=street, actor=actor, action=action)
    if amount is not None:
        d["amount"] = amount
    return d

pre = [event("preflop", "me", "raise", 6), event("preflop", "opp", "raise", 18),
       event("preflop", "me", "raise", 40), event("preflop", "opp", "call", 40)]

if b.get("FIX_BET_SIZES", True):
    cases = []
    for bet, target, bucket in ((20, 62, "fold_small"), (39, 94, "fold_small"),
                                (40, 96, "fold_large"), (41, 98, "fold_large")):
        cases.append((pre + [event("flop", "opp", "raise", bet)],
                      80 + bet, bet, 0, bet, 2 * bet, 160, target, bucket))
    cases.append((pre + [event("flop", "opp", "check")], 80, 0, 0, 0, 2, 160, 28, "fold_small"))
    prefix = [event("preflop", "me", "call", 2), event("preflop", "opp", "check"),
              event("flop", "opp", "raise", 2), event("flop", "me", "raise", 4),
              event("flop", "opp", "raise", 6)]
    cases.append((prefix, 14, 2, 4, 6, 8, 198, 12, "fold_small"))
    g = b["posterior_action"].__globals__
    helper = g["raise_size_features"]
    for history, pot, call, mine, other, lo, hi, target, bucket in cases:
        req = dict(street="flop", pot=pot, to_call=call, my_bet=mine, opp_bet=other,
                   my_stack=hi - mine, opp_stack=hi - other, min_raise=lo, max_raise=hi,
                   legal_actions=["fold", "call", "raise"] if call else ["check", "raise"])
        state = b["State"]()
        state.seat = "button"
        state.posterior = np.ones(100), np.asarray([1.] * 65 + [0.] * 35), np.arange(100.)
        calls = []
        def spy(p, c, a):
            result = helper(p, c, a)
            calls.append(((p, c, a), result[1]))
            return result
        g["raise_size_features"] = spy
        try:
            b["posterior_action"](state, req, .65)
            assert ((pot, call, target - mine), bucket) in calls, (req, target, calls)
            for response in ("fold", "call", "raise"):
                before, after = b["Frequencies"](), b["Frequencies"]()
                before.observe(history, "button")
                reply_amount = None if response == "fold" else (target if response == "call" else 2 * target - other)
                assert reply_amount is None or reply_amount <= hi
                calls.clear()
                after.observe(history + [event("flop", "me", "raise", target),
                                         event("flop", "opp", response, reply_amount)], "button")
                assert ((pot, call, target - mine), bucket) in calls
                key = ("postflop", bucket)
                a, n = before.cells.get(key, (0, 0))
                assert after.cells[key] == (a + (response == "fold"), n + 1)
                wrong = ("postflop", "fold_large" if bucket == "fold_small" else "fold_small")
                assert after.cells.get(wrong, (0, 0)) == before.cells.get(wrong, (0, 0))
        finally:
            g["raise_size_features"] = helper
    assert helper(80, 0, 48) == (.6, "fold_large")
    assert helper(80, 0, 47)[1] == "fold_small"
    print("Size prediction/observation agree for 18 legal raise responses, calls, reraises and boundary cases")

if b.get("FIX_RERAISES", True):
    h = [event("preflop", "me", "raise", 4), event("preflop", "opp", "raise", 6)]
    public = b["range_events"](h, "button")[0]
    assert public.reraise and abs(public[3] - 1 / 3) < 1e-12
    seen = []
    class Spy(b["Frequencies"]):
        def rate(self, key, prior, mass=16):
            seen.append(key)
            return super().rate(key, prior, mass)
    b["vector_estimate"]((48, 45, 38), (0, 5, 10), (), [public], Spy(), 32)
    assert ("preflop", "reraise") in seen and ("preflop", "open") not in seen
    print("Raise-to-4 / minimum-reraise-to-6 queries the public reraise model")

if b.get("FIX_OPENINGS", True):
    model = b["Frequencies"]()
    model.observe([event("preflop", "me", "call", 2), event("preflop", "opp", "check")], "button")
    assert model.cells[("preflop", "isolate")] == (0, 1) and ("preflop", "open") not in model.cells
    model.observe([event("preflop", "opp", "raise", 5)], "big_blind")
    assert model.cells[("preflop", "open")] == (1, 1)
    for history, seat, wanted in (([event("preflop", "opp", "raise", 5)], "big_blind", "open"),
                                  ([event("preflop", "me", "call", 2), event("preflop", "opp", "raise", 6)], "button", "isolate")):
        seen = []
        class Spy(b["Frequencies"]):
            def rate(self, key, prior, mass=16):
                seen.append(key)
                return super().rate(key, prior, mass)
        b["vector_estimate"]((48, 45, 38), (0, 5, 10), (), b["range_events"](history, seat), Spy(), 32)
        assert ("preflop", wanted) in seen
    print("Open/isolation counters and inference lookups agree")
