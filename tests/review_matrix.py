import copy
from pathlib import Path
import sys

sys.path.insert(0, str(Path("tools").resolve()))
from matrix import validate

meta = dict(seeds=["fixture"], opponents={"rival": "b"}, candidate_sha256="a")
bot = dict(bank_s=1, startup_to_first_reply_ms=10, p99_ms=1, max_ms=2, notices=0, diagnostics=0)
rows = []
for stage, hands in ((1, 400), (2, 1000)):
    for reverse in (False, True):
        rows.append(dict(stage=stage, seed="fixture", opponent="rival", reverse=reverse,
                         played=hands, net=0, delta=0, points=.5, candidate_net=0,
                         candidate_delta=0, candidate_points=.5, forfeits={}, wall_s=1.,
                         bots=[dict(bot, sha256=sha) for sha in ("ba" if reverse else "ab")]))
assert len(validate(meta, rows)) == 4
for bad in (rows[:-1], rows + rows[:1],
            [dict(rows[0], played=399), *rows[1:]],
            [dict(rows[0], candidate_delta=2), *rows[1:]]):
    try:
        validate(meta, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted broken matrix")
corrupt = copy.deepcopy(rows)
corrupt[0]["bots"].reverse()
try:
    validate(meta, corrupt)
except ValueError:
    pass
else:
    raise AssertionError("accepted incorrect assignments")
print("complete, missing, duplicate, scoring and assignment matrix fixtures passed")

