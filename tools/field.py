"""Small field sensitivity exercise using empirical full-match edge samples."""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
from random import Random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("reports", nargs="+")
    p.add_argument("--trials", type=int, default=2000)
    args = p.parse_args()
    edges = defaultdict(list)
    for report in args.reports:
        for row in map(json.loads, Path(report).read_text(encoding="utf-8").splitlines()):
            first, second = [Path(bot["path"].replace("\\", "/")).stem for bot in row["bots"]]
            a, b = sorted((first, second))
            sign = 1 if a == first else -1
            edges[row["stage"], a, b].append(sign * row["delta"])
    players = sorted({name for _, a, b in edges for name in (a, b)})
    for stage in (1, 2):
        missing = [(a, b) for a, b in combinations(players, 2) if not edges[stage, a, b]]
        if missing:
            raise ValueError(f"Stage {stage} missing field edges: {missing}")
    rng = Random(473)
    for mode in ("swiss", "round_robin"):
        ranks = Counter()
        for _ in range(args.trials):
            order = players.copy()
            rng.shuffle(order)
            points = dict.fromkeys(order, 0.)
            chips = dict.fromkeys(order, 0)
            met = set()
            stage = 1 if mode == "swiss" else 2

            def play(a, b):
                a, b = sorted((a, b))
                met.add((a, b))
                delta = rng.choice(edges[stage, a, b])
                points[a] += 1 if delta > 0 else .5 if delta == 0 else 0
                points[b] += 1 if delta < 0 else .5 if delta == 0 else 0
                chips[a] += delta
                chips[b] -= delta

            if mode == "round_robin":
                for a, b in combinations(order, 2):
                    play(a, b)
            else:
                bye = set()
                for _ in range(min(5, len(order) - 1)):
                    pool = sorted(order, key=lambda x: (points[x], chips[x]), reverse=True)
                    if len(pool) % 2:
                        recipient = next(x for x in reversed(pool) if x not in bye)
                        bye.add(recipient)
                        pool.remove(recipient)
                        points[recipient] += 1
                    while pool:
                        a = pool.pop(0)
                        b = next((x for x in pool if tuple(sorted((a, x))) not in met), pool[0])
                        pool.remove(b)
                        play(a, b)
            best = max((points[a], chips[a]) for a in order)
            leaders = [a for a in order if (points[a], chips[a]) == best]
            for a in leaders:
                ranks[a] += 1 / len(leaders)
        print(mode, {a: round(ranks[a] / args.trials, 3) for a in players})

if __name__ == "__main__":
    main()

