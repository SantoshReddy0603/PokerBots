"""Development-only match runner using the untouched organizer rules."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "Starter_Kit"))
import engine

# perf_counter avoids the coarse Windows monotonic tick used by the reference.
engine.time = SimpleNamespace(monotonic=time.perf_counter)

class TimedBot(engine.Bot):
    def __init__(self, *args):
        super().__init__(*args)
        self.replies = []
        self.startup_ms = None

    def _read_stderr(self):
        while chunk := self.proc.stderr.read1(4096):
            self.stderr_bytes += len(chunk)
            if self.stderr_file and self.stderr_file.tell() < engine.STDERR_LIMIT:
                remaining = engine.STDERR_LIMIT - self.stderr_file.tell()
                self.stderr_file.write(chunk[:remaining])

    def wait_reply(self, wall_deadline):
        # First response can include interpreter launch. Charge all subsequent
        # requests even if the entire match fits within the five-second grace.
        if self.replies:
            self.startup_deadline = 0
        previous = self.time_used_s
        line, error = super().wait_reply(wall_deadline)
        if self.startup_ms is None:
            self.startup_ms = (time.perf_counter() - self.launch_time) * 1000
        else:
            self.replies.append((self.time_used_s - previous) * 1000)
            return line, error
        self.replies.append(0.0)
        return line, error

class ReportMatch(engine.Match):
    def summary(self, totals, played, forfeits):
        failed = {bot.name: reason for bot, reason in forfeits}
        net = totals[0]
        delta = max(-self.cap, min(self.cap, net))
        if failed:
            delta = self.cap * (int("B" in failed) - int("A" in failed))
        reports = []
        for bot in self.bots:
            times = sorted(bot.replies[1:])
            reports.append(dict(path=bot.label, sha256=hashlib.sha256(Path(bot.path).read_bytes()).hexdigest(),
                                notices=bot.notices, bank_s=bot.time_used_s,
                                startup_to_first_reply_ms=bot.startup_ms,
                                diagnostics=bot.stderr_bytes,
                                p99_ms=times[math.ceil(.99 * len(times)) - 1] if times else None,
                                max_ms=times[-1] if times else None))
        self.result = dict(seed=self.seed, played=played, net=net, delta=delta,
                           points=1 if delta > 0 else 0 if delta < 0 else .5,
                           forfeits=failed, bots=reports)

def match(a, b, stage, seed, log_dir=""):
    engine.Bot = TimedBot
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
    p.add_argument("--stage", type=int, required=True)
    p.add_argument("--seed", required=True)
    p.add_argument("--log-dir", required=True)
    args = p.parse_args()
    print(json.dumps(match(**vars(args)), indent=2))
