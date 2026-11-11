"""Alternating paired warm timings on one CPU; not a playing-strength test."""
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter
import json
import runpy

root = Path('experiments/daily-1110')
bots = {name: runpy.run_path(str(root / (name + '.py'))) for name in ('baseline', 'histogram')}
np = bots['baseline']['np']
for bot in bots.values():
    bot['batch_preflop'](np.array([[0, 5, 10]]))
rng = Random(111011)
report = {}
for length in (3, 4, 5):
    times = {name: [] for name in bots}
    cases = []
    for i in range(20):
        cards = tuple(rng.sample(range(52), 10))
        cases.append((cards[:3] if length == 3 else cards[:2], cards[3:3 + length],
                      () if length == 3 else cards[8:10]))
    for repetition in range(5):
        for i, (hole, board, dead) in enumerate(cases):
            events = [(0, 'raise', 1.3, .33, .02, True), (3, 'call', .4, .4, .1, True)]
            if length >= 4:
                events.append((length, 'raise', 1., 0., .3, True))
            labels = list(bots) if (repetition + i) % 2 == 0 else list(reversed(bots))
            for name in labels:
                bot = bots[name]
                bot['vector_estimate'].__globals__['VECTOR_RNG'] = np.random.default_rng(7110 + i)
                start = perf_counter()
                bot['vector_estimate'](hole, board, dead, events, bot['Frequencies'](), 512, True)
                times[name].append((perf_counter() - start) * 1000)
    medians = {k: median(v) for k, v in times.items()}
    report[length] = dict(medians_ms=medians, savings_percent=100 * (1 - medians['histogram'] / medians['baseline']),
                          raw_ms=times)
with (root / 'histogram-timing.json').open('x') as f:
    json.dump(report, f, indent=2)
print(json.dumps({k: {n: v for n, v in row.items() if n != 'raw_ms'} for k, row in report.items()}, indent=2))
