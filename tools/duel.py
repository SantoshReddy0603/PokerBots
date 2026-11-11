"""Summarize a validated head-to-head matrix by whole deal seed blocks."""
import argparse
from pathlib import Path
from random import Random
from statistics import mean
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matrix import read

def main():
    p = argparse.ArgumentParser()
    p.add_argument("report")
    args = p.parse_args()
    meta, rows = read(args.report)
    if len(meta["opponents"]) != 1:
        p.error("expected one opponent")
    rng = Random(414)
    for stage in (1, 2):
        selected = [row for row in rows.values() if row["stage"] == stage]
        blocks = [mean(row["candidate_points"] for row in selected if row["seed"] == seed)
                  for seed in meta["seeds"]]
        draws = sorted(mean(rng.choices(blocks, k=len(blocks))) for _ in range(4000))
        print(stage, "W/D/L", [sum(r["candidate_points"] == p for r in selected) for p in (1, .5, 0)],
              "points per seed", blocks, "conditional 95% interval", [draws[100], draws[3899]],
              "capped chips/hand", round(mean(r["candidate_delta"] for r in selected) / {1: 400, 2: 1000}[stage], 4),
              "max bank", round(max(r["bots"][int(r["reverse"])]["bank_s"] for r in selected), 3),
              "failures", sum(bool(r["forfeits"]) for r in selected),
              "notices/diagnostic bytes", sum(b["notices"] for r in selected for b in r["bots"]),
              sum(b["diagnostics"] for r in selected for b in r["bots"]))

if __name__ == "__main__":
    main()

