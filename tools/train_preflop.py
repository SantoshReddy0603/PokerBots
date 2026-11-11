"""Generate suit-isomorphic all-in equities with uniform and premium-heavy priors."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path
from random import Random
import runpy

scope = runpy.run_path("checkpoints/betting.py")
scope.update(runpy.run_path("src/preflop_key.py"))

def train(job):
    key, hole, samples = job
    rng = Random(432983 + key)
    deck = [c for c in range(52) if c not in hole]
    total = weighted = weight_sum = 0.
    rank, pick = scope["rank"], scope["pick"]
    pairs = scope["PAIRS"]
    for n in range(samples):
        draw = tuple(rng.sample(deck, 8))
        opp, board = draw[:3], draw[3:]
        flop = board[:3]
        a, b = pairs[pick(hole, flop)]
        c, d = pairs[pick(opp, flop, (0, 2, 2, 1)[n % 4])]
        value = scope["compare"](rank((hole[a], hole[b]) + board), rank((opp[c], opp[d]) + board))
        weight = scope["premium_weight"](opp)
        total += value
        weighted += weight * value
        weight_sum += weight
    return key, round(1000 * total / samples), round(1000 * weighted / weight_sum)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--samples", type=int, default=512)
    p.add_argument("--jobs", type=int, default=8)
    args = p.parse_args()
    representatives = {scope["preflop_key"](cards): cards for cards in combinations(range(52), 3)}
    jobs = [(k, v, args.samples) for k, v in sorted(representatives.items())]
    with ProcessPoolExecutor(args.jobs) as pool:
        result = list(pool.map(train, jobs, chunksize=12))
    lines = [f"    {key}: ({uniform}, {premium})," for key, uniform, premium in result]
    Path("src/preflop_table.py").write_bytes((
        f"# {args.samples} original rollouts per suit class, seed 432983 + key.\n" +
        "PREFLOP_EQUITY = {\n" + "\n".join(lines) + "\n}\n").encode())
    print(f"{len(result)} classes, {args.samples} samples each")

if __name__ == "__main__":
    main()

