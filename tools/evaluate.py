import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import platform
import subprocess
from pathlib import Path
from random import Random
from statistics import mean
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import match
from matrix import digest, validate

def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidate")
    p.add_argument("opponents", nargs="+")
    p.add_argument("--split", required=True)
    p.add_argument("--manifest", default="experiments/seeds.json")
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--out", required=True)
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--engine-format", choices=("legacy", "legs"), default="legs",
                   help="updated two-leg engine by default; legacy reproduces archived studies")
    args = p.parse_args()
    play_match = match
    if args.engine_format == "legs":
        from benchmark_legs import match as play_match
    available = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))[args.split]
    if not 0 < args.count <= len(available) or len(set(available)) != len(available):
        p.error("seed split is empty, duplicated, or smaller than requested count")
    if args.jobs < 1 or len(set(args.opponents)) != len(args.opponents):
        p.error("invalid concurrency or duplicate opponents")
    seeds = available[:args.count]
    output = Path(args.out)
    jobs = [(opp, stage, seed, reverse) for opp in args.opponents for stage in (1, 2)
            for seed in seeds for reverse in (False, True)]

    def play(job):
        opp, stage, seed, reverse = job
        a, b = (opp, args.candidate) if reverse else (args.candidate, opp)
        result = play_match(a, b, stage, seed)
        return dict(opponent=opp, reverse=reverse, candidate_net=result["net"] * (-1 if reverse else 1),
                    candidate_delta=result["delta"] * (-1 if reverse else 1),
                    candidate_points=1 - result["points"] if reverse else result["points"], **result)

    meta = dict(seeds=seeds, candidate=args.candidate, candidate_sha256=digest(args.candidate),
                opponents={opponent: digest(opponent) for opponent in args.opponents},
                python=sys.version, platform=platform.platform(), jobs=args.jobs,
                revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                clock="production-time-adaptive", policy_rng="embedded in hashed bot sources",
                harness={str(path): digest(path) for path in
                         ("tools/benchmark.py", "tools/evaluate.py", "tools/matrix.py", "vendor/Starter_Kit/engine.py")},
                manifest=args.manifest, manifest_sha256=digest(args.manifest), split=args.split)
    if args.engine_format == "legs":
        meta["engine_format"] = "two-leg-2026-11-10"
        meta["clock"] = "official-per-leg-startup-grace-production-time-adaptive"
        meta["harness"] = {str(path): digest(path) for path in
                           ("tools/benchmark_legs.py", "tools/evaluate.py", "tools/matrix.py",
                            "vendor/Starter_Kit_2026_11_10/engine.py")}
    if output.exists():
        p.error("output already exists")
    with output.with_suffix(".meta.json").open("x", encoding="utf-8") as file:
        json.dump(meta, file, indent=2)
    rows = []
    with output.open("x", encoding="utf-8") as file, ThreadPoolExecutor(args.jobs) as pool:
        for row in pool.map(play, jobs):
            file.write(json.dumps(row) + "\n")
            file.flush()
            rows.append(row)
    validate(meta, rows)
    summarize(rows)

def summarize(rows):
    rng = Random(31)
    for stage in (1, 2):
        for opponent in sorted({r["opponent"] for r in rows}):
            group = [r for r in rows if r["stage"] == stage and r["opponent"] == opponent]
            points = [r["candidate_points"] for r in group]
            pairs = [mean(r["candidate_net"] / max(1, r["played"]) for r in group if r["seed"] == s)
                     for s in sorted({r["seed"] for r in group})]
            boot = sorted(mean(rng.choices(pairs, k=len(pairs))) for _ in range(3000))
            bots = [r["bots"][int(r["reverse"])] for r in group]
            print(stage, opponent, "W/D/L", [points.count(x) for x in (1, .5, 0)],
                  "chips/hand", round(mean(pairs), 3), "seed bootstrap 95%",
                  [round(boot[i], 3) for i in (75, 2924)], "bank max",
                  round(max(b["bank_s"] for b in bots), 2), "notices",
                  sum(b["notices"] for b in bots), "forfeits", sum(bool(r["forfeits"]) for r in group))

if __name__ == "__main__":
    main()
