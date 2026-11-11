"""Validate the recorded rule-update study and write its reproducible summary."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("tools").resolve()))
from matrix import read, digest

root = Path("experiments/rules-update-1110")
parser = argparse.ArgumentParser()
parser.add_argument("--validate-only", action="store_true", help="check frozen evidence without replacing summary.json")
args = parser.parse_args()
summary = dict(date_ist="2026-11-10", decision="retain existing release; candidate not promoted",
               seed_blocks=1, block_confidence_interval=None, comparisons={})
for name in ("candidate", "baseline"):
    meta, indexed = read(root/(name+".jsonl"))
    rows = list(indexed.values())
    assert all(digest(path) == expected for path,expected in meta["harness"].items())
    assert all(digest(path) == expected for path,expected in meta["opponents"].items())
    stats = dict(sha256=meta["candidate_sha256"], wins=sum(r["candidate_points"]==1 for r in rows),
                 draws=sum(r["candidate_points"]==.5 for r in rows), losses=sum(r["candidate_points"]==0 for r in rows),
                 forfeits=sum(bool(r["forfeits"]) for r in rows), wall_s_sum=sum(r["wall_s"] for r in rows),
                 by_opponent={}, by_stage={})
    for opponent in meta["opponents"]:
        group=[r for r in rows if r["opponent"]==opponent]
        stats["by_opponent"][opponent]=[sum(r["candidate_points"]==p for r in group) for p in (1,.5,0)]
    for stage in (1,2):
        group=[r for r in rows if r["stage"]==stage]
        bots=[leg["bots"][int(r["reverse"])] for r in group for leg in r["legs"]]
        stats["by_stage"][stage]=dict(wdl=[sum(r["candidate_points"]==p for r in group) for p in (1,.5,0)],
                                             max_leg_bank_s=max(b["bank_s"] for b in bots),
                                             max_reply_ms=max(b["max_ms"] for b in bots),
                                             notices=sum(b["notices"] for b in bots),
                                             diagnostics=sum(b["diagnostics"] for b in bots))
    summary["comparisons"][name]=stats
summary["stress"]={}
for name in ("stress", "retained-stress"):
    rows=[json.loads(line) for line in (root/(name+".jsonl")).read_text().splitlines()]
    assert len(rows)==3
    summary["stress"][name]=rows
for file in ("checks.jsonl", "retained-linux-checks.jsonl", "retained-checks.jsonl"):
    rows=[json.loads(line) for line in (root/file).read_text().splitlines()]
    assert all(row["exit_code"]==0 for row in rows)
    summary[file]=dict(count=len(rows),wall_s=sum(row["wall_s"] for row in rows))
manifest=json.loads((root/"retained.release.json").read_text())
# A separate later daily task may promote a new release. This study describes
# the frozen rule-update artifacts; never overwrite or relabel that later work.
assert manifest["sha256"]==digest("checkpoints/pre-rules-1110.py")
assert all(digest(root/"frozen-sources"/Path(path).name)==expected
           for path,expected in manifest["source_sha256"].items())
assert digest("checkpoints/rules-1110.py")==digest("checkpoints/rules-1110-rebuild.py")
assert manifest["sha256"]==digest("checkpoints/rules-1110-retained-rebuild.py")
supplied=json.loads((root/"sources.json").read_text())
assert all(digest(path)==expected for path,expected in supplied.items())
summary["selected_manifest"]=manifest
if not args.validate_only:
    with (root/"summary.json").open("x",encoding="utf8") as file:
        json.dump(summary,file,indent=2)
print(json.dumps({k:{f:v[f] for f in ('wins','draws','losses','by_opponent','by_stage')} for k,v in summary['comparisons'].items()},indent=2))
