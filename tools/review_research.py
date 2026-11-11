"""Build separate measurable experiments, without changing the selected release."""
import json
from pathlib import Path
import hashlib

root = Path("experiments/review-fixes-1109")
config = str(root / "recipes/combined.py")
for name, learner, equity, policy in (
        ("sampling-exp", "src/review_learning.py", "src/research_sampling_equity.py", "src/research_sampling_policy.py"),
        ("ranges-exp", "src/research_range_learning.py", "src/research_range_equity.py", "src/research_range_policy.py")):
    sources = ["src/learning_protocol.py", "src/poker.py", "src/preflop_key.py", "src/preflop_table.py",
               "src/bet_features.py", config, "src/review_ranges.py", learner, equity, policy]
    body = "\n\n".join(Path(p).read_text(encoding="utf-8-sig").strip() for p in sources)
    body += '\n\nif __name__ == "__main__":\n    main()\n'
    target = Path(f"checkpoints/review-1109-{name}.py")
    compile(body, str(target), "exec")
    with target.open("xb") as file:
        file.write(body.encode())
    with (root / f"recipes/{name}.json").open("x") as file:
        json.dump(dict(output=str(target), sources={p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                                   for p in sources},
                       sha256=hashlib.sha256(body.encode()).hexdigest()), file, indent=2)
