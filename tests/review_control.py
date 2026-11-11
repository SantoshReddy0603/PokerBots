"""Disabling all fixes preserves the release's learned counts and full posterior."""
import runpy
from random import Random

old = runpy.run_path("checkpoints/review-1109-fallback.py")
new = runpy.run_path("checkpoints/review-1109-control.py")
def e(s, who, action, n=None):
    d = dict(street=s, actor=who, action=action)
    if n is not None:
        d["amount"] = n
    return d
scenarios = [
    ("button", [e("preflop", "me", "call", 2), e("preflop", "opp", "check"),
                e("flop", "opp", "check"), e("flop", "me", "raise", 4), e("flop", "opp", "call", 4)]),
    ("big_blind", [e("preflop", "opp", "raise", 4), e("preflop", "me", "call", 4),
                   e("flop", "me", "check"), e("flop", "opp", "raise", 3), e("flop", "me", "call", 3)]),
    ("button", [e("preflop", "me", "raise", 4), e("preflop", "opp", "raise", 6), e("preflop", "me", "call", 6),
                e("flop", "opp", "raise", 4), e("flop", "me", "call", 4)]),
    ("big_blind", [e("preflop", "opp", "call", 2), e("preflop", "me", "raise", 7), e("preflop", "opp", "call", 7),
                   e("flop", "me", "check"), e("flop", "opp", "raise", 5), e("flop", "me", "call", 5)]),
]
rng = Random(345129)
models = [scope["Frequencies"]() for scope in (old, new)]
for i in range(40):
    seat, history = scenarios[i % len(scenarios)]
    cards = tuple(rng.sample(range(52), 6))
    results = []
    for scope, model in zip((old, new), models):
        model.observe(history, seat)
        scope["vector_estimate"].__globals__["VECTOR_RNG"] = scope["np"].random.default_rng(5000 + i)
        results.append(scope["vector_estimate"](cards[:3], cards[3:], (), scope["range_events"](history, seat), model, 64, True))
    assert models[0].cells == models[1].cells
    assert results[0][0] == results[1][0]
    assert old["np"].array_equal(results[0][1], results[1][1])
    assert all(old["np"].array_equal(x, y) for x, y in zip(results[0][2], results[1][2]))
    assert old["np"].array_equal(results[0][3], results[1][3])
print("40 real-history control cases preserve release counts and full posterior exactly")
