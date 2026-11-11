"""Reproduce the focused and applicable release checks; never rebuild dist."""
import json
from pathlib import Path
import subprocess
import sys
import time

artifact = "checkpoints/rules-1110.py"
commands = [[sys.executable, "-B", "tests/" + name + ".py", artifact]
            for name in ("rules_update", "protocol", "selection", "evaluator", "learning",
                         "review_decisions", "optimization")]
commands += [[sys.executable, "-B", "tests/optimization.py", artifact, "--timing-out",
              "experiments/rules-update-1110/optimization-timing.json"],
             [sys.executable, "-B", "tests/rules_matrix.py"],
             [sys.executable, "-B", "tests/review_findings.py"],
             [sys.executable, "-B", "tests/review_research.py"],
             [sys.executable, "-B", "tests/review_control.py"],
             [sys.executable, "-B", "-S", "tests/protocol.py", artifact]]
output = Path("experiments/rules-update-1110/checks.jsonl")
with output.open("x", encoding="utf8") as file:
    for command in commands:
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        row = dict(command=command, exit_code=result.returncode, wall_s=time.perf_counter()-start,
                   stdout=result.stdout, stderr=result.stderr)
        file.write(json.dumps(row)+"\n");file.flush()
        print(command[2:4], result.returncode, round(row["wall_s"],2), flush=True)
        if result.returncode:
            print(result.stdout, result.stderr, flush=True)
            raise SystemExit(result.returncode)
