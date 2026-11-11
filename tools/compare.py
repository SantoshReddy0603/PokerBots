"""Compare validated matrices, keeping assignments and opponents inside seed blocks."""
import argparse
from pathlib import Path
from random import Random
import sys
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matrix import read

def compare(meta_a, a, meta_b, b, excluded_opponents=()):
    excluded = {"candidate", "candidate_sha256"}
    if {k: v for k, v in meta_a.items() if k not in excluded} != {
            k: v for k, v in meta_b.items() if k not in excluded} or a.keys() != b.keys():
        raise ValueError("experiment configurations or match matrices differ")
    if not set(excluded_opponents) <= meta_a["opponents"].keys():
        raise ValueError("unrecognized excluded opponent")
    included = [o for o in meta_a["opponents"] if o not in excluded_opponents]
    if not included:
        raise ValueError("no opponents left")
    if excluded_opponents:
        print("Explicitly excluded after matrix validation", list(excluded_opponents))
    rng = Random(42)
    for stage in (1, 2):
        rows = [k for k in sorted(a) if k[0] == stage and k[2] in included]
        def difference(key):
            x, y = a[key], b[key]
            return (x["candidate_points"] - y["candidate_points"],
                    (x["candidate_delta"] - y["candidate_delta"]) / {1: 400, 2: 1000}[stage],
                    (x["candidate_net"] - y["candidate_net"]) / {1: 400, 2: 1000}[stage])
        for opponent in included:
            group = [k for k in rows if k[2] == opponent]
            print(stage, opponent, "paired points/capped/raw", [round(mean(v), 4) for v in zip(*map(difference, group))])
        groups = [[difference(k) for k in rows if k[1] == seed] for seed in meta_a["seeds"]]
        for i, metric in enumerate(("match points", "capped chips/hand", "raw chips/hand")):
            blocks = [mean(x[i] for x in g) for g in groups]
            interval = None
            if len(blocks) > 1:
                draws = sorted(mean(rng.choices(blocks, k=len(blocks))) for _ in range(4000))
                interval = [round(draws[100], 4), round(draws[3899], 4)]
            print(stage, metric, round(mean(blocks), 4), "seed blocks", len(blocks), "95% bootstrap", interval)
        for name, matrix in (("candidate", a), ("reference", b)):
            bots = [matrix[k]["bots"][int(k[3])] for k in rows]
            print(stage, name, "W/D/L",
                  [sum(matrix[k]["candidate_points"] == x for k in rows) for x in (1, .5, 0)],
                  "max bank", round(max(bot["bank_s"] for bot in bots), 3),
                  "failures/notices/stderr", sum(bool(matrix[k]["forfeits"]) for k in rows),
                  sum(bot["notices"] for bot in bots), sum(bot["diagnostics"] for bot in bots))
        for dropped in included:
            remain = [difference(k)[0] for k in rows if k[2] != dropped]
            if remain:
                print(stage, "points without", dropped, round(mean(remain), 4))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--exclude-opponent", action="append", default=[])
    args = p.parse_args()
    compare(*read(args.a), *read(args.b), args.exclude_opponent)
