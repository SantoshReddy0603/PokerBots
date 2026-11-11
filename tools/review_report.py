"""Validate completed review matrices and archive paired comparisons without overwrites."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from matrix import read

p = argparse.ArgumentParser()
p.add_argument("phase", choices=["screen", "confirmation", "research"])
args = p.parse_args()
root = Path("experiments/review-fixes-1109")
profiles = {"screen": ["baseline", "bets", "reraises", "openings", "combined"],
            "confirmation": ["baseline", "openings"],
            "research": ["combined", "sampling-exp", "ranges-exp"]}[args.phase]
summary = {}
for profile in profiles:
    path = root / f"{args.phase}-{profile}.jsonl"
    meta, matrix = read(path)
    rows = list(matrix.values())
    bots = [r["bots"][int(r["reverse"])] for r in rows]
    summary[profile] = dict(sha256=meta["candidate_sha256"], matches=len(rows),
                           WDL=[sum(r["candidate_points"] == value for r in rows) for value in (1, .5, 0)],
                           failures=sum(bool(r["forfeits"]) for r in rows),
                           notices=sum(b["notices"] for b in bots), diagnostics=sum(b["diagnostics"] for b in bots),
                           runtime_by_stage={str(s): dict(
                               bank_max=max(r["bots"][int(r["reverse"])]["bank_s"] for r in rows if r["stage"] == s),
                               response_max=max(r["bots"][int(r["reverse"])]["max_ms"] for r in rows if r["stage"] == s))
                               for s in (1, 2)},
                           opponents={opponent: {str(s): [sum(r["candidate_points"] == v for r in rows
                                                                          if r["opponent"] == opponent and r["stage"] == s)
                                                         for v in (1, .5, 0)] for s in (1, 2)}
                                      for opponent in meta["opponents"]})
    if profile != profiles[0]:
        cmd = [sys.executable, "tools/compare.py", str(path), str(root / f"{args.phase}-{profiles[0]}.jsonl")]
        report = subprocess.run(cmd, text=True, capture_output=True, check=True)
        with (root / f"{args.phase}-{profile}-comparison.txt").open("x") as file:
            file.write(report.stdout)
with (root / f"{args.phase}-summary.json").open("x") as file:
    json.dump(summary, file, indent=2)
for name, row in summary.items():
    print(name, row["WDL"], "failures/notices/diagnostics", row["failures"], row["notices"], row["diagnostics"])
