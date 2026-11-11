from pathlib import Path
import runpy
import sys
from time import perf_counter
from random import Random

sys.path.insert(0, str(Path("vendor/Starter_Kit").resolve()))
import engine

bot = runpy.run_path(sys.argv[1] if len(sys.argv) > 1 else "dist/bot.py")
rank = bot["rank"]
cards = bot["CARDS"]
rng = Random(20261104)
cases = [tuple(rng.sample(range(52), 7)) for _ in range(24000)]
start = perf_counter()
scores = [rank(case) for case in cases]
elapsed = perf_counter() - start
for case, score in zip(cases, scores):
    hand = [cards[c] for c in case]
    oracle = engine.best_hand(hand[:2], hand[2:])
    assert score == (oracle[0], *(v - 2 for v in oracle[1:])), (case, score, oracle)
    assert score == rank(tuple((c & ~3) + ((c + 1) % 4) for c in case))
simulate = bot["simulate"]
hole, board = cases[0][:2], cases[0][2:]
dead = tuple(c for c in range(52) if c not in cases[0])[:2]
assert simulate(hole, board, dead, 64, float("inf"), Random(11)) == simulate(
    hole, board, dead, 64, float("inf"), Random(11))
royal = tuple(bot["CARD_ID"][r + "s"] for r in "TJQKA")
assert simulate(hole, royal, dead, 64, float("inf"), Random(4)) == (.5,)
# Spy on the preflop policy boundary: only three board cards reach each
# simulated discard, and each private holding excludes the other's cards.
scope = simulate.__globals__
original_pick = scope["pick"]
preflop_hole = cases[0][:3]
calls = []
def checked_pick(private, flop, mode=2):
    assert len(private) == len(flop) == 3
    assert len(set(private + flop)) == 6
    assert private == preflop_hole or not set(private) & set(preflop_hole)
    assert not set(flop) & set(preflop_hole)
    calls.append((private, flop))
    return original_pick(private, flop, mode)

scope["pick"] = checked_pick
try:
    simulate(preflop_hole, (), (), 64, float("inf"), Random(2026))
finally:
    scope["pick"] = original_pick
assert len(calls) == 128 and all(calls[i][1] == calls[i+1][1] for i in range(0, 128, 2))
print(f"{len(cases)} oracle and suit checks, {len(cases)/elapsed:,.0f} evaluations/s")
