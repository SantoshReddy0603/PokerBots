"""Write a manifest after the exact artifact passes local validation."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", default="dist/bot.py")
    p.add_argument("--selected", default="checkpoints/selective-1110.py")
    p.add_argument("--fallback", default="checkpoints/pre-selective-1110.py")
    p.add_argument("--fallback-report", default="experiments/loss-improvement-1110/confirmation-baseline.jsonl")
    p.add_argument("--report", default="experiments/loss-improvement-1110/selective-stress.jsonl")
    p.add_argument("--final-report", default="experiments/loss-improvement-1110/confirmation-selective.jsonl")
    p.add_argument("--sources", nargs="+", default=["src/learning_protocol.py", "src/poker.py",
                   "src/preflop_key.py", "src/preflop_table.py", "src/friend_ranges.py",
                   "src/learning.py", "src/selective_equity.py", "src/learning_policy.py"])
    p.add_argument("--build", default="python3.11 tools/build_submission.py")
    p.add_argument("--output", default="dist/release.json")
    p.add_argument("--validation-note", default='Selective postflop aggression ranges: weak-hand likelihood floor scales with learned large-bet/reraise frequency; ordinary/frequent aggression, preflop policy and evaluator are unchanged. Fresh four-block confirmation selected 86/96 wins versus prior 76/96; both assignments/stages, six declared opponent snapshots. Supplementary pressure/switch/champion test selected 24/24, including 8/8 head-to-head. Exact candidate passed one-CPU/1-GiB Linux current-format resource tests and correctness/protocol/audit checks. Finite local evidence does not guarantee no true regression. See experiments/loss-improvement-1110/RESULTS.md.')
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
