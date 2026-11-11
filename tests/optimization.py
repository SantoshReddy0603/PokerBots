"""Same draws and posterior arrays before/after caching, plus local timings."""
import argparse
import json
from pathlib import Path
from random import Random
import runpy
from statistics import median
from time import perf_counter

p = argparse.ArgumentParser()
p.add_argument("candidate", nargs="?", default="checkpoints/daily-1110-histogram.py")
p.add_argument("--timing-out", type=Path, help="optional new timing report; existing reports are preserved")
cli_args = p.parse_args()
old = runpy.run_path("checkpoints/learning-v5.py")
new = runpy.run_path(cli_args.candidate)
np = new["np"]
rng = Random(78391)
report = {}
for length in (3, 4, 5):
    cases = []
    for i in range(20):
        cards = tuple(rng.sample(range(52), 10))
        hole = cards[:3] if length == 3 else cards[:2]
        board = cards[3:3 + length]
        dead = () if length == 3 else cards[8:10]
        events = [(0, "raise", 1.3, .33, .02, True), (3, "call", .4, .4, .1, True)]
        if length >= 4:
            events.append((length, "raise", 1., 0., .3, True))
        case_args = (hole, board, dead, events)
        outputs = []
        for scope in (old, new):
            g = scope["vector_estimate"].__globals__
            g["VECTOR_RNG"] = np.random.default_rng(900 + i)
            outputs.append(scope["vector_estimate"](*case_args, scope["Frequencies"](), 512, True))
        assert outputs[0][0] == outputs[1][0]
        assert np.array_equal(outputs[0][1], outputs[1][1])
        assert all(np.array_equal(a, b) for a, b in zip(outputs[0][2], outputs[1][2]))
        assert np.array_equal(outputs[0][3], outputs[1][3])
        cases.append(case_args)
    timings = {}
    for label, scope in (("previous", old), ("optimized", new)):
        elapsed = []
        for _ in range(3):
            start = perf_counter()
            for case_args in cases:
                scope["vector_estimate"](*case_args, scope["Frequencies"](), 512, True)
            elapsed.append((perf_counter() - start) * 1000 / len(cases))
        timings[label] = median(elapsed)
    report[str(length)] = timings
if cli_args.timing_out:
    with cli_args.timing_out.open("x") as file:
        file.write(json.dumps(report, indent=2) + "\n")
print("60 complete posterior equivalence cases passed", json.dumps(report))
