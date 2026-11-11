"""Summarize logged replays; hindsight is confined to this offline analysis."""
import json
from pathlib import Path


def main():
    summary = []
    for folder in sorted(Path("experiments/loss-review").glob("s*")):
        if not (folder / "result.json").exists():
            continue
        result = json.loads((folder / "result.json").read_text())
        hands, decisions = {}, {}
        net = 0
        for line in (folder / "trace.jsonl").read_text().splitlines():
            record = json.loads(line)
            if "input" in record:
                msg = record["input"]
                kind, hand = msg["type"], msg.get("hand_id")
                if kind == "new_hand":
                    hands[hand] = dict(before=net, seat=msg["seat"], cards=msg["hole_cards"])
                elif kind == "hand_result":
                    net += msg["net"]
                    hands[hand]["result"] = msg
            else:
                d = record["decision"]
                decisions.setdefault(d["hand"], []).append(d)
        full = [h for h in hands.values() if "result" in h]
        showdown = [h for h in full if h["result"]["result"] == "showdown"]
        large_losses = []
        for hand, h in hands.items():
            if "result" in h and h["result"]["net"] <= -100:
                r = h["result"]
                large_losses.append(dict(hand=hand, net=r["net"], hole=r["my_hole_cards"],
                                         opponent=r["opp_hole_cards"], board=r["board"],
                                         decisions=decisions.get(hand, [])))
        row = dict(replay=folder.name, original_net=result["original_net"],
                   replay_net=result["candidate_net"], hands=len(full),
                   showdown_net=sum(h["result"]["net"] for h in showdown),
                   nonshowdown_net=sum(h["result"]["net"] for h in full if h not in showdown),
                   stack_wins=sum(h["result"]["net"] == 200 for h in full),
                   stack_losses=sum(h["result"]["net"] == -200 for h in full),
                   large_losses=large_losses)
        summary.append(row)
        print(row["replay"], "original/replay", row["original_net"], row["replay_net"],
              "showdown/nonshowdown", row["showdown_net"], row["nonshowdown_net"],
              "200-chip wins/losses", row["stack_wins"], row["stack_losses"])
    Path("experiments/loss-review/summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
