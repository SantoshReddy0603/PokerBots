"""Write a manifest after the exact artifact passes local validation."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", default="dist/bot.py")
    p.add_argument("--selected", default="checkpoints/daily-1110-histogram.py")
    p.add_argument("--fallback", default="checkpoints/pre-daily-1110.py")
    p.add_argument("--fallback-report", default="experiments/rules-update-1110/retained-stress.jsonl")
    p.add_argument("--report", default="experiments/daily-1110/histogram-stress.jsonl")
    p.add_argument("--final-report", default="experiments/daily-1110/exact-friend.jsonl")
    p.add_argument("--sources", nargs="+", default=["src/learning_protocol.py", "src/poker.py",
                   "src/preflop_key.py", "src/preflop_table.py", "src/friend_ranges.py",
                   "src/learning.py", "src/vector_equity.py", "src/learning_policy.py"])
    p.add_argument("--build", default="python3.11 tools/build_submission.py")
    p.add_argument("--output", default="dist/release.json")
    p.add_argument("--validation-note", default="Direct rank histograms preserve fixed-draw outputs: "
                   "16,536 rank rows and 60 complete posterior cases exactly match the prior release. "
                   "Local single-CPU warm median equity time improved 4.8-6.8%. "
                   "Both full current-format stages passed one-CPU/1-GiB validation. "
                   "Exact release versus fetched teammate: 2/4 wins on one fresh seed block. "
                   "Calculation efficiency is improved; no stronger win-rate claim follows. "
                   "See experiments/daily-1110/RESULTS.md.")
    p.add_argument("--numpy-note", default="optional; NumPy 2.2.6 full Linux checks and no-site-packages "
                   "(-S) official-leg protocol fixtures passed")
    args = p.parse_args()
    artifact = Path(args.artifact)
    data = artifact.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    records = [json.loads(line) for line in Path(args.report)
               .read_text(encoding="utf-8-sig").splitlines()]
    assert len(records) == 3 and records[-1]["sha256"] == digest
    for stage, row in enumerate(records[:2], 1):
        assert row["stage"] == stage and row["played"] == {1: 400, 2: 1000}[stage]
        assert row["bots"][0]["sha256"] == digest and not row["forfeits"]
        assert not row["bots"][0]["notices"] and not row["bots"][0]["diagnostics"]
        if "legs" in row:
            from matrix import validate_legs
            validate_legs(row, {1: 400, 2: 1000}[stage], [b["sha256"] for b in row["bots"]])
            assert all(not leg["bots"][0]["notices"] and not leg["bots"][0]["diagnostics"]
                       for leg in row["legs"])
    assert data == Path(args.selected).read_bytes()
    fallback = Path(args.fallback)
    manifest = dict(artifact=artifact.as_posix(), bytes=len(data), sha256=digest,
                    python=records[-1]["python"], build=args.build,
                    sources=args.sources,
                    provenance="Independently implemented leg-local frequency model, base-15 NumPy "
                               "histogram evaluator and continuing-range policy built on this project's "
                               "original scalar evaluator and equity table. Teammate code used only as "
                               "an external opponent; unchanged organizer engine used as test oracle.",
                    numpy="optional; validated with 2.2.6 and with standard-library fallback",
                    validation_note="Calculation caching preserves fixed-draw outputs. New strategic "
                                    "experiments were retained outside the release after inconclusive "
                                    "held-out comparisons; see LOSS_REVIEW.md.",
                    source_sha256={source: hashlib.sha256(Path(source).read_bytes()).hexdigest()
                                   for source in args.sources},
                    final_report=args.final_report,
                    release_report=args.report,
                    fallback=dict(path=fallback.as_posix(),
                                  sha256=hashlib.sha256(fallback.read_bytes()).hexdigest(),
                                  report=args.fallback_report),
                    status="locally validated")
    if "legs" in records[0]:
        manifest["engine_format"] = "two-leg-2026-11-10"
        manifest["organizer_engine_sha256"] = hashlib.sha256(
            Path("vendor/Starter_Kit_2026_11_10/engine.py").read_bytes()).hexdigest()
    if args.validation_note:
        manifest["validation_note"] = args.validation_note
    if args.numpy_note:
        manifest["numpy"] = args.numpy_note
    Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline='\n')

if __name__ == "__main__":
    main()
