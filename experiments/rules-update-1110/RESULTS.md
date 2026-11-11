# Updated-rule review and validation: 10 November 2026

## Decision and artifact scope

The rule-update study retained the exact prior playing bot, SHA-256
`44b011220dce58a5a9ce0c8352c66a1f3c5054ef791c1669a1a3cfb2a68abe46`
(76,699 bytes). Its existing handling of the official 200/500-hand leg messages
already disables the old full-match lead protection. The explicit lifecycle
candidate was not promoted: it won 13/16 compared with the retained bot's 15/16.
The active rule-update changes are the updated organizer integration, leg-aware
measurement and validation, regression tests, rules documentation and release
metadata. No research strategy or opponent-range candidate was promoted here.

**Subsequent work:** a separate daily task later promoted a calculation-only
histogram optimization. The current submission is now `dist/bot.py`, SHA-256
`bb86e3e7dafd4019157bf9f24cee640e4c9dfbb276883dd92fee1585a03a1990`.
That work and its results belong to `experiments/daily-1110/`; this review did
not reverse it. The 15/16 and 13/16 figures below describe only the frozen
rule-update artifacts, not the later optimized artifact. The rule-update
manifest is preserved at `retained.release.json`; current release authority is
`dist/release.json`.

## Documents and confirmed changes

Reviewed all three PDFs, extracted full text, compared them with the earlier
documents, and visually inspected the relevant protocol and rulebook pages.
The three standalone PDFs match the corresponding PDFs inside the new archive.
`new_updates/instructions.txt.txt` is empty. The documents prevail over a
conflicting starter kit. Sources and hashes are recorded in `sources.json`.

- A match now consists of two fresh-process legs: 200 hands per leg in Stage 1,
  500 in Stage 2. Match totals remain 400/1,000 hands.
- Each process sees each deal once. Cards and seats are exchanged in the other
  leg; no information may be transferred between legs or duplicate deals
  identified by the playing bot.
- `init.total_hands`, `hand_id` and `time_left_ms` are scoped to a leg. Exit after
  `match_end`; the organizer launches a new process for the other leg.
- Banks are 30/75 seconds per leg, with 90/225-second per-leg wall limits.
  The five-second startup grace applies to every request sent before launch + 5s,
  as specified; the new measurement wrapper preserves that behavior.
- Match points and the 400/1,000-chip caps apply to the sum of both legs.
  A forfeit in either leg ends the match. Its denominator is scheduled hands,
  not the partial count actually played. A local leg lead cannot guarantee a
  whole-match win.
- Submission-local file reads are permitted; writes, networking, subprocesses
  and state transfer remain forbidden. No runtime IO was added to the bot.
- Missing replies time out. `legal_actions` remains authoritative even when
  `raises_left` is positive against an all-in opponent. These clarifications
  required tests rather than a new betting policy.
- Betting mechanics, stack sizes, simultaneous exposed discard and showdown
  evaluation did not change. Tournament/upload clarifications do not require
  playing-code changes.

## Implementation

Original `vendor/Starter_Kit` files remain untouched. Updated originals are in
`vendor/Starter_Kit_2026_11_10`; engine SHA-256 is
`f42c38fa30b44b55f3963e67f836134b49f5afbcf810e781f289d6458d826390`.

`tools/benchmark_legs.py` runs that updated engine and records both legs' process
metrics. `tools/evaluate.py` and `tools/validate_release.py` default to the new
format; `--engine-format legacy` remains available for historical reproduction.
`tools/benchmark.py` remains the old-format runner. Matrix checks verify both
leg counts, hashes, totals, resource metrics, forfeit location and scheduled
whole-match scoring. Release manifests validate the leg records too.

The candidate, `src/leg_protocol.py` / `checkpoints/rules-1110.py`, resets its
state on init and explicitly disables local-score locking, including custom
leg lengths. Its SHA-256 is
`4bee6c3e30a87610f60768f3b30af13d995fcf10ce66a63fe7c13848bc042cd3`.
Sixty fixed-draw official-format decisions matched the retained release.
Seven of the eight original playing source modules were byte-for-byte unchanged
in this experiment. The original selected protocol was restored after selection;
no candidate protocol was silently left in the default build.

## Correctness and resource results

- Thirteen Linux candidate/checking invocations passed: protocol, selection,
  evaluator, learning, decision fixtures, optimization default and timing-output
  modes, new lifecycle/matrix fixtures, existing review fixtures, and protocol
  without site packages. See `checks.jsonl` for exact commands, output and times.
- Eight Linux checks passed on the exact retained release, including official
  leg fixtures with and without site packages. Three additional Windows checks
  passed. See `retained-linux-checks.jsonl` and `retained-checks.jsonl`.
- New fixtures exercise fresh process launches, leg-local IDs, state reset in
  the candidate, all-in action/discard legality, exit behavior, and whole-match
  forfeits in either leg. Negative matrix fixtures reject corrupt leg records.
- Both artifacts passed complete 400- and 1,000-hand matches using Linux
  CPython 3.11.9, one CPU and a 1 GiB per-process address-space limit. The runner
  and both bots shared that CPU, which is stricter than separate CPUs per bot.
  Startup grace was kept as supplied. There were no corrections, diagnostics
  or forfeits.

| Artifact | Stage 1 maximum bank per leg / limit | Stage 2 maximum bank per leg / limit | Maximum charged reply | Timed-command maximum RSS |
|---|---:|---:|---:|---:|
| Retained 44b01122 | 7.459 / 30 s | 31.990 / 75 s | 65.118 ms | 40,492 KiB |
| Candidate 4bee6c3e | 8.359 / 30 s | 36.399 / 75 s | 84.004 ms | 40,404 KiB |

The constrained commands completed in 1:40.23 and 1:52.18 respectively. Both
artifacts scored +3,090 chips against pressure in Stage 1 and +1,641 against
trap in Stage 2 on the shared resource-test seeds. These timing differences
are measurements under different host load, not evidence of a policy change.
See `retained-stress.jsonl`, `stress.jsonl` and their `*-time.txt` files.

An additional Windows Stage 1 smoke match completed +2,429 against trap with
zero corrections/forfeits. Overall this rule-update work completed 36 Linux
full matches plus that one Windows smoke match. Static audits found no direct
seed/opponent lookup or exact shared top-level function bodies with the old ZIP
opponent; those syntactic checks are not a proof of authorship.

## Paired match results, including losses

Both matrices used one fresh seed block, both assignments, both stages, frozen
opponent hashes, jobs=2 per matrix, and simultaneous execution of the two
matrices. Each contained 16 full matches. Complete configuration and runtime
records are in `candidate.meta.json`, `baseline.meta.json` and the JSONL rows.
Strict matrix/configuration comparison passed.

| Opponent | Retained 44b01122 W/D/L | Candidate 4bee6c3e W/D/L |
|---|---:|---:|
| Trap/check-raise | 4/0/0 | 4/0/0 |
| Tight-reraise | 4/0/0 | 4/0/0 |
| Pressure | 4/0/0 | 4/0/0 |
| External comparison opponent from original friend's ZIP | 3/0/1 | 1/0/3 |
| **Total** | **15/0/1** | **13/0/3** |

Stage 1 was 8/8 versus 6/8; Stage 2 was 7/8 for each. Candidate Stage 1 losses
against the external opponent were -950 and -49 chips, and its Stage 2 loss was
-978. The retained release also lost one Stage 2 external-opponent match.
No result was excluded. Neither matrix had a forfeit, correction or diagnostic.

Candidate minus retained paired match points were -0.25 per match in Stage 1
and 0 in Stage 2; capped chips/hand differences were -0.2700 and -0.0117.
See `comparison.txt` for raw-chip differences and matchup details.

**Uncertainty:** there is only one independent seed block, so no meaningful
block-level confidence interval is reported. The generic evaluator's degenerate
one-block bootstrap output must not be interpreted as certainty. The external
opponent and some sampling work depend on elapsed time, so identical fixed-draw
decisions do not guarantee identical full-match outcomes under different load.
This study does not establish the cause of the observed gap. It provides no
support for replacing the release with this candidate. Old 56/64 results used a
different format and are not current-format evidence. Frozen opponents may also
have assumptions from the old format; these wins do not forecast the tournament.

## Reproduction and preserved work

`commands.json` records actual argv and frozen-source reproduction commands.
Run Linux commands from the repository root with the recorded CPython 3.11
interpreter under Ubuntu WSL. Use new result paths: report writers intentionally
refuse to overwrite existing results. Both original release bytes/manifest are
preserved at `checkpoints/pre-rules-1110.py` and its `.release.json` sidecar.
`frozen-sources/` preserves all eight source hashes for this study, including the
vector evaluator that was subsequently optimized by the daily task.

Validate historical evidence without rewriting it:

```powershell
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B experiments/rules-update-1110/summarize.py --validate-only
```

No Git push, submission upload or organizer contact was performed by this
rule-update task. Existing uncommitted/untracked work and the later daily
promotion were preserved. The one-time 04:45 IST continuation finishes this
report; it should not restart completed matches.

## Remaining weaknesses and next experiment

Learning now has only 200/500 hands of observations per process. Preflop action
classification, sparse-range calibration and continuation assumptions remain
the high-value strategic weaknesses already identified in previous reviews.
None was automatically promoted here. Next, test one isolated action-specific
opponent-model change under the new format, using more fresh seed blocks and
opponents with wide openings but tight reraises. Check calibration and per-leg
resources before a reserved confirmation study. Coordinate with the separate
daily task rather than duplicating its still-experimental river-order work.
