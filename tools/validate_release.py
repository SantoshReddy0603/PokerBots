"""Validate the exact artifact with real full matches under host resource limits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import match

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bot", default="dist/bot.py", type=Path)
    p.add_argument("--opponents", nargs=2, default=["opponents/final_aggro.py", "opponents/final_equity.py"])
    p.add_argument("--prefix", default="release-linux")
    p.add_argument("--seeds", nargs=2)
    p.add_argument("--engine-format", choices=("legacy", "legs"), default="legs")
    args = p.parse_args()
    play_match = match
    if args.engine_format == "legs":
        from benchmark_legs import match as play_match
    bot_path = args.bot
    original = bot_path.read_bytes()
    assert sys.version_info[:2] == (3, 11)
    assert 0 < len(original) <= 5_000_000
    compile(original, str(bot_path), "exec")
    for stage, opponent in enumerate(args.opponents, 1):
        seed = args.seeds[stage - 1] if args.seeds else f"{args.prefix}-s{stage}"
        row = play_match(str(bot_path), opponent, stage, seed, f"experiments/{args.prefix}-s{stage}")
        print(json.dumps(row), flush=True)
        bot = row["bots"][0]
        assert row["played"] == {1: 400, 2: 1000}[stage]
        assert not row["forfeits"] and not bot["notices"] and not bot["diagnostics"]
        assert bot["startup_to_first_reply_ms"] < 2000
        assert bot["bank_s"] < {1: 42, 2: 105}[stage]
        assert bot["p99_ms"] < 100 and bot["max_ms"] < 1000
        if args.engine_format == "legs":
            assert len(row["legs"]) == 2
            for leg in row["legs"]:
                assert leg["played"] == {1: 200, 2: 500}[stage]
                measured = leg["bots"][0]
                assert not measured["notices"] and not measured["diagnostics"]
                assert measured["bank_s"] < {1: 21, 2: 52.5}[stage]
                assert leg["wall_s"] < {1: 90, 2: 225}[stage]
    assert original == bot_path.read_bytes()
    print(json.dumps(dict(sha256=hashlib.sha256(original).hexdigest(), bytes=len(original),
                          python=sys.version, platform=sys.platform, engine_format=args.engine_format)))

if __name__ == "__main__":
    main()
