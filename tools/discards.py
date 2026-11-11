from pathlib import Path
import runpy
from random import Random
from statistics import mean, stdev
from math import sqrt

bot = runpy.run_path("dist/bot.py")
pick, rank, sim, pairs, score = (bot[name] for name in
                                ("pick", "rank", "simulate", "PAIRS", "flop_score"))
for seed in ("validation-0", "validation-1", "validation-2", "validation-3"):
    rng = Random(seed)
    outcomes = [[], []]
    for n in range(350):
        h1, h2, flop, runout = (lambda cards: (cards[:3], cards[3:6], cards[6:9], cards[9:]))(
            tuple(rng.sample(range(52), 11)))
        board = flop + runout
        if n % 4 == 3:
            v = sim(h2, flop, (), 96, float("inf"), rng)
            oi = max(range(3), key=v.__getitem__)
        else:
            oi = pick(h2, flop, n % 4)
        opp = rank(tuple(h2[j] for j in pairs[oi]) + board)
        v = sim(h1, flop, (), 128, float("inf"), rng)
        best = max(range(3), key=lambda i: v[i] + .05 *
                   score(tuple(h1[j] for j in pairs[i]), flop))
        scores = [bot["compare"](rank(tuple(h1[j] for j in pairs[i]) + board), opp)
                  for i in (best, pick(h1, flop, 0), pick(h1, flop, 1))]
        for diffs, value in zip(outcomes, scores[1:]):
            diffs.append(scores[0] - value)
    print(seed, [(round(mean(d), 4), round(1.96 * stdev(d) / sqrt(len(d)), 4)) for d in outcomes])

