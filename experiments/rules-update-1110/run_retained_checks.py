"""Validate the exact retained submission after the two-leg comparison."""
import json
from pathlib import Path
import subprocess
import sys
import time

commands = [[sys.executable, "-B", "tests/"+name+".py", "dist/bot.py"] for name in
            ("leg_compatibility", "protocol", "selection", "evaluator", "learning", "review_decisions", "optimization")]
commands.append([sys.executable, "-B", "-S", "tests/leg_compatibility.py", "dist/bot.py"])
with Path("experiments/rules-update-1110/retained-linux-checks.jsonl").open("x",encoding="utf8") as file:
    for command in commands:
        start=time.perf_counter()
        result=subprocess.run(command,capture_output=True,text=True,timeout=180)
        row=dict(command=command,exit_code=result.returncode,wall_s=time.perf_counter()-start,
                 stdout=result.stdout,stderr=result.stderr)
        file.write(json.dumps(row)+"\n");file.flush()
        print(command[2:],result.returncode,flush=True)
        if result.returncode:
            print(result.stdout,result.stderr,flush=True)
            raise SystemExit(result.returncode)
