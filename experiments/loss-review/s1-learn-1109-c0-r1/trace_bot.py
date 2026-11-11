BOT_PATH = '/mnt/c/Users/varun/OneDrive/Documents/ChatGPT/PokerBots/checkpoints/learning-v5.py'
TRACE_PATH = '/mnt/c/Users/varun/OneDrive/Documents/ChatGPT/PokerBots/experiments/loss-review/s1-learn-1109-c0-r1/trace.jsonl'

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
