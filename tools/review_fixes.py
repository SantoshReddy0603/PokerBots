"""Build isolated review candidates; run fresh, non-overwriting paired matrices."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path("experiments/review-fixes-1109")
PROFILES = {"bets": (True, False, False), "reraises": (False, True, False),
            "openings": (False, False, True), "combined": (True, True, True)}


def build():
    recipes = ROOT / "recipes"
    recipes.mkdir(exist_ok=True)
    for name, flags in PROFILES.items():
        config = recipes / (name + ".py")
        with config.open("x") as file:
            for key, value in zip(("FIX_BET_SIZES", "FIX_RERAISES", "FIX_OPENINGS"), flags):
                file.write(f"{key} = {value!r}\n")
        output = f"checkpoints/review-1109-{name}.py"
        if Path(output).exists():
            raise FileExistsError(output)
        sources = ["src/learning_protocol.py", "src/poker.py", "src/preflop_key.py",
                   "src/preflop_table.py", "src/bet_features.py", str(config), "src/review_ranges.py",
                   "src/review_learning.py", "src/review_equity.py", "src/review_policy.py"]
        body = "\n\n".join(Path(p).read_text(encoding="utf-8-sig").strip() for p in sources)
        body += '\n\nif __name__ == "__main__":\n    main()\n'
        compile(body, output, "exec")
        Path(output).write_bytes(body.encode())
        with (recipes / (name + ".json")).open("x") as file:
            json.dump(dict(output=output, sources={p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                                  for p in sources},
                           sha256=hashlib.sha256(body.encode()).hexdigest()), file, indent=2)
    tight_sources = ["src/protocol.py", "src/poker.py", "src/preflop_key.py",
                     "src/preflop_table.py", "tools/review_tight_policy.py"]
    tight = ROOT / "tight_reraise.py"
    with tight.open("x") as file:
        file.write("\n\n".join(Path(p).read_text().strip() for p in tight_sources) +
                   '\n\nif __name__ == "__main__":\n    main()\n')
    seeds = dict(screen=["reviewfix-1109-screen-a", "reviewfix-1109-screen-b"],
                 confirmation=[f"reviewfix-1109-holdout-{i}" for i in range(4)],
                 research=["reviewfix-1109-research-a", "reviewfix-1109-research-b"])
    with (ROOT / "seeds.json").open("x") as file:
        json.dump(seeds, file, indent=2)


def run(args):
    pool = ["opponents/league/confirmation/trap.py", str(ROOT / "tight_reraise.py"),
            "opponents/league/confirmation/pressure.py",
            "experiments/friend-review/pokerbots-discard-holdem-main/bot.py"]
    def evaluate(name):
        bot = "checkpoints/review-1109-fallback.py" if name == "baseline" else f"checkpoints/review-1109-{name}.py"
        out = ROOT / f"{args.phase}-{name}.jsonl"
        cmd = [sys.executable, "-B", "tools/evaluate.py", bot, *pool, "--manifest", str(ROOT / "seeds.json"),
               "--split", args.phase, "--count", str(args.count), "--jobs", str(args.jobs), "--out", str(out)]
        with out.with_suffix(".stdout.txt").open("x") as stdout, out.with_suffix(".stderr.txt").open("x") as stderr:
            subprocess.run(cmd, stdout=stdout, stderr=stderr, check=True)
        print(name, "complete", flush=True)
    with ThreadPoolExecutor(args.parallel) as executor:
        list(executor.map(evaluate, args.candidates))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["build", "run"])
    p.add_argument("--phase", choices=["screen", "confirmation", "research"], default="screen")
    p.add_argument("--candidates", nargs="+", default=["baseline", *PROFILES])
    p.add_argument("--count", type=int, default=2)
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--parallel", type=int, default=3)
    args = p.parse_args()
    build() if args.action == "build" else run(args)
