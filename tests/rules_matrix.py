"""Reject missing/misreported legs and incorrect whole-match forfeit scoring."""
import copy
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path("tools").resolve()))
from matrix import validate

fixture = runpy.run_path("tests/review_matrix.py")
meta, rows = copy.deepcopy(fixture["meta"]), copy.deepcopy(fixture["rows"])
meta["engine_format"] = "two-leg-2026-11-10"
for row in rows:
    row.update(scheduled_hands=row["played"], forfeit_at=None)
    row["legs"] = [dict(leg=i, played=row["played"]//2, net=0, wall_s=.5,
                        bots=[dict(b, bank_s=b["bank_s"]/2) for b in row["bots"]]) for i in (1,2)]
assert len(validate(meta, rows)) == 4
mutations = [
    lambda r:r["legs"].pop(0),
    lambda r:r["legs"][0].update(played=1),
    lambda r:r["legs"][0]["bots"][0].update(bank_s=31),
    lambda r:r["legs"][0]["bots"][0].update(diagnostics=-1),
    lambda r:r["legs"][0]["bots"][0].update(sha256="wrong"),
    lambda r:r["legs"][0].update(net=99),
    lambda r:r.update(scheduled_hands=200),
    lambda r:r["bots"][0].update(bank_s=2),
]
for mutate in mutations:
    broken=copy.deepcopy(rows)
    mutate(broken[0])
    try: validate(meta, broken)
    except ValueError: pass
    else: raise AssertionError("accepted corrupt leg")
failed=copy.deepcopy(rows)
row=failed[0]
row.update(played=0, forfeits={"A":"fixture"}, forfeit_at=[1,1], delta=-400,
           points=0, candidate_delta=-400, candidate_points=0)
row["legs"]=row["legs"][:1]
row["legs"][0]["played"]=0
row["bots"]=[dict(b) for b in row["legs"][0]["bots"]]
assert validate(meta, failed)
row["scheduled_hands"]=0
try: validate(meta, failed)
except ValueError: pass
else: raise AssertionError("forfeit denominator must be scheduled hands")
print("Both-leg totals, hashes, resources, completeness and scheduled-hand forfeit fixtures passed")
