"""Fill remaining field edges with full clocked matches."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations, product
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import match

def play(job):
    (a, b), stage, reverse = job
    if reverse:
        a, b = b, a
    return match(a, b, stage, "field-peer-0")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("bots", nargs="+")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    jobs = product(combinations(args.bots, 2), (1, 2), (False, True))
    with Path(args.out).open("x") as out, ThreadPoolExecutor(args.jobs) as pool:
        for row in pool.map(play, jobs):
            out.write(json.dumps(row) + "\n")
            out.flush()

if __name__ == "__main__":
    main()

