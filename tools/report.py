"""Summarize complete match matrices and their resource observations."""
import argparse
import json
from pathlib import Path
from statistics import mean

def summarize(rows):
    for stage, hands in [(1, 400), (2, 1000)]:
        matches = [r for r in rows if r["stage"] == stage]
        if not matches:
            continue
        reports = [r["bots"][int(r["reverse"])] for r in matches]
        points = [r["candidate_points"] for r in matches]
        totals = [r["delta"] * (-1 if r["reverse"] else 1) for r in matches]
        print(json.dumps(dict(
            stage=stage, matches=len(matches), win_draw_loss=[points.count(x) for x in (1, .5, 0)],
            mean_points=mean(points), raw_chips_per_hand=sum(r["candidate_net"] for r in matches) /
            sum(max(1, r["played"]) for r in matches), capped_chips_per_hand=mean(totals) / hands,
            incomplete=sum(r["played"] != hands for r in matches),
            forfeits=sum(bool(r["forfeits"]) for r in matches),
            notices=sum(b["notices"] for b in reports), stderr_bytes=sum(b["diagnostics"] for b in reports),
            max_startup_ms=max(b["startup_to_first_reply_ms"] for b in reports),
            max_bank_s=max(b["bank_s"] for b in reports),
            worst_match_p99_ms=max(b["p99_ms"] or 0 for b in reports),
            max_reply_ms=max(b["max_ms"] or 0 for b in reports))))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file")
    args = p.parse_args()
    summarize(list(map(json.loads, Path(args.file).read_text(encoding="utf-8").splitlines())))

