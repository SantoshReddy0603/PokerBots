"""Concatenate the modules in src/ into the single-file submission bot.py."""
import argparse
from pathlib import Path

SOURCES = [
    "src/learning_protocol.py", "src/poker.py", "src/preflop_key.py",
    "src/preflop_table.py", "src/event_ranges.py", "src/learning.py",
    "src/selective_equity.py", "src/pure_equity.py", "src/learning_policy.py",
    "src/range_engine.py", "src/main_loop.py",
]

p = argparse.ArgumentParser()
p.add_argument("--output", default="bot.py")
args = p.parse_args()

body = "\n\n".join(Path(path).read_text(encoding="utf-8-sig").strip() for path in SOURCES)
body += '\n\nif __name__ == "__main__":\n    main()\n'
compile(body, args.output, "exec")
data = body.encode("utf-8")
if len(data) > 5_000_000:
    raise ValueError("submission exceeds 5 MB")
Path(args.output).write_bytes(data)
