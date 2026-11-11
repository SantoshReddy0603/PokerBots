"""Full 400-hand coverage checks; single assignment, not a paired selection test."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import platform
import sys
from benchmark import match
from matrix import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bot")
    p.add_argument("--peer-dir", type=Path)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--seed", required=True)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    if args.jobs < 1:
        p.error("jobs must be positive")
    opponents = [path for path in sorted(Path("opponents").glob("*.py"))
                 if path.name != "league_policy.py"]
    if args.peer_dir:
        opponents.extend(path for path in sorted(args.peer_dir.glob("*.py")) if not path.name.startswith("_"))
    meta = dict(candidate=args.bot, sha256=digest(args.bot), stage=1,
                seed=args.seed, python=sys.version, platform=platform.platform(),
                jobs=args.jobs, assignment="candidate A only; coverage diagnostic",
                opponents={p.as_posix(): digest(p) for p in opponents},
                harness={p: digest(p) for p in ("tools/screen_pool.py", "tools/benchmark.py", "vendor/Starter_Kit/engine.py")})
    with args.out.with_suffix(".meta.json").open("x") as file:
        json.dump(meta, file, indent=2)
    def play(path):
        return dict(opponent=path.as_posix(), **match(args.bot, str(path), 1, args.seed))
    with args.out.open("x") as file, ThreadPoolExecutor(args.jobs) as pool:
        for result in pool.map(play, opponents):
            file.write(json.dumps(result) + "\n")
            file.flush()
            print(result["opponent"], result["net"], result["forfeits"], flush=True)


if __name__ == "__main__":
    main()
