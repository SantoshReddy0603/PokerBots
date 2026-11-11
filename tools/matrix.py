"""Validate matrices against their recorded, immutable experiment configuration."""
import hashlib
from itertools import product
import json
import math
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def keys(meta):
    return set(product((1, 2), meta["seeds"], meta["opponents"], (False, True)))

def validate(meta, rows):
    for name in ("seeds", "opponents"):
        if not meta[name] or (name == "seeds" and len(set(meta[name])) != len(meta[name])):
            raise ValueError(f"invalid {name}")
    seen = {}
    expected = keys(meta)
    for row in rows:
        key = (row["stage"], row["seed"], row["opponent"], row["reverse"])
        if type(row["reverse"]) is not bool or key not in expected or key in seen:
            raise ValueError(f"unexpected or duplicate match {key}")
        stage, _, opponent, reverse = key
        hands = {1: 400, 2: 1000}[stage]
        expected_hashes = [meta["candidate_sha256"], meta["opponents"][opponent]]
        if reverse:
            expected_hashes.reverse()
        if [b["sha256"] for b in row["bots"]] != expected_hashes:
            raise ValueError(f"bot hash mismatch {key}")
        failed = row["forfeits"]
        played = row["played"]
        if (type(played) is not int or not 0 <= played <= hands or
            (played != hands) != bool(failed) or not set(failed) <= {"A", "B"}):
            raise ValueError(f"invalid completion {key}")
        delta = hands * (int("B" in failed) - int("A" in failed)) if failed else max(-hands, min(hands, row["net"]))
        points = 1 if delta > 0 else 0 if delta < 0 else .5
        sign = -1 if reverse else 1
        if (row["delta"], row["points"], row["candidate_delta"], row["candidate_points"], row["candidate_net"]) != (
                delta, points, sign * delta, 1 - points if reverse else points, sign * row["net"]):
            raise ValueError(f"invalid scoring {key}")
        for bot in row["bots"]:
            for metric in ("bank_s", "startup_to_first_reply_ms", "p99_ms", "max_ms", "notices", "diagnostics"):
                value = bot[metric]
                if value is None and failed:
                    continue
                if value is None or not math.isfinite(value) or value < 0:
                    raise ValueError(f"invalid {metric} {key}")
        if meta.get("engine_format") == "two-leg-2026-11-10":
            validate_legs(row, hands, expected_hashes)
        if not math.isfinite(row["wall_s"]) or row["wall_s"] < 0:
            raise ValueError(f"invalid wall time {key}")
        seen[key] = row
    if seen.keys() != expected:
        raise ValueError(f"incomplete matrix: {len(seen)}/{len(expected)}")
    return seen


def validate_legs(row, hands, hashes):
    """Never hide a failed/slow first leg behind a valid second-leg summary."""
    legs = row.get("legs", [])
    failed = bool(row["forfeits"])
    if row.get("scheduled_hands") != hands or not 1 <= len(legs) <= 2:
        raise ValueError("invalid leg schedule")
    if not failed and (len(legs) != 2 or row.get("forfeit_at") is not None):
        raise ValueError("missing completed leg or spurious forfeit")
    if sum(leg["played"] for leg in legs) != row["played"] or sum(leg["net"] for leg in legs) != row["net"]:
        raise ValueError("leg totals disagree with match")
    for number, leg in enumerate(legs, 1):
        if leg["leg"] != number or type(leg["played"]) is not int or not 0 <= leg["played"] <= hands // 2:
            raise ValueError("invalid leg order or hand count")
        if (not failed or number < len(legs)) and leg["played"] != hands // 2:
            raise ValueError("incomplete leg")
        if [b["sha256"] for b in leg["bots"]] != hashes:
            raise ValueError("leg bot hash mismatch")
        for bot in leg["bots"]:
            for field in ("bank_s", "startup_to_first_reply_ms", "p99_ms", "max_ms", "notices", "diagnostics"):
                value = bot[field]
                if value is None and failed:
                    continue
                if value is None or not math.isfinite(value) or value < 0:
                    raise ValueError("invalid leg resource metric")
            if not failed and (bot["bank_s"] > hands * .075 or bot["max_ms"] > 5000):
                raise ValueError("completed leg exceeded resource limit")
    for index, aggregate in enumerate(row["bots"]):
        for field in ("bank_s", "notices", "diagnostics"):
            if not math.isclose(aggregate[field], sum(l["bots"][index][field] for l in legs), abs_tol=1e-9):
                raise ValueError("aggregate leg metrics disagree")
    if failed:
        where = row.get("forfeit_at")
        if not where or where[0] != len(legs) or not 1 <= where[1] <= hands // 2:
            raise ValueError("invalid leg forfeit location")

def read(path):
    path = Path(path)
    meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return meta, validate(meta, rows)

