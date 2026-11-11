"""Showdown-order oracle and isolation checks for the experimental river model."""
from itertools import combinations
from pathlib import Path
from random import Random
import json
import runpy

root = Path('experiments/daily-1110')
old = runpy.run_path(str(root / 'baseline.py'))
new = runpy.run_path(str(root / 'river-order.py'))
np = new['np']
assert np is not None
rng = Random(111026)
witnesses = []
for i in range(80):
    board = tuple(rng.sample(range(52), 5))
    live = [c for c in range(52) if c not in board]
    pairs = np.asarray(list(combinations(live, 2)))
    scores = new['batch_rank'](np.concatenate((pairs, np.broadcast_to(board, (len(pairs), 5))), axis=1))
    strength = new['vector_strength'](pairs, board, scores)
    assert np.array_equal(strength, new['vector_strength'](pairs, board))
    order = np.argsort(scores, kind='stable')
    assert (np.diff(strength[order]) >= 0).all()
    assert ((np.diff(scores[order]) == 0) == (np.diff(strength[order]) == 0)).all()
    for j in rng.sample(range(len(pairs)), 125):
        scalar = new['rank'](tuple(map(int, pairs[j])) + board)
        expected = scalar[0] * 15 ** 5 + sum((r + 1) * 15 ** (4 - k) for k, r in enumerate(scalar[1:]))
        assert scores[j] == expected
    previous = old['vector_strength'](pairs, board, scores)
    backwards = np.where(np.diff(previous[order]) < 0)[0]
    if len(backwards) and len(witnesses) < 3:
        a, b = map(int, order[backwards[0]:backwards[0] + 2])
        witnesses.append(dict(board=board, weaker=pairs[a].tolist(), stronger=pairs[b].tolist(),
                              ranks=[int(scores[a]), int(scores[b])], old=[float(previous[a]), float(previous[b])]))
assert witnesses, 'Must demonstrate a real old-order inversion'

for length in (3, 4, 5):
    for i in range(20):
        cards = tuple(rng.sample(range(52), 10))
        hole = cards[:3] if length == 3 else cards[:2]
        board = cards[3:3 + length]
        dead = () if length == 3 else cards[8:10]
        events = [(0, 'raise', 1.3, .33, .02, True), (3, 'call', .4, .4, .1, True)]
        if length == 4:
            events.append((4, 'raise', 1., 0., .3, True))
        outputs = []
        for bot in (old, new):
            bot['vector_estimate'].__globals__['VECTOR_RNG'] = np.random.default_rng(700 + i)
            outputs.append(bot['vector_estimate'](hole, board, dead, events, bot['Frequencies'](), 512, True))
        assert outputs[0][0] == outputs[1][0]
        assert np.array_equal(outputs[0][1], outputs[1][1])
        assert all(np.array_equal(a, b) for a, b in zip(outputs[0][2], outputs[1][2]))
        if length < 5:
            assert np.array_equal(outputs[0][3], outputs[1][3])

# River action evidence can change inferred weights; estimates must stay finite,
# exact under suit rotation, and insensitive to ordering of the candidate pairs.
hole, board, dead = (48, 49), (0, 5, 10, 15, 20), (25, 30)
events = [(0, 'raise', 1.3, .33, .02, True), (5, 'raise', 1., 0., .3, True)]
rotate = lambda cards: tuple(c // 4 * 4 + (c % 4 + 1) % 4 for c in cards)
values = new['vector_estimate'](hole, board, dead, events, new['Frequencies']())
rotated = new['vector_estimate'](rotate(hole), rotate(board), rotate(dead), events, new['Frequencies']())
assert abs(values[0] - rotated[0]) < 1e-12
assert 0 <= values[0] <= 1
assert new['vector_estimate']((1, 6), (32, 36, 40, 44, 48), (11, 15), events, new['Frequencies']()) == (.5,)
with (root / 'oracle.json').open('x') as f:
    json.dump(dict(boards=80, exhaustive_pair_order_checks=80 * 1081, scalar_oracle_checks=10000,
                   isolation_cases=60, inversion_examples=witnesses), f, indent=2)
print('86,480 river pair orders, 10,000 scalar ranks, 60 isolation cases, suit and tie fixtures passed')
