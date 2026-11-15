import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--output", default="dist/bot.py")
p.add_argument("--policy")
p.add_argument("--extra", action="append", default=[])
p.add_argument("--protocol")
p.add_argument("--deterministic-samples", action="store_true", help="development only; external match clocks stay enabled")
args = p.parse_args()
if args.protocol or args.policy or args.extra:
    sources = [args.protocol or "src/protocol.py", "src/poker.py", *args.extra,
               args.policy or "src/policy.py"]
else:
    sources = ["src/learning_protocol.py", "src/poker.py", "src/preflop_key.py",
               "src/preflop_table.py", "src/event_ranges.py", "src/learning.py",
               "src/selective_equity.py", "src/pure_equity.py", "src/learning_policy.py",
               "src/range_engine.py", "src/main_loop.py"]
# Experimental policies share exactly one bet-size definition when bundled.
if any(Path(path).name in {"context_learning.py", "uncertainty_policy.py", "review_learning.py", "review_policy.py"}
       for path in sources) and "src/bet_features.py" not in sources:
    sources.insert(1, "src/bet_features.py")
body = "\n\n".join(Path(path).read_text(encoding="utf-8-sig").strip() for path in sources)
if args.deterministic_samples:
    if Path(args.output).resolve().is_relative_to(Path("dist").resolve()):
        p.error("deterministic sample builds must stay outside dist")
    body += "\n\ndef perf_counter():\n    return 0.0  # Development-only sample counts\n"
body += '\n\nif __name__ == "__main__":\n    main()\n'
output = Path(args.output)
compile(body, str(output), "exec")
data = body.encode("utf-8")
if len(data) > 5_000_000:
    raise ValueError("submission exceeds 5 MB")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(data)
