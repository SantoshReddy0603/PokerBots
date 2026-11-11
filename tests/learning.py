"""Independent scalar/vector agreement and public-learning invariants."""
import runpy
import sys
from random import Random

b = runpy.run_path(sys.argv[1] if len(sys.argv) > 1 else "dist/bot.py")
np = b["np"]
assert np is not None
rng = Random(97031)
for count in (5, 6, 7):
    cards = [tuple(rng.sample(range(52), count)) for _ in range(5000)]
    vector = b["batch_rank"](np.array(cards))
    for hand, score in zip(cards, vector):
        actual = b["rank"](hand)
        expected = actual[0] * 15 ** 5 + sum((r + 1) * 15 ** (4 - i) for i, r in enumerate(actual[1:]))
        assert score == expected, (hand, actual, score, expected)
for _ in range(10):
    cards = tuple(rng.sample(range(52), 3))
    pairs = [tuple(rng.sample([c for c in range(52) if c not in cards], 2)) for _ in range(200)]
    vector = b["batch_flop"](np.array(pairs), cards)
    expected = [b["flop_score"](pair, cards) for pair in pairs]
    assert np.max(np.abs(vector - expected)) < 1e-12

model = b["Frequencies"]()
history = [dict(street="preflop", actor="opp", action="raise", amount=5),
           dict(street="preflop", actor="me", action="call", amount=5),
           dict(street="flop", actor="me", action="check"),
           dict(street="flop", actor="opp", action="raise", amount=4)]
for _ in range(100):
    model.observe(history, "big_blind")
assert model.rate(("postflop", "raise"), .35) > .85
assert b["Frequencies"]().cells == {}
state = b["State"]()
state.observe(dict(hand_id=1, seat="big_blind"), "new_hand")
result = dict(hand_id=1, net=3, history=history)
state.observe(result, "hand_result")
before = dict(state.model.cells)
state.observe(result, "hand_result")
assert state.model.cells == before and state.match_net == 3

state.observe(dict(protocol_version="1.0", small_blind=1, big_blind=2,
                   total_hands=400, per_response_ms=5000), "init")
state.match_net, state.scored_hands = 10, 395
state.observe(dict(hand_id=396, seat="button"), "new_hand")
assert not state.locked if getattr(state, "score_scope", None) == "leg" else state.locked
state.match_net, state.scored_hands = 6, 395
state.observe(dict(hand_id=396, seat="button"), "new_hand")
assert not state.locked

hole, board, dead = (48, 49), (0, 5, 10, 15, 20), (25, 30)
equity = b["vector_estimate"](hole, board, dead, [], b["Frequencies"]())[0]
# Exact independent enumeration, including the vector engine's soft discard prior.
live = [c for c in range(52) if c not in hole + board + dead]
mass = total = 0
from itertools import combinations
for pair in combinations(live, 2):
    triple = pair + (dead[1],)
    scores = [b["flop_score"](tuple(triple[j] for j in keep), board[:3]) for keep in b["PAIRS"]]
    import math
    probabilities = [math.exp((s - max(scores)) / .12) for s in scores]
    weight = .15 + .85 * probabilities[2] / sum(probabilities)
    total += weight * b["compare"](b["rank"](hole + board), b["rank"](pair + board))
    mass += weight
assert abs(total / mass - equity) < 1e-12
royal = (32, 36, 40, 44, 48)
assert b["vector_estimate"]((1, 6), royal, (11, 15), [], model) == (.5,)
positions = b["weighted_position"](np.array([2., 1., 2.]), np.array([1., 2., 3.]))
assert positions[0] == positions[2] and positions[0] > positions[1]
events = [(0, "raise", 1.3, .33, .02, True), (3, "call", .4, .4, .1, True),
          (5, "raise", 2., 0., .4, True)]
reference = b["vector_estimate"](hole, board, dead, events, model)
rotate = lambda cards: tuple(c // 4 * 4 + (c % 4 + 1) % 4 for c in cards)
assert abs(reference[0] - b["vector_estimate"](rotate(hole), rotate(board), rotate(dead), events, model)[0]) < 1e-12

g = b["vector_estimate"].__globals__
original_flop, original_strength = g["batch_flop"], g["vector_strength"]
def checked_flop(pairs, visible):
    assert tuple(visible) == board[:3]
    return original_flop(pairs, visible)
def checked_strength(pairs, visible, made=None):
    assert tuple(visible) in (board[:3], board[:4])
    assert made is None  # No future runout score can enter a past-street range.
    return original_strength(pairs, visible, made)
g["batch_flop"], g["vector_strength"] = checked_flop, checked_strength
try:
    b["vector_estimate"](hole, board[:4], dead, events, model)
finally:
    g["batch_flop"], g["vector_strength"] = original_flop, original_strength
print("15,000 scalar/vector ranks, 2,000 flop features, exact river oracle, suit/future isolation and learning invariants passed")
