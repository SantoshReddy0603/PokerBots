"""Development-only replay/trace harness. Never included in the submission."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from benchmark import match


WRAPPER = r'''
import json
import runpy
import sys
scope = runpy.run_path(BOT_PATH)
stream = open(TRACE_PATH, "w", buffering=1)
original_loads = json.loads
def capture(line, *args, **kwargs):
    message = original_loads(line, *args, **kwargs)
    stream.write(json.dumps({"input": message}) + "\n")
    return message
json.loads = capture
def profile(frame, event, arg):
    if event == "return" and frame.f_code.co_name == "posterior_action":
        local = frame.f_locals
        stream.write(json.dumps({"decision": {
            "hand": local["req"]["hand_id"], "street": local["req"]["street"],
            "equity": float(local["equity"]),
            "choices": [(list(k), float(v)) for k, v in local["choices"].items()],
            "chosen": list(arg), "model": [(list(k), v) for k, v in local["state"].model.cells.items()]
        }}) + "\n")
sys.setprofile(profile)
scope["main"]()
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bot", default="checkpoints/learning-v5.py")
    p.add_argument("--report", default="experiments/learning-v5-confirmation.jsonl")
    p.add_argument("--out", type=Path, default=Path("experiments/loss-review"))
    p.add_argument("--jobs", type=int, default=2)
    args = p.parse_args()
    rows = [json.loads(line) for line in Path(args.report).read_text().splitlines()]
    losses = [r for r in rows if r["candidate_points"] == 0]
    args.out.mkdir(parents=True, exist_ok=True)
    def play(row):
        label = f"s{row['stage']}-{row['seed']}-r{int(row['reverse'])}"
        folder = args.out / label
        folder.mkdir(exist_ok=False)
        wrapper = folder / "trace_bot.py"
        wrapper.write_text("BOT_PATH = " + repr(str(Path(args.bot).resolve())) + "\nTRACE_PATH = " +
                           repr(str((folder / "trace.jsonl").resolve())) + "\n" + WRAPPER)
        a, b = (row["opponent"], str(wrapper)) if row["reverse"] else (str(wrapper), row["opponent"])
        result = match(a, b, row["stage"], row["seed"], str(folder))
        result["reverse"] = row["reverse"]
        result["original_net"] = row["candidate_net"]
        result["candidate_net"] = result["net"] * (-1 if row["reverse"] else 1)
        (folder / "result.json").write_text(json.dumps(result, indent=2))
        return result
    with (args.out / "replays.jsonl").open("x") as file, ThreadPoolExecutor(args.jobs) as pool:
        for result in pool.map(play, losses):
            file.write(json.dumps(result) + "\n")
            file.flush()
            print(result["stage"], result["seed"], result["reverse"], result["original_net"],
                  "replayed", result["candidate_net"], flush=True)


if __name__ == "__main__":
    main()
