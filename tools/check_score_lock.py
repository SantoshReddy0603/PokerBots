"""Audit completed local stress logs against the capped-lead guarantee."""
import argparse
from pathlib import Path
import re

def check(path, hands, alternating_blinds=False, late_win=False):
    net = 0
    locked_at = None
    locked_target = hands
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == hands, (path, len(lines))
    for index, line in enumerate(lines, 1):
        remaining = hands - index + 1
        cost = 2 * remaining
        if alternating_blinds:
            button = re.search(r"button ([AB]) \|", line)
            assert button, line
            cost = 3 * (remaining // 2) + (remaining % 2) * (1 if button[1] == "A" else 2)
        target = 1 if late_win and index > .9 * hands else hands
        if locked_at is None and net - cost >= target:
            locked_at = index
            locked_target = target
        assert line.startswith(f"#{index} ")
        match = re.search(r"\bA ([+-]\d+), B [+-]\d+$|\bB [+-]\d+, A ([+-]\d+)$", line)
        assert match, line
        result = int(match[1] or match[2])
        if locked_at is not None:
            history = line.split(" | ")[-2]
            assert result >= -2 and not re.search(r"\bA[cr]\d+", history), (index, result, history)
        net += result
    if locked_at is not None:
        assert net >= locked_target
    print(path, "locked from", locked_at, "target", locked_target, "final net", net)
    return locked_at

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("prefix")
    p.add_argument("--alternating-blinds", action="store_true")
    p.add_argument("--late-win", action="store_true")
    args = p.parse_args()
    locks = [check(f"experiments/{args.prefix}-s{stage}/match.log", hands, args.alternating_blinds, args.late_win)
             for stage, hands in ((1, 400), (2, 1000))]
    assert any(locks), "neither stress match exercised lead protection"

