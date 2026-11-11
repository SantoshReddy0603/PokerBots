# Pokerbots: implementation and model handoff plan

> Historical initial plan. Implementation and a locally validated release now exist. For the 4 November 2026 review and prioritized next changes, see [REVIEW_AND_IMPROVEMENT_PLAN.md](REVIEW_AND_IMPROVEMENT_PLAN.md); completed work is recorded in [PROGRESS.md](PROGRESS.md).

Prepared 4 November 2026 (IST). Deadline in supplied rules: **15 November 2026, 23:59 IST**. Status: planning only; no competition bot implemented or performance established.

## 1. Objective and starting point

Build the strongest reliable, rules-compliant Discard Hold'em bot feasible before the deadline, with first place as the target. No model, strategy, local win rate, or amount of reasoning guarantees first place against unknown opponents. Optimize the probability of winning through measured improvement, diverse opponents, and reliable execution.

The repository currently contains three official PDFs, a starter ZIP, and an empty `pokerbots_1/instructions.txt.txt`. The ZIP was inspected without unpacking. There are no existing project implementation instructions or tests in the visible workspace. Do not assume an implementation exists.

Read these primary local sources before coding:

| Source under `pokerbots_1/` | Contents |
|---|---|
| `5869f741-8421-4b25-b948-1ad66e1e1316.pdf` | Rulebook, especially sections 5-10 |
| `497da9d5-f0da-442b-b739-b5c06f15fe9b.pdf` | Protocol specification 1.0, full message fields |
| `8a894a3d-946f-40e9-b7ab-7c4e01eb0d4c.pdf` | Problem statement, game mechanics and examples |
| `26f11512-f33e-4b0c-99c2-33ba73464329.zip` | `Starter_Kit/engine.py`, `bot.py`, `README.md`, `example_bots/random_bot.py` |

Rulebook prevails generally; Problem Statement prevails for variant rules. Limits marked provisional must be checked against organizer announcements before release. Current announcements, registration status, hardware speed, and AI-assistance policy have not been verified. The rules require team-owned work and permit published algorithms and organizer code; they do not explicitly settle AI assistance. Have the team confirm any applicable organizer guidance before submission. Do not block independent local implementation on unrelated administrative details.

## 2. Non-negotiable requirements

- Python **3.11**, standard library plus optional numpy/scipy only. No runtime package installation.
- One `bot.py`, or ZIP with `bot.py` at its top level; maximum 5 MB. Prefer one self-contained generated file with embedded tables.
- No bot filesystem reads/writes, network, subprocesses, or cross-match persistence. Development tools may use local files/processes; submission code must not.
- 1 vCPU, 1 GB RAM; startup 5 s. Stage 1: 400 hands, 60 s cumulative response bank, 180 s wall clock. Stage 2: 1000 hands, 150 s bank, 450 s wall clock. Single reply limit 5 s. Read actual limits from `init` and `time_left_ms`.
- JSON lines over stdin/stdout, flush each response. Exactly one response to action/discard requests and no replies to informational messages. Diagnostics only to bounded stderr. Ignore unknown message types/fields.
- Three hole cards; flop betting occurs **before** simultaneous discard. Both discards become public only afterward. Discard still happens after an all-in, unless the hand ended by folding.
- Stacks reset to 200 each hand, blinds 1/2. Button first preflop, second later. Best five of remaining two hole cards plus board, using zero, one, or two hole cards.
- Raise amounts are street totals, not increments. Trust `legal_actions`, `min_raise`, and `max_raise`. Four bets/raises per street, including the preflop big blind. Short all-in raises may have equal minimum and maximum.
- `action_request` does **not** contain hole cards: retain them from `new_hand` and `discard_result`. `discard_request` lacks history: retain history from action requests. Reset hand state each new hand and match state each process.
- Only use information legally available at the decision. Never let test logs, unrevealed opponent cards, future boards, seeds, or duplicate identity reach the policy.
- Starter engine pairs duplicate deals consecutively. Do not infer the next hand's board or opponent cards from that implementation detail. Rulebook 10.3 prohibits exploiting the evaluation system; report weaknesses to organizers through the team, without using them. No automatic external messages are authorized by this plan.

## 3. What to optimize

Stage 1 normally uses 6 Swiss rounds (7-8 for very large fields), top 32 qualify; smaller fields have alternate formats. Finals are a fresh round robin among 32 bots, 31 matches per bot, with scores reset. Match points are win=1, draw=0.5, loss=0. The secondary tie-break is sum of clipped net chips divided by total hands, caps 400/1000 for stages 1/2. Confirm full edge cases from Rulebook 7-8.

Primary development metric: held-out average match points against a broad opponent population, reported separately at both match lengths. Also track raw chips/hand, capped score, per-opponent results, variance, runtime, memory, corrections and forfeits. Do not select a bot solely by profit against the supplied random bot. Estimated first-place probability from simulated fields is a diagnostic, not a calibrated claim about unknown real entrants.

## 4. Proposed repository layout

Create these during implementation, adapting names if needed:

```
vendor/Starter_Kit/       # unchanged extracted organizer files
src/                     # protocol/state, evaluator, equity, discard, policy, model, budget
tools/                   # build_submission.py, benchmark.py, evaluate.py, train_tables.py
tests/                   # protocol fixtures, evaluator/property tests, integration tests
opponents/               # original diverse local opponents and frozen checkpoints
experiments/             # manifests and compact machine-readable results
dist/bot.py              # generated, self-contained submission
RULES.md                 # verified constraints, precedence, unresolved questions
PROGRESS.md              # current milestone, exact commands, results, next steps
```

Keep input files intact. Preserve an unchanged reference engine; any instrumented harness lives separately. Embed original offline-generated constants into the final file instead of loading data at runtime. Keep performance training and packaging outside bot startup. Record provenance of reused organizer code; never copy public poker bot repositories or competitors' code.

## 5. Ordered milestones and acceptance gates

### M0: reproducible environment and baseline (4 November)

1. Safely extract the starter ZIP, inspect any newly discovered instructions, inventory source hashes, and record the rules in `RULES.md`.
2. Provision/locate Python 3.11 and record its exact path/version. In the planning session `python` was absent from PATH; a bundled Python exists at `C:/Users/varun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, but its version has not been validated for competition use. Do not silently assume it is 3.11.
3. Run untouched starter against random bot at both full stage lengths using fixed seeds and clocks enabled. Save commands and results, including losses.
4. Build subprocess protocol fixtures and a benchmark report schema. Select and freeze separate training, validation, and final-test seed manifests before strategy tuning.

Gate: reproducible baseline, verified interpreter, no undocumented setup dependency. A baseline win is not required.

### M1: protocol/state safety and release pipeline (4-5 November)

Implement explicit match and hand state, legal action normalization, deterministic fallback (check if legal, otherwise fold), and a valid deterministic fallback discard. Correct state when `notice` reports a substituted discard/action. Recover safely from strategy exceptions while reporting bounded diagnostics; do not conceal failures in evaluation reports. Exit cleanly on match end/EOF.

Fixtures: unknown fields/types; no raise fields; min=max all-in; cap reached; limp then big-blind option; fold before flop/discard; all-in before flop with mandatory discard; ties; informational messages requiring no output; decreasing time bank; fresh process between matches. Verify raise integers are not booleans and are clamped to engine bounds.

Build a self-contained `dist/bot.py` early. Integration tests must exercise the generated artifact, not just modules. Gate: full matches at both stages without notices, invalid messages, crashes, or stalls; packaged startup works from a clean working directory without project files.

### M2: correct fast evaluation and bounded equity (5-6 November)

Use the supplied `rank5`/`best_hand` as a correctness oracle. Implement an original compact rank-count/bitmask evaluator if profiling justifies it; the naive 21-five-card-combination evaluator may be too slow inside simulations. Compare all hand categories, wheel, kickers, board-playing ties, and large randomized seven-card samples against the oracle. Suit renaming must preserve rankings. Record actual throughput.

Card sampling must remove all known cards, including our discarded card and the exposed opponent discard. Before discard, sample opponent three-card holdings and model their legal flop-based discard. After discard, use compatible retained pairs weighted by observed betting and discard evidence. Unknown cards are sampled without replacement. Equity includes half the ties.

Preflop rollout: sample flop, choose discards using only flop information, then sample turn/river. Never choose a discard with knowledge of the sampled future runout. Likewise do not let the modeled opponent see our private cards or unrevealed discard. Board fixation does not permit future information access.

Use sample caps and elapsed-time checks in small batches. Exact enumeration is optional where measured cost is affordable; do not assume full turn range enumeration fits. Cache only with complete state/range keys and bounded memory. Gate: known-state correctness, no duplicate cards or information leakage, measured latency and reproducible simulations.

### M3: strong discard policy (6-7 November)

Compare all three candidate retained pairs using common sampled opponent holdings and runouts to reduce comparison noise. Start with showdown-equity selection against several plausible discard policies. Keep action-value estimates clearly separate from raw equity: later betting and the information revealed by our discard also matter.

Include low-card-discard, made-hand-first, draw-aware, and equity-aware opponent discard models. Do not assume one is universally correct. Begin with an efficient flop-only heuristic for simulated opponent discards; upgrade only if measured gains justify cost. Add crafted cases where lowest-rank discard loses pairs, flush draws, straight draws, or kickers.

Gate: demonstrate improvements over rank-only and made-hand-only discards on held-out paired scenarios and full matches; include uncertainty and runtime cost. Ship the simpler policy if comparisons remain inconclusive.

### M4: coherent betting baseline (7-9 November)

Preflop features/tables must reflect three cards: pairs/trips, suitedness, connectivity, high-card quality, position, and previous actions. Ordinary two-card Hold'em charts are not a drop-in solution. Generate original tables offline if affordable and embed them with documented precision and size.

Postflop combine range equity, position, pot odds, stack-to-pot ratio, draw potential, betting history, exposed discards, and credible fold estimates. At a terminal call with no future betting, `EV(call) = equity * (pot + to_call) - to_call`, relative to folding. This is not a complete model for a flop call with future betting. Validate incremental contributions and pot accounting separately.

Use a small action set: check/fold/call, several pot-relative bet/raise sizes, and justified all-ins. Translate sizes into raise-to amounts and deduplicate after clamping. Flop value must anticipate the discard; do not evaluate a three-card holding as if all three survive to showdown. Add conservative value betting, selective semi-bluffs and blocker-aware river bluffs; frequencies are tuneable hypotheses, not assumed optimal constants.

Gate: candidate performs competitively across original tight-aggressive, loose-passive, calling-station, over-folding, aggressive/overbetting, shove-heavy, and equity-based opponents. Record weaknesses, not just aggregate wins.

### M5: robust adaptation and optional search (9-11 November)

Maintain within-match statistics with conservative priors: action rates conditional on opportunities, fold-to-size tendencies, aggression by street, showdown strength, and discard habits. Process each history event once; repeated complete histories must not multiply counts. Separate street/context buckets only when samples support them. Showdowns are selectively observed and do not directly represent all opponent hands.

Blend an unadapted policy with bounded exploitation according to evidence. Shrink sparse estimates toward priors, limit extreme reactions, and reset between matches. Infer retained ranges from the likelihood of the exposed discard under plausible policies, not the certainty that a discarded king means a stronger pair.

Only after M0-M4 work: experiment with restricted action lookahead, offline regret minimization/self-play, or a compact distilled policy. Published algorithms may be implemented originally. Validate on toy games and against independent opponents. Do not claim equilibrium or low exploitability from self-play wins. Do not start a full no-limit solver or large neural training project without a demonstrated deadline advantage.

Gate: adaptation/search wins ablations against the same base policy on unseen seeds and opponents without exhausting resources. Otherwise disable it in release.

### M6: tournament selection and hardening (11-13 November)

Evaluate complete matches with paired seeds and both bot assignments. Duplicate hands are correlated: use match-level or duplicate-block statistics, never treat individual hands as independent samples. Bootstrap paired match differences; report win/draw/loss counts, confidence intervals, and sample size. Sequential tuning on validation seeds is not final-test evidence.

Suggested screening: 20 full matches per opponent/style and stage, then allocate additional games where candidate differences are uncertain. Scale to compute budget and publish actual counts; no universal match count proves superiority. Use multiple parameter variants per style and frozen prior bots. Reserve a final untouched opponent/seed set for selection confirmation. Investigate poor matchups even when average results improve.

Run simulated Swiss/round-robin fields for ranking sensitivity. Score-dependent variance control is optional: compare it to the same bot without it on full matches. Do not blindly fold every hand while ahead or chase losses with arbitrary shoves; remaining blind losses and opponent behavior matter.

Gate: selected champion has a defensible held-out comparison against the prior champion, no severe unresolved matchup collapse, and a reproducible manifest. Retain the previous champion if evidence is inconclusive.

### M7: release freeze and submission (14-15 November)

Freeze strategy on 14 November; allow only demonstrated correctness or resource fixes afterward. Re-run full release validation on the exact built file. Target upload by 15 November 18:00 IST, leaving buffer before the official 23:59 deadline. User/team handles registration and upload unless explicitly authorizing those actions in a later task.

Confirm two team members, verified emails, current announcements and eligibility. Record SHA-256, size, runtime version, source provenance, build command, and final results. Independently reopen/rebuild and verify artifact bytes. Confirm the correct file was uploaded and the platform accepted it. Keep a tested fallback artifact ready; do not replace the champion with an untested last-minute change.

## 6. Runtime engineering targets

The bank averages 150 ms per hand at both stages, **not per decision**. Many decisions share that budget. Initial engineering targets (not official limits): use at most 70% of the total bank on representative full matches, aim for per-decision p99 below 100 ms and maximum below 1 s, startup below 2 s, peak memory below 500 MB. Adjust targets from actual reference-speed benchmarks while preserving a substantial reserve.

Budget from remaining hands, observed decisions per hand, reported time left, and a monotonic local timer. Reserve time for mandatory future discard/serialization and degrade progressively: fewer samples, cached/heuristic policy, then immediate legal fallback. Stress long raise-heavy matches and all-in discard paths; short easy matches are insufficient. Run clocks enabled. Use a clean Python 3.11 Linux environment with 1 CPU and 1 GB if available; local Windows timing is not proof of server timing. Bot code must not inspect platform files to enforce this.

## 7. Evidence and handoff contract

After each milestone update `PROGRESS.md` with: completed work; exact commands; interpreter; artifact/commit hashes; seed manifest; results and uncertainty; runtime/memory; failures; decisions and reasons; next concrete task. Record experiment configuration, opponent versions, PRNG seeds and budgets. Separate observed results from hypotheses. Never invent benchmark wins or mark an unrun gate complete.

The next model should implement one milestone at a time, run its acceptance checks, and preserve a runnable champion throughout. Do not rewrite unrelated working components. No sub-agents are required by this plan. Do not automatically create chats, send messages externally, upload, or spend money.

Suggested commands after extracting/building (replace `<python311>` with the verified executable):

```
<python311> vendor/Starter_Kit/engine.py dist/bot.py vendor/Starter_Kit/example_bots/random_bot.py --stage 1 --seed smoke-s1 --log-dir experiments/smoke-s1
<python311> vendor/Starter_Kit/engine.py dist/bot.py vendor/Starter_Kit/example_bots/random_bot.py --stage 2 --seed smoke-s2 --log-dir experiments/smoke-s2
```

These are proposed commands, not tests already executed. `--no-time-limits` is debugging-only. Use unique log directories to prevent overwriting evidence.

## 8. Model and effort recommendation for Plus

Recommendation: **GPT-6.1 Sol, High reasoning effort**, standard speed, for the main implementation. Use **Extra high** selectively for evaluator/range correctness, discard information boundaries, statistical review, and final audit. Use Medium for straightforward packaging, fixtures, and reporting once requirements are settled. This is a workload recommendation, not a measured comparison on this repository.

If GPT-6 Astra is offered in your model picker and allowance permits, use it at Extra high for a focused strategy/design review. Do not spend the entire Plus allowance asking a flagship model to generate untested strategies. The practical advantage comes from running local experiments and reviewing evidence. The development assistant is not the submitted bot; no LLM calls or paid API are needed during gameplay.

Official documentation checked 4 November 2026 lists GPT-6.1 Sol in Plus and describes it as suitable for complex work where time/cost matter. Limits depend on model/task and can change; account-specific access was not inspected. Confirm available effort labels and usage in your picker/dashboard. Do not assume API support alone proves product availability.

- Model guidance: https://developers.openai.com/api/docs/guides/model-selection
- Plus availability and limits: https://learn.chatgpt.com/docs/pricing

## 9. Copy-paste prompt for the implementing model

> Read IMPLEMENTATION_PLAN.md and PROGRESS.md if present, then inspect the original competition PDFs and starter ZIP. Implement the next incomplete milestone, starting with M0. Use Python 3.11, preserve the supplied engine as an oracle, and build a self-contained bot that obeys the runtime restrictions. Focus on robust match wins, correct simultaneous discard modeling, and measured resource limits. Never use duplicate-deal ordering, hidden cards, logs, or future boards in policy decisions. Run the milestone's checks and record exact evidence, failures, and next steps in PROGRESS.md. Keep the best tested bot available. Do not claim guaranteed first place or claim benchmarks that were not run. Follow the saved plan through implementation, evaluation, and local release preparation; ask only for genuinely blocking information. Do not submit or send external messages without authorization.
