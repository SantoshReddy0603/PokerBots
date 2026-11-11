"""Run the exact lock-only artifact through a capped-lead protocol transcript."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

bot = Path(sys.argv[1]).resolve()
messages = [dict(type="init", protocol_version="1.0", small_blind=1, big_blind=2,
                 total_hands=400, per_response_ms=5000)]
cards = ["As", "Ah", "Ad"]
for hand in range(1, 7):
    messages += [dict(type="new_hand", hand_id=hand, seat="big_blind", hole_cards=cards),
                 dict(type="hand_result", hand_id=hand, net=200)]
messages.append(dict(type="new_hand", hand_id=7, seat="big_blind", hole_cards=cards))
request = dict(type="action_request", hand_id=7, street="preflop", board=[],
               pot=4, my_bet=2, opp_bet=2, to_call=0, my_stack=198, opp_stack=198,
               history=[], time_left_ms=50000, min_raise=4, max_raise=200)
messages.extend([
    dict(request, legal_actions=["check", "raise"]),
    dict(request, legal_actions=["fold", "call", "raise"], pot=16, to_call=12, opp_bet=14),
    dict(type="discard_request", hand_id=7, board=["2s", "3c", "4d"],
         hole_cards=cards, time_left_ms=50000),
    dict(type="match_end"),
])
with tempfile.TemporaryDirectory() as folder:
    copy = Path(folder) / "bot.py"
    copy.write_bytes(bot.read_bytes())
    result = subprocess.run([sys.executable, str(copy)], input="\n".join(map(json.dumps, messages)),
                            cwd=folder, text=True, capture_output=True, timeout=5, check=True)
assert not result.stderr, result.stderr
assert list(map(json.loads, result.stdout.splitlines())) == [
    dict(type="action", action="check"), dict(type="action", action="fold"),
    dict(type="discard", card="As"),
]
print("isolated capped-lead transcript passed")

