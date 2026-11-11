"""Validate the separately built sampling and action-specific range experiments."""
import runpy
import sys
from random import Random

sample = runpy.run_path("checkpoints/review-1109-sampling-exp.py")
np = sample["np"]
model = sample["Frequencies"]()
hole, board, dead = (48, 45), (0, 5, 10, 15), (20, 25)
first = sample["vector_estimate"](hole, board, dead, [], model, 128, True, return_particles=True)
pooled = sample["vector_estimate"](hole, board, dead, [], model, 128, True,
                                    particles=first[-1], return_particles=True)
assert len(pooled[1]) == 256 and 0 <= pooled[0][0] <= 1
pairs, triple, full = pooled[-1]
assert np.array_equal(pairs[:128], first[-1][0])
assert np.array_equal(full[:128], first[-1][2])
for pair, runout in zip(pairs, full):
    assert tuple(runout[:4]) == board
    assert len(set(map(int, pair)) | set(map(int, runout)) | set(hole) | set(dead)) == 11

g = sample["estimate"].__globals__
original_vector, original_clock = g["vector_estimate"], g["perf_counter"]
calls = []
clock = [0.]
def tick():
    clock[0] += .001
    return clock[0]
def stub(*args, **kwargs):
    calls.append(kwargs)
    n = 1024 if kwargs.get("particles") is not None else 512
    result = ((.5,), np.ones(n), [np.asarray([1.] * (n // 2) + [0.] * (n // 2))], np.zeros(n))
    return result + ((np.empty((n, 2)), np.empty((n, 3)), np.empty((n, 5))),) if kwargs.get("return_particles") else result
g["vector_estimate"], g["perf_counter"] = stub, tick
state = sample["State"]()
state.seat = "button"
req = dict(type="action_request", hand_id=1, pot=202, to_call=198, time_left_ms=60000, opp_stack=0)
try:
    sample["estimate"](state, req, hole, board, dead, 512)
    assert len(calls) == 2 and state.sample_stats["rows"] == 1024
    calls.clear()
    sample["estimate"](state, req, hole, board + (30,), dead, 512)
    assert len(calls) == 1  # Exact river has no Monte Carlo sampling error.
    calls.clear()
    g["perf_counter"] = lambda: 0. if not calls else 1.
    sample["estimate"](state, req, hole, board, dead, 512)
    assert len(calls) == 1  # No second batch once the estimated time is exhausted.
finally:
    g["vector_estimate"], g["perf_counter"] = original_vector, original_clock

range_bot = runpy.run_path("checkpoints/review-1109-ranges-exp.py")
rng = Random(71930)
flops, pairs = [], []
for _ in range(300):
    cards = rng.sample(range(52), 5)
    flops.append(tuple(cards[:3])); pairs.append(tuple(cards[3:]))
actual = range_bot["batch_flop"](np.asarray(pairs), np.asarray(flops))
expected = [range_bot["flop_score"](p, f) for p, f in zip(pairs, flops)]
assert np.max(np.abs(actual - expected)) < 1e-12
state = range_bot["State"]()
state.seat, state.hole = "button", (48, 49, 44)
state.history = [dict(street="preflop", actor="me", action="raise", amount=6),
                 dict(street="preflop", actor="opp", action="raise", amount=200)]
state.model.observe(state.history, state.seat)
assert state.model.cells[("preflop", "shove_reraise")] == (1, 1)
req = dict(hand_id=1, time_left_ms=60000, opp_stack=0, opp_bet=200)
g = range_bot["action_preflop_equity"].__globals__
results = []
for aggression in (440, 460):
    state.model.cells[("preflop", "raise")] = (aggression, 1000)
    g["VECTOR_RNG"] = np.random.default_rng(7512)
    results.append(range_bot["action_preflop_equity"](state, req, 256))
assert results[0] == results[1]  # No aggregate-aggression 0.45 discontinuity.
assert 0 <= results[0][0] <= 1 and 0 < results[0][1] <= 256
print("Pooled samples, budget/exact-river gates, variable-flop features and action-specific preflop checks passed")
