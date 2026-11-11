# Competition review and improvement plan

Reviewed 4 November 2026, IST. Scope: the complete project folder, supplied rules and starter kit, current source, frozen bots, test tools, and recorded experiments. This is a review and implementation plan; the submission strategy has not been changed.

## Assessment

The project has a credible engineering foundation: a compact self-contained bot, a fast checked hand evaluator, legal-action normalization, bounded simulations, reproducible builds, and recorded Linux release validation. Keep these components and the current champion.

The main obstacle to winning is strategic strength and the quality of evidence used to select improvements. The current policy is a small heuristic strategy with approximate opponent ranges. The recorded 40/40 final wins are against five configurations of one opponent generator, using two deal seeds. That establishes success in this local pool, not performance against strong independent entrants.

Recommended order: **repair decision errors and strengthen evaluation; improve preflop and later-street ranges; improve action selection; then consider adaptation or a small solver.** Preserve the existing release as a fallback throughout.

## What was checked

| Area | Review result |
|---|---|
| `pokerbots_1/`, `RULES.md`, `vendor/` | Read the three supplied PDFs and reference code. All recorded input hashes match; all four files in the starter ZIP match their extracted copies. The instructions text file is empty. |
| `src/` | Reviewed all three modules, including information flow, sampling, discard, preflop scores, betting thresholds, and time allocation. |
| `dist/`, `checkpoints/` | Current source reconstructs the release bytes exactly. The chosen release equals the betting checkpoint; the adaptive checkpoint contains an unsuccessful experimental extension. |
| `opponents/`, `tools/` | Reviewed generation, evaluation, paired comparison, field simulation, discard experiment, and release scripts. The generated opponents share protocol, evaluator, features, and most decision logic. |
| `tests/` | Reran all three existing test scripts under WSL CPython 3.11.9. All passed, including 24,000 oracle and suit-invariance cases. Tests cover mechanics more thoroughly than decision quality. |
| `experiments/` | Parsed all JSONL reports, checked available bot hashes, inspected summary/clock reports and seed usage. Historical reports have no recorded forfeits. Old full-match results were inspected, not rerun during this review. |
| Planning and repository | Initial plan still describes an unimplemented project despite completed milestones. No `AGENTS.md` was found in the project. Working tree was clean before this review. |

Current champion: `dist/bot.py`, 11,875 bytes, SHA-256 `404af500d979b827d40bd34ff2aecb3c2545d203dd9c94ddc0be53a685c9e171`.

Historical constrained Linux validation reports 10.386 / 29.426 seconds of bank usage for 400 / 1,000 hands. This suggests room for targeted computation, but only two release matchups were tested under those constraints. It does not justify spending that spare budget on every decision.

## Prioritized findings and changes

### P0: Make evaluation capable of rejecting a weak strategy

**Evidence:** `tools/build_opponents.py:50` generates both the development and final opponents from the same template. `experiments/m6-betting.jsonl` contains 40 wins, but only `sealed-0` and `sealed-1`. Both finalists have identical match points and fully saturated capped scores against this pool. The seven-player field resamples the same outcomes, so its 100% first-place result adds no evidence about unknown entrants.

**Changes:**

- Keep existing styles as regression opponents. Add original, independently designed decision policies: a range-aware value opponent, a polarized river bettor, a small-bet pressure opponent, a trap/check-raise opponent, an always-shove diagnostic, and a parameter-search adversary trained against frozen champions. Include current and prior champions in the league.
- Sharing a verified evaluator and protocol is reasonable; varying only thresholds in one betting template is insufficient. Do not copy other teams or public bot repositories.
- Separate deal seeds, opponent policy seeds, and opponent families. Treat the inspected final results as development evidence from now on. Create a new confirmation manifest before tuning; do not repeatedly select on it.
- Screen each candidate against eight representative opponents with four independent deal seeds, both bot assignments, and both match lengths: 128 matches per candidate. For finalists, target 20 fresh seeds on the same dimensions: 640 matches per candidate. These are workload targets, not statistical guarantees; narrow uncertainty and matchup weaknesses determine whether more games are useful.
- Evaluate paired differences against the champion using match points first, capped chips second, and raw chips as a diagnostic. Report each opponent separately and bootstrap whole seed blocks, keeping assignments and repeated deals together. Also report sensitivity to opponent-family weighting.
- Predefine promotion criteria: zero new failures, resource limits met, improved paired match-point evidence on the strong pool, and no severe unexplained regression. If evidence is inconclusive, retain the champion or gather more independent results. Pure correctness fixes still need regression matches.

**Harness repairs:** `tools/evaluate.py:20` silently truncates requested counts to available seeds; `--count 20` currently supplies at most four. Reject insufficient seeds and empty splits. `tools/compare.py:8` silently overwrites duplicate keys, and line 14 silently drops unmatched records. Validate unique complete match matrices, candidate/opponent hashes, configuration identity, and sample counts before comparisons. Record interpreter, platform, concurrency, revision, and policy RNG configuration with every experiment. Use the same clock at both ends of wall-time measurement in `tools/benchmark.py`.

**Acceptance:** mismatched or incomplete reports fail loudly; every reported comparison has the intended number of independent seed blocks; stronger opponents can distinguish candidates whose scores saturate against the old pool. Keep `tools/field.py` explicitly exploratory: its five-round toy Swiss and shared treatment of ties are not the complete official format/replay rules.

### P0: Repair terminal call decisions

**Evidence:** `src/policy.py:75-79` imposes a roughly 31-44% equity floor even for cheap river calls. A controlled probe supplying 25% equity, a pot of 100, and a call of 10 returns `fold`. Calling has incremental expected value `0.25 * (100 + 10) - 10 = +17.5` chips if that equity is correct. The applied threshold is 32.3%, although pot odds require only 9.09%.

This probe isolates the decision rule; it does not claim that a particular real holding has exactly 25% equity. Conservative estimation can be justified, but an unrelated fixed floor can discard large positive-value calls.

**Changes:** for terminal calls, compare range equity with `call / (pot + call)`, with a separately measured uncertainty allowance if needed. Distinguish a terminal call from an early-street call that leaves future betting. Cover all-ins and river calls. Evaluate raises separately against the opponent's continuing range.

**Acceptance:** deterministic decision fixtures cover cheap calls, pot-sized calls, overbets, guaranteed ties, zero equity, all-in calls, and uncertainty near break-even. Increasing the pot without changing call cost/equity must not make a terminal call less attractive. Verify full-match behavior against both bluff-heavy and value-heavy opponents.

### P0: Correct preflop strength calibration

**Evidence:** `src/policy.py:30-35` assigns three deuces a score of 0.71. It calls 198 more into a pot of 202 against an all-in, which requires 49.5% equity. A review probe with 20,000 preflop rollouts estimated **34.145%** against the existing random-holding/discard mixture. This is model-conditioned evidence, not exact equity against a real shoving range. Discards were selected from flop information only. Three equal hole ranks must become a retained pair, and the discarded matching card removes an out.

For comparison, the same probe estimated 80.168% for `As Ah Kd` and 62.915% for `As Kh Qd`; their heuristic scores are 0.773 and 0.615. The score is not a calibrated equity probability. Whether AKQ should call a particular shove depends on the shover's range.

**Changes:** generate original offline three-card equity/features tables, with suit-isomorphic compression if helpful. There are only 22,100 unordered three-card holdings before compression. Model legal flop-based discards, dead matching cards, suitedness, connectivity, position, and action-conditioned opposing ranges. Start with reliable all-in call decisions, then tune opens, calls, and reraises. Embed tables in the submission; do not load files at runtime.

**Acceptance:** targeted low-trip and pair cases pass; table estimates agree with independent high-sample checks within documented sampling error; rare categories receive explicit coverage. Show improvement against wide and tight shove ranges and normal betting styles without excessive preflop folding.

### P1: Use betting history and exposed discards to build plausible ranges

**Evidence:** `src/policy.py:20` compresses all raises into one scalar, ignoring sizes and checks/calls; its `street` argument is unused. `src/poker.py:115` weights hands using flop strength even after turn and river raises. A hand that improves on the river is therefore not explicitly represented as more likely to make a river value bet. Post-discard likelihood is just 1.0 versus 0.29 based on one heuristic discard policy.

**Changes:** represent weighted opponent holdings/particles and update their likelihood for each observed action, using the board available at that action, bet-to amount, pot, position, and stack context. At discard, transform three-card holdings to compatible retained pairs using a mixture of legal discard policies. Keep uncertainty and a nonzero likelihood floor for unexpected actions. Track effective sample size and resample as needed.

Replay complete histories without counting events twice. The discard request has no history: retain our applied action and infer only what public stacks/pot and completed betting establish. Do not assume access to unseen final actions or unrevealed cards. Never condition a past discard on later board cards.

**Acceptance:** information-flow tests prevent future-card use; synthetic value-only versus bluff-heavy opponents cause sensible and distinct range updates; later-street improvements affect weights; results beat the old scalar model in an isolated ablation.

### P1: Spend computation where decisions are close

**Evidence:** betting uses at most 144 samples, discard 128; time limits can reduce those counts. At 144 independent equally weighted binary samples near 50%, the approximate 95% sampling half-width is eight percentage points. Weighted sampling can be noisier. `max(values)` on the flop also introduces selection optimism among noisy alternatives. These effects can move decisions across fixed thresholds.

**Changes:** expose sample counts, effective sample size, and uncertainty in development diagnostics. Stop early when the decision is clear and allocate more samples near call, raise, or discard boundaries. Reuse common random samples for competing actions. Investigate exact river evaluation: with two retained cards, five board cards, and two known discards, there are 903 compatible opponent pairs before range filtering. Benchmark its actual cost before enabling it. Exact enumeration removes sampling error, not range-model error.

Separate the simulation RNG from the action-mixing RNG, so changing sample counts does not shift all subsequent bluff draws. For strategy comparisons, support deterministic sample budgets; separately test the production time-adaptive path on constrained hardware.

**Acceptance:** decisions approach high-budget references on close-call/discard fixtures; exact river results match enumerated references; full-match bank stays below the existing engineering reserve (42 / 105 seconds), including long raise-heavy games. Retain progressive low-time fallbacks.

### P1: Choose bets by expected value and continuing ranges

**Evidence:** `src/policy.py:82-95` mostly maps equity to fixed thresholds and sizes. Bluffing is confined to the button, low equity, and a fixed random frequency. Value bets use equity against the sampled range without explicitly estimating which hands call or raise. More raw equity does not automatically make a larger bet profitable.

**Changes:** compare a small legal action set: check/call, small bet, medium bet, large bet, and justified shove. Include fold probability, equity against callers, raise risk, position, and remaining stacks. Select semi-bluffs using draw quality and river bluffs using blockers and opposing range composition. Keep credible strong hands in checking ranges. Treat any simplified action-value model as a hypothesis to validate.

**Acceptance:** decision fixtures cover value against callers, thin value, failed bluffs against stations, overfolders, and polarized raises. Promote only if an ablation improves the stronger league. Avoid adding many unmeasured constants at once.

### P1: Protect mathematically secured match results

**Evidence:** `src/protocol.py:37` clears hand state without accumulating `hand_result.net`. The policy therefore cannot respond to the actual match-point objective.

**Changes:** track cumulative reported net separately from hand state. At a hand boundary with lead `L` and `R` hands left, a policy that never voluntarily contributes more chips can lose at most `2R` in blinds under the supplied fixed 1/2 rules. Therefore `L > 2R` guarantees a positive finish, provided the bot remains valid and responsive. Checking when free, folding when facing a bet, and answering mandatory discards implements this bound. An exact alternating-blind sum can tighten it.

For a conservative default, preserve the maximum tie-break as well: lock only when `L - 2R >= C`, with the applicable stage cap `C`. Test a win-only lock separately because it may sacrifice capped score. Verify current limits and hand count before enabling this feature. Use reported scores only, with no inference from duplicate identities.

**Acceptance:** mathematical boundary tests, accounting tests across every hand ending, and full matches show preservation of the promised points/capped score with zero protocol failures. Do not generalize this into arbitrary shoving while behind.

### P2: Reintroduce adaptation selectively

**Evidence:** the adaptive checkpoint lost all four recorded head-to-head matches against fixed betting, with only one validation seed. It also earned fewer raw chips against the shared final pool. That supports keeping adaptation disabled in the current release; it does not prove that adaptation can never help.

**Changes:** first improve the base range model. Then test one learned quantity at a time: fold response by bet size, aggression by street/opportunity, or discard-model likelihood. Use shrinkage, minimum evidence, and bounded adjustments. Treat shown hands as selected observations. Maintain a fixed-policy fallback.

**Acceptance:** each feature improves fresh-seed comparisons versus the same nonadaptive policy, including opponents that change style within a match. Remove features that do not justify their complexity/runtime.

### P2: Small solver experiment only after the preceding work

A limited river or reduced-action self-play experiment may be worthwhile if the base strategy and evaluation infrastructure are already strong. Implement published algorithms originally and validate on a small game with a known solution first. Budget at most one exploratory day before deciding whether to continue.

Do not mistake solving sampled fully revealed deals for solving an imperfect-information game. Safe subgame solving depends on the surrounding strategy; see Brown and Sandholm, [Safe and Nested Subgame Solving for Imperfect-Information Games](https://papers.nips.cc/paper_files/paper/2017/hash/7fe1f8abaad094e0b5cb1b01d712f708-Abstract.html). This is a research reference, not a claim that a solver is necessary or feasible before this deadline.

## Execution schedule and promotion gates

Dates use IST. The supplied submission deadline is **15 November 2026, 23:59 IST**.

| Dates | Deliverable | Gate |
|---|---|---|
| 4-5 November | Preserve champion; repair evaluation/report checks; add decision fixtures and independent adversaries | Reports reject missing data; current bot's strategic failures are reproducible |
| 5-6 November | Terminal call fix, preflop calibration, match-score accounting and conservative score lock | Targeted checks plus screening matches pass |
| 7-9 November | Action-conditioned ranges, better discard likelihoods, selective computation, action-value betting | One-feature ablations beat champion on stronger development opponents |
| 10-11 November | Strong-opponent league; limited adaptation or solver only if justified | Paired improvements survive new seeds and opponent families |
| 12-13 November | Untouched confirmation set; constrained Linux stress; independent clean rebuild | Champion selected using points, capped score, matchup robustness, and runtime |
| 14 November | Freeze strategy; exact-byte release checks, manifest, tested fallback | All checks reference the exact submission artifact |
| 15 November | Target upload by 18:00 IST and verify acceptance | Buffer before 23:59 deadline; no untested last-minute replacement |

Evaluation runtime should be measured with a pilot before scheduling the full matrix. Use concurrency for throughput within available CPU capacity, but benchmark production timing separately on one CPU. Lower sample counts caused by contention can otherwise change the strategy being evaluated.

## Repository changes to make during implementation

- Keep `vendor/` and originals unchanged; retain the current champion under a stable versioned name.
- Add focused modules such as `src/ranges.py`, `src/preflop_tables.py`, and `src/match_score.py` only as features warrant them; extend the single-file build accordingly.
- Make candidate builds produce separate artifacts instead of overwriting the only tested release. Record source hashes and table provenance.
- Add a top-level README with exact Windows and WSL Python commands, build/test/evaluation instructions, current champion, and promotion rules. Python is not currently on the PowerShell PATH.
- Put experiment configurations and expanded seed manifests under version control. Keep compact results and representative failure hands; avoid requiring all large logs in Git as experiments grow.
- Extend tests around strategy decisions, history updates, dead-card exclusion, weighted ranges, exact river equity, low-budget degradation, and match-score locks. Keep the existing evaluator/protocol tests.
- Generalize `tools/release_manifest.py`, which currently requires equality with `checkpoints/betting.py`, so a newly selected champion can be validated without misleading provenance.
- Keep `PROGRESS.md` factual: distinguish mechanical completion, experiment results, statistical uncertainty, and unverified tournament readiness.

## Event information and unresolved external facts

The supplied PDFs remain the local authority for the rules reviewed here. Their limits are marked provisional. A public search now finds a matching [Unstop event](https://unstop.com/hackathons/pokerbots-synergy-26-international-institute-of-information-technology-iiit-bangalore-1762863), but the retrieved page exposed no readable details. A [secondary HackLoop listing](https://hackloop.tech/hackathons/pokerbots) names IIIT Bangalore and lists registration closing on 12 November; verify that date and any amendments in the official event/account communications. Do not rely on the aggregator's relative countdown or treat it as confirmation of current rules.

Before release, confirm registration for both team members, latest resource limits, and organizer guidance on AI assistance. No organizer has been contacted and nothing has been uploaded during this review.

Local sources: Rulebook `pokerbots_1/5869f741-8421-4b25-b948-1ad66e1e1316.pdf` (especially sections 5-10); Protocol `pokerbots_1/497da9d5-f0da-442b-b739-b5c06f15fe9b.pdf`; Problem Statement `pokerbots_1/8a894a3d-946f-40e9-b7ab-7c4e01eb0d4c.pdf`; exact recorded results under `experiments/`.

## Verification performed in this review

From the repository root:

```powershell
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tests/protocol.py
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tests/selection.py
wsl -d Ubuntu -- /home/miyyapuram_saivarun/pokerbots-runtime/Python-3.11.9/python -B tests/evaluator.py
```

All passed. Evaluator throughput in this run was approximately 119,956 evaluations/second; this measures the evaluator only.

Additional read-only probes used Windows CPython 3.11.9 at `C:/Users/varun/AppData/Local/PokerBots/python311/python.exe`, loading the exact release with `runpy.run_path`. Preflop probes called `simulate(hole, (), (), 20000, float('inf'), Random(981))` independently for each holding, with no action evidence and the current default discard mixture. The river probe temporarily supplied `(0.25,)` from `simulate` in memory, then restored the original function. No production files were altered by these probes. Review results are recorded in `experiments/review-2026-11-04.json`.

Winning cannot be established from the present local results. The practical route is to fix demonstrated decision failures, build opponents that expose weaknesses, and promote changes on fresh full-match evidence.
