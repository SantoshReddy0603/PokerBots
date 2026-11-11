"""A separate calculation-only candidate; exact same policy and random draws."""
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter
import hashlib
import json
import runpy

root = Path('experiments/daily-1110')
before = '    counts = (values[:, :, None] == ranks).sum(axis=1)'
after = ('    # Count (row, rank) bins directly without a rows x cards x 13 boolean array.\n'
         '    bins = values + 13 * np.arange(len(cards))[:, None]\n'
         '    counts = np.bincount(bins.ravel(), minlength=13 * len(cards)).reshape(len(cards), 13)')
original = (root / 'baseline.py').read_text()
assert original.count(before) == 1
candidate = original.replace(before, after)
with (root / 'histogram.py').open('x') as f:
    f.write(candidate)
old, new = [runpy.run_path(str(root / p)) for p in ('baseline.py', 'histogram.py')]
np = old['np']
rng = Random(110107)
cases = [np.asarray([rng.sample(range(52), n) for _ in range(size)])
         for n in (5, 6, 7) for size in (1, 512, 903, 4096)]
timings = []
for cards in cases:
    assert np.array_equal(old['batch_rank'](cards), new['batch_rank'](cards))
    measured = {'baseline': [], 'histogram': []}
    for repetition in range(12):
        labels = ['baseline', 'histogram'] if repetition % 2 == 0 else ['histogram', 'baseline']
        for label in labels:
            bot = old if label == 'baseline' else new
            start = perf_counter()
            for _ in range(8):
                bot['batch_rank'](cards)
            measured[label].append((perf_counter() - start) / 8 * 1000)
    timings.append(dict(rows=len(cards), cards=cards.shape[1],
                        medians_ms={k: median(v) for k, v in measured.items()}, raw_ms=measured))
posterior_times = {'baseline': [], 'histogram': []}
for length in (3, 4, 5):
    for i in range(20):
        cards = tuple(rng.sample(range(52), 10))
        hole = cards[:3] if length == 3 else cards[:2]
        board = cards[3:3 + length]
        dead = () if length == 3 else cards[8:10]
        events = [(0, 'raise', 1.3, .33, .02, True), (3, 'call', .4, .4, .1, True)]
        if length >= 4:
            events.append((length, 'raise', 1., 0., .3, True))
        outputs = []
        for label in (['baseline', 'histogram'] if i % 2 == 0 else ['histogram', 'baseline']):
            bot = old if label == 'baseline' else new
            bot['vector_estimate'].__globals__['VECTOR_RNG'] = np.random.default_rng(11100 + i)
            start = perf_counter()
            outputs.append(bot['vector_estimate'](hole, board, dead, events, bot['Frequencies'](), 512, True))
            posterior_times[label].append(dict(street=length, ms=(perf_counter() - start) * 1000))
        assert outputs[0][0] == outputs[1][0]
        assert np.array_equal(outputs[0][1], outputs[1][1])
        assert all(np.array_equal(a, b) for a, b in zip(outputs[0][2], outputs[1][2]))
        assert np.array_equal(outputs[0][3], outputs[1][3])
report = dict(candidate_sha256=hashlib.sha256(candidate.encode()).hexdigest(),
              ranks_checked=sum(len(c) for c in cases), posterior_cases=60,
              rank_timings=timings, posterior_timings=posterior_times,
              posterior_medians_ms={label: {n: median(x['ms'] for x in values if x['street'] == n)
                                           for n in (3, 4, 5)} for label, values in posterior_times.items()})
with (root / 'histogram-probe.json').open('x') as f:
    json.dump(report, f, indent=2)
print(json.dumps({k: v for k, v in report.items() if k not in ('rank_timings', 'posterior_timings')}, indent=2))
