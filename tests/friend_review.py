"""Exact blind-loss bounds and fixed-sample equivalence of river caching."""
import runpy
import sys
from random import Random

candidate = runpy.run_path(sys.argv[1] if len(sys.argv) > 1 else "checkpoints/friend-review.py")
previous = runpy.run_path("checkpoints/pre-friend-review.py")
lock = candidate["protected_lead"]

for total in (400, 1000):
    for remaining in range(1, total + 1):
        hand = total - remaining + 1
        for seat in ("button", "big_blind"):
            # Independent explicit simulation of folding every remaining hand.
            blinds = [1 if (i % 2 == 0) == (seat == "button") else 2
                      for i in range(remaining)]
            net = total + sum(blinds)
            assert lock(net, total, hand, hand - 1, total, seat)
            assert not lock(net - 1, total, hand, hand - 1, total, seat)
            for offset, blind in enumerate(blinds):
                net -= blind
                if offset + 1 < remaining:
                    next_seat = seat if (offset + 1) % 2 == 0 else (
                        "big_blind" if seat == "button" else "button")
                    assert lock(net, total, hand + offset + 1,
                                hand + offset, total, next_seat)
            assert net == total
        assert not lock(10000, total, hand, hand - 2, total, "button")
        assert not lock(10000, total, hand, hand - 1, None, "button")

state = candidate["State"]()
state.observe(dict(protocol_version="1.0", small_blind=1, big_blind=2,
                   total_hands=400, per_response_ms=5000), "init")
state.match_net, state.scored_hands = 407, 395
state.observe(dict(hand_id=396, seat="button"), "new_hand")
assert state.locked  # 1+2+1+2+1 = 7, instead of the old bound of 10.
state.observe(dict(hand_id=396, seat="big_blind"), "new_hand")
assert not state.locked  # 2+1+2+1+2 = 8.

rng = Random(58271)
for n in range(100):
    cards = tuple(rng.sample(range(52), 9))
    hole, board, dead = cards[:2], cards[2:7], cards[7:]
    events = [(0, "raise", .7, .2, .1, True),
              (3, "call", .4, .4, .1, True),
              (5, "raise", .8, 0., .4, True)] if n % 2 else []
    args = (hole, board, dead, events, 144, float("inf"))
    assert candidate["modeled_equity"](*args, Random(n)) == previous["modeled_equity"](*args, Random(n))

# A complete 144-sample river rollout now ranks hero and board once each.
g = candidate["modeled_equity"].__globals__
original_rank = g["rank"]
counts = {"board": 0, "hero": 0}
def counted_rank(cards):
    if cards == board:
        counts["board"] += 1
    if cards == hole + board:
        counts["hero"] += 1
    return original_rank(cards)
g["rank"] = counted_rank
try:
    candidate["modeled_equity"](hole, board, dead, [], 144, float("inf"), Random(71))
finally:
    g["rank"] = original_rank
assert counts == {"board": 1, "hero": 1}, counts
print("2,800 blind boundaries, fold-out guarantees, 100 river equivalence cases and caching passed")
