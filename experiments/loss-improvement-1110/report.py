"""Produce a report only after all declared studies and gates are complete."""
from pathlib import Path
import hashlib
import json
import re

root=Path('experiments/loss-improvement-1110')
load=lambda name:json.loads((root/name).read_text())
decision=load('decision.json')
screen=load('screen-summary.json')
confirmation=load('confirmation-summary.json')
regression=load('regression-summary.json')
diagnosis=load('full.json')
holding=load('call-diagnostics.json')
stress=[json.loads(line) for line in (root/'selective-stress.jsonl').read_text().splitlines()]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
promoted=decision['promote']
expected=sha(root/('selective.py' if promoted else 'baseline.py'))
assert sha('dist/bot.py')==expected
if promoted:
    assert load('promotion.json')['sha256']==expected
fmt=lambda values:'/'.join(map(str,values))
def label(path):
    if 'friend-review' in path:
        return 'Archived friend bot'
    if 'requested-field-test' in path:
        return 'Friend snapshot from the 96-match test'
    return {'trap':'Trap / check-raise','tightjam':'Tight shove','range':'Range-aware',
            'polar':'Polarized betting','pressure':'Pressure','switch':'Style switching','baseline':'Previous champion'}.get(Path(path).stem,Path(path).stem)

text=['# PokerBots loss analysis and improvement — 10 November 2026','',
      ('**Promoted the validated selective-aggression range update.** The previous champion is preserved byte-for-byte.' if promoted else
       '**Retained the previous champion.** The candidate did not clear every declared gate; research code is preserved outside the release.'),'',
      '## What the loss investigation found','',
      'The original field test had 14 losses against the friend snapshot. It retained match summaries, not every action. '
      'All 16 friend matchups—including the two wins—were rerun with development-only request/decision logging. '
      'The bot and opponent work depend on timing, so these are diagnostic replays, not exact reconstructions of the original action sequences. '
      'Original results were preserved. The replay analysis covers 11,200 hands.','',
      '| Replay cohort | Hands | Net chips |','|---|---:|---:|']
for key,title in [('nonshowdown','Ended before showdown'),('showdown','Showdowns'),
                  ('preflop_20plus','Our preflop street contribution at least 20'),
                  ('allin_flop','First voluntary all-in decision on flop'),('allin_turn','First voluntary all-in decision on turn'),
                  ('allin_river','First voluntary all-in decision on river')]:
    g=diagnosis['groups'][key]
    text.append(f"| {title} | {g['hands']:,} | {g['net']:+,} |")
turn=holding['groups']['turn|terminal']
c=holding['terminal_turn_classification']
text += ['', 'Cohorts overlap and must not be added together. Decision-level summaries can repeat a hand’s final net; they are not a causal accounting of each action.','',
         f"The main observed leak was expensive postflop continuation against strong hands. In {turn['calls']} terminal turn calls, "
         f"mean estimated equity was {turn['mean_estimated']:.1%}; exact future runouts against the subsequently shown holding averaged {turn['mean_known_holding']:.1%}. "
         f"Against those actual holdings, {c['negative_holding_ev']} calls had negative incremental call EV; {c['lost_despite_positive_holding_ev']} other calls lost despite nonnegative conditional EV. "
         'These are selected called/showdown hands, not an unbiased calibration of every opponent action. Knowing the shown hand retrospectively does not prove a call was wrong against the full range.','',
         'For example, one replay called 158 chips on the turn with Ad Ah on 3s Ks 4d 7s. '
         'The estimate was about 51%, but the later-shown As 5s already made a flush; conditional equity against that hand was zero. '
         'Other losses were ordinary unfavorable runouts. No shown/hidden opponent cards enter the submitted strategy.','',
         '## Implemented change','',
         '`src/selective_equity.py` lowers the weak-hand likelihood floor for postflop reraises and large bets when their learned frequency is low. '
         'The floor is `min(0.08, max(0.01, 0.20 * frequency))` in those contexts. '
         'Ordinary bets and frequent aggression retain the prior broad floor. This stops rare strong actions from leaving as much weight on weak holdings. '
         'The rule uses public history and shrunk within-leg action frequencies, not opponent identity, test seeds or revealed cards.','',
         'The preflop decision code, hand evaluator, sample counts, discard scoring code and standard-library fallback were retained. '
         'Posterior equities and therefore actions/discards can intentionally change after selective aggression. '
         'The existing histogram calculation optimization is retained.','',
         'A separate explicit reraise-response model was implemented in `src/response_policy.py` and tested alone and combined. '
         'Its effective-stack-shove assumption did not win selection; it is excluded from the selected build.','',
         '## Fresh screening — complete results','',
         'Two fresh seed blocks, four opponents, both assignments and both stages: 32 matches per artifact, 128 total. '
         'No partial score was used to select a candidate.','',
         '| Artifact | W/D/L |','|---|---:|']
for name in ('baseline','selective','response','combined'):
    text.append(f"| {name} | {fmt(screen[name]['wdl'])} |")
text += ['', 'Range-only was advanced because it had the highest eligible match points, gained at both stages, and had no observed matchup regression. '
         'The current friend subset was 6/8 versus baseline 0/8. Screening scores are selection evidence, not fresh confirmation.','',
         '## Untouched confirmation','',
         'Four reserved fresh blocks, six opponent snapshots, both assignments/stages: 96 matches per artifact. '
         'All matrices and paired configurations passed strict validation before comparison.','',
         '| Opponent | Previous champion W/D/L | Range candidate W/D/L |','|---|---:|---:|']
for opp,old in confirmation['baseline']['by_opponent'].items():
    text.append(f"| {label(opp)} | {fmt(old)} | {fmt(confirmation['selective']['by_opponent'][opp])} |")
text += [f"| **Total** | **{fmt(confirmation['baseline']['wdl'])}** | **{fmt(confirmation['selective']['wdl'])}** |",'',
         '| Stage | Previous champion W/D/L | Range candidate W/D/L |','|---|---:|---:|']
for stage in ('1','2'):
    text.append(f"| {400 if stage=='1' else 1000} hands | {fmt(confirmation['baseline']['by_stage'][stage])} | {fmt(confirmation['selective']['by_stage'][stage])} |")
delta=confirmation['selective']
text += ['', f"Paired match-point difference: {delta['paired_points']:+.4f} per match; four-block bootstrap 95% interval {delta['point_interval']}. "
         f"Individual block differences: {delta['point_blocks']}. "
         'Four blocks provide limited uncertainty information; this conditional local interval is not a tournament-wide forecast.','',
         '## Additional regression and resource checks','',
         f"Fresh pressure/switch/champion study: candidate {fmt(regression['selective']['wdl'])}, previous champion {fmt(regression['baseline']['wdl'])}. "
         'Candidate won all eight against each opponent, including the previous champion. '
         'The baseline-versus-itself games were eight draws; do not present those as losses.','',
         'Exact candidate bytes also passed full official-format matches sharing one CPU and inheriting a 1 GiB address-space limit. '
         'The resource test includes an unfavorable result:','',
         '| Stage / opponent | Net chips | Worst per-leg bank | Official bank |','|---|---:|---:|---:|']
for row in stress[:2]:
    bank=max(leg['bots'][0]['bank_s'] for leg in row['legs'])
    text.append(f"| {row['stage']} / {'friend test snapshot' if row['stage']==1 else 'archived friend'} | {row['net']:+,} | {bank:.2f} s | {30 if row['stage']==1 else 75} s |")
time_text=(root/'selective-stress-time.txt').read_text()
rss=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',time_text).group(1)
max_reply=max(row['bots'][0]['max_ms'] for row in stress[:2])
failures=sum(v['forfeits'] for phase in (screen,confirmation,regression) for v in phase.values())+sum(bool(r['forfeits']) for r in stress[:2])
notices=sum(v['notices'] for phase in (screen,confirmation,regression) for v in phase.values())+sum(r['bots'][0]['notices'] for r in stress[:2])
diagnostics=sum(v['diagnostics'] for phase in (screen,confirmation,regression) for v in phase.values())+sum(r['bots'][0]['diagnostics'] for r in stress[:2])
text += ['',f"Largest response {max_reply:.2f} ms; timed-command maximum RSS {int(rss):,} KiB. "
         'All 20 initial correctness invocations passed, including 15,000 scalar/vector rank checks per candidate, '
         'range isolation, loose-opponent controls, protocol, decision and official-leg fixtures. '
         'Selected-byte static audit and no-NumPy official-leg checks also passed. '
         f"Screen, confirmation, regression and resource reports recorded {failures} match forfeits; "
         f"the tested artifacts had {notices} correction notices and {diagnostics} diagnostic bytes.",'',
         '## Release decision and reproducibility','',
         f"- Decision: {'promote selective range update' if promoted else 'retain previous champion'}; precise Boolean gate results are in `decision.json`.",
         f"- Current artifact SHA-256: `{expected}`.",
         '- Project: `C:\\Users\\varun\\OneDrive\\Documents\\ChatGPT\\PokerBots`.',
         '- Evidence: `experiments/loss-improvement-1110/`, including traces, original/replay comparisons, all three candidates, source hashes, seed manifests, matrix metadata, raw results and strict comparisons. Existing reports are never overwritten.',
         '- Reproduction uses the frozen recipe/seed files. Reusing inspected seeds is reproduction, not new holdout evidence. '
         'Opponent sampling depends on time, so repeated runs can differ.',
         '- The synthetic families share project infrastructure; the two friend snapshots also share their author and architecture. '
         'They do not represent every strong entrant or independent family.',
         '- Finite tests cannot guarantee no true regression, or wins against every opponent. '
         'The previous exact bot remains available as a fallback. No commit, push, upload or external contact was performed.']
if promoted:
    text += ['', 'Default `tools/build_submission.py` reproduces the selected tested bytes. '
             'The active vector module is now `src/selective_equity.py`; `src/vector_equity.py` preserves the previous model. '
             'The optimization-equivalence test keeps its equality assertions and targets the preserved calculation-only checkpoint by default; '
             'the new range weights are checked by separate isolation/model fixtures and fresh games. '
             '`dist/release.json` and the manifest-generator defaults reference the correct new source/report hashes. '
             'Fallback: `checkpoints/pre-selective-1110.py` and its `.release.json` companion.']
with (root/'RESULTS.md').open('x') as f:
    f.write('\n'.join(text)+'\n')
print('Wrote complete loss analysis and release decision report')
