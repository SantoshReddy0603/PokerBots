import runpy
import sys
from itertools import combinations

b = runpy.run_path(sys.argv[1])
encode = lambda cards: tuple(b["CARD_ID"][c] for c in cards.split())
board = encode("2s 7h Jd 4c Qd")
weak = encode("3s 5c")
improved = encode("Qs Qh")
exposed = encode("9s")[0]
history = [
    dict(street="preflop", actor="opp", action="call", amount=2),
    dict(street="flop", actor="me", action="raise", amount=4),
    dict(street="flop", actor="opp", action="call", amount=4),
    dict(street="river", actor="opp", action="raise", amount=24),
]
events = b["range_events"](history, "big_blind")
assert events[0][:4] == (0, "call", 1/3, 1/3)
assert events[1][:4] == (3, "call", .5, .5)
assert events[2][:4] == (5, "raise", 2., 0.)
weight = b["range_weight"]
assert weight(improved + (exposed,), improved, board, events) > weight(weak + (exposed,), weak, board, events)
assert weight(improved + (exposed,), improved, board, events[:-1]) == weight(
    improved + (exposed,), improved, board[:4], events)
assert b["discard_weight"](improved, exposed, board[:3]) >= .16

if "river_distribution" in b:
    hero = encode("Jh Js")
    dead = encode("Ac 9s")
    d = b["river_distribution"](hero, board, dead, events, float("inf"), b["Random"](61))
    assert d[-1] and len(d[2]) == 903 and 0 < d[1] <= 903
    made = b["rank"](hero + board)
    board_rank = b["rank"](board)
    expected_sum = total = 0.
    for pair in combinations(set(range(52)) - set(hero + board + dead), 2):
        opp = b["rank"](pair + board)
        w = b["discard_weight"](pair, dead[1], board[:3]) * weight(pair + (dead[1],), pair, board, events, opp, board_rank)
        total += w
        expected_sum += w * b["compare"](made, opp)
    assert abs(d[0] - expected_sum / total) < 1e-10
    assert b["river_distribution"](hero, board, dead, events, 0., b["Random"](61)) is None
    ev = b["river_bet_ev"]
    assert ev([(1., 1., .65)], 100, 30, 30, False) > 100
    assert ev([(1., 0., .85)], 100, 30, 30, False) < 0
    assert ev([(1., 0., .12)], 100, 30, 30, False) > 0
print("history, information boundary and river fixtures passed")

