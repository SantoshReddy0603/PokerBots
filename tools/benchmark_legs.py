"""Measure the unmodified 2026-11-10 organizer runner, preserving both legs."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "vendor/Starter_Kit_2026_11_10/engine.py"
spec = importlib.util.spec_from_file_location("organizer_engine_1110", ENGINE_PATH)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.time = SimpleNamespace(monotonic=time.perf_counter)


class TimedBot(engine.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replies = []
        self.startup_ms = None

    def _read_stderr(self):
        while chunk := self.proc.stderr.read1(4096):
            self.stderr_bytes += len(chunk)
            if self.stderr_file and self.stderr_file.tell() < engine.STDERR_LIMIT:
                remaining = engine.STDERR_LIMIT - self.stderr_file.tell()
                self.stderr_file.write(chunk[:remaining])

    def wait_reply(self, wall_deadline):
        # Keep the official five-second grace on EVERY request. Report bank
        # increments separately from startup latency; do not silently change it.
        before = self.time_used_s
        result = super().wait_reply(wall_deadline)
        self.replies.append((self.time_used_s - before) * 1000)
        if self.startup_ms is None:
            self.startup_ms = (time.perf_counter() - self.launch_time) * 1000
        return result


engine.Bot = TimedBot


def bot_report(bot):
    times = sorted(bot.replies)
    return dict(path=bot.label, sha256=hashlib.sha256(Path(bot.path).read_bytes()).hexdigest(),
                notices=bot.notices, bank_s=bot.time_used_s, diagnostics=bot.stderr_bytes,
                startup_to_first_reply_ms=bot.startup_ms,
                p99_ms=times[math.ceil(.99 * len(times)) - 1] if times else None,
                max_ms=times[-1] if times else None)


class ReportMatch(engine.Match):
    def __init__(self, args):
        super().__init__(args)
        self.runs = []

    def launch(self, leg):
        bots = super().launch(leg)
        self.runs.append(dict(leg=leg + 1, played=0, net=0, processes=bots,
                              started=time.perf_counter()))
        return bots

    def log_hand(self, hand, seat_nets):
        run = self.runs[-1]
        run["played"] += 1
        run["net"] += seat_nets[0] if hand.bots[0].name == "A" else seat_nets[1]
        run["wall_s"] = time.perf_counter() - run["started"]
        super().log_hand(hand, seat_nets)

    def summary(self, totals, played, forfeits, forfeit_at):
        failed = {bot.name: reason for bot, reason in forfeits}
        delta = max(-self.cap, min(self.cap, totals[0]))
        if failed:
            delta = self.cap * (int("B" in failed) - int("A" in failed))
        legs = [dict(leg=r["leg"], played=r["played"], net=r["net"],
                     wall_s=r.get("wall_s", 0), bots=[bot_report(b) for b in r["processes"]])
                for r in self.runs]
        bots = []
        for index in (0, 1):
            parts = [leg["bots"][index] for leg in legs]
            row = dict(parts[0])
            for field in ("bank_s", "notices", "diagnostics"):
                row[field] = sum(p[field] for p in parts)
            for field in ("startup_to_first_reply_ms", "p99_ms", "max_ms"):
                values = [p[field] for p in parts if p[field] is not None]
                row[field] = max(values) if values else None
            bots.append(row)
        self.result = dict(seed=self.seed, played=played, scheduled_hands=self.hands,
                           net=totals[0], delta=delta,
                           points=1 if delta > 0 else 0 if delta < 0 else .5,
                           forfeits=failed, forfeit_at=forfeit_at, bots=bots, legs=legs)


def match(a, b, stage, seed, log_dir=""):
    args = argparse.Namespace(bot_a=a, bot_b=b, python=sys.executable, hands=None,
                              stage=stage, seed=seed, verbose=False, log_dir=log_dir,
                              no_time_limits=False)
    start = time.perf_counter()
    game = ReportMatch(args)
    game.run()
    return dict(stage=stage, wall_s=time.perf_counter() - start, **game.result)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--stage", type=int, choices=(1, 2), required=True)
    p.add_argument("--seed", required=True)
    p.add_argument("--log-dir", required=True)
    args = p.parse_args()
    print(json.dumps(match(**vars(args)), indent=2))
