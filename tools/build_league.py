"""Package the independent opponent policies and adversary trials."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--variant", default="development-v2", choices=["development-v2", "confirmation"])
args = p.parse_args()
paths = ["src/protocol.py", "src/poker.py", "opponents/league_policy.py"]
protocol, poker, policy = [Path(path).read_text(encoding="utf-8-sig").strip() for path in paths]
folder = Path("opponents/league") / args.variant
folder.mkdir(parents=True, exist_ok=True)
profiles = {
    "range": (), "polar": (), "pressure": (), "trap": (), "jam": (),
    "adversary": (.66, .30, .56, .07),
    "adversary_wide": (.59, .24, .92, .17),
    "adversary_tight": (.72, .39, .42, .03),
}
if args.variant == "confirmation":
    profiles.update(switch=(), tightjam=(.68, .35, .64, .04))
for i, (name, params) in enumerate(profiles.items()):
    seed = 4087 + i + (900 if args.variant == "confirmation" else 0)
    config = f"STYLE = {name.split('_')[0]!r}\nLEAGUE_SEED = {seed}\nADVERSARY = {params!r}"
    (folder / f"{name}.py").write_bytes(("\n\n".join([protocol, poker, config, policy]) +
        '\n\nif __name__ == "__main__":\n    main()\n').encode("utf-8"))





