"""Validate the complete declared matrix and summarize every result."""
from pathlib import Path
from statistics import mean
import hashlib
import json
import sys

sys.path.insert(0, str(Path('tools').resolve()))
from matrix import read

root = Path('experiments/requested-field-test-1110')
meta, indexed = read(str(root / 'results.jsonl'))
rows = list(indexed.values())
assert len(rows) == 96 and len(meta['seeds']) == 4 and len(meta['opponents']) == 6
plan = json.loads((root / 'plan.json').read_text())
assert meta['candidate_sha256'] == plan['frozen_sha256']['our-bot.py']
assert hashlib.sha256(Path('dist/bot.py').read_bytes()).hexdigest() == meta['candidate_sha256'], 'Current release changed during test'
labels = {'friend':'Friend (current GitHub version)', 'trap':'Trap / check-raise',
          'pressure':'Pressure', 'tightjam':'Tight shove', 'range':'Range-aware', 'polar':'Polarized betting'}
wdl = lambda group: [sum(r['candidate_points'] == p for r in group) for p in (1, .5, 0)]
def group_summary(group):
    return dict(wdl=wdl(group), matches=len(group), hands=sum(r['played'] for r in group),
                raw_net_chips=sum(r['candidate_net'] for r in group),
                raw_chips_per_hand=sum(r['candidate_net'] for r in group) / sum(r['played'] for r in group),
                by_stage={str(stage): dict(wdl=wdl([r for r in group if r['stage'] == stage]),
                                           raw_chips_per_hand=mean(r['candidate_net']/r['played'] for r in group if r['stage'] == stage))
                          for stage in (1,2)},
                by_seed={seed: wdl([r for r in group if r['seed'] == seed]) for seed in meta['seeds']})

summary = dict(candidate_sha256=meta['candidate_sha256'], total=group_summary(rows),
               opponents={Path(opp).stem: group_summary([r for r in rows if r['opponent'] == opp]) for opp in meta['opponents']},
               forfeits=[dict(opponent=r['opponent'], seed=r['seed'], stage=r['stage'], reverse=r['reverse'], failed=r['forfeits'])
                         for r in rows if r['forfeits']],
               all_bot_notices=sum(b['notices'] for r in rows for b in r['bots']),
               all_bot_diagnostics=sum(b['diagnostics'] for r in rows for b in r['bots']),
               our_notices=sum(r['bots'][int(r['reverse'])]['notices'] for r in rows),
               our_diagnostics=sum(r['bots'][int(r['reverse'])]['diagnostics'] for r in rows),
               by_stage_runtime={str(stage): dict(max_leg_bank_s=max(leg['bots'][int(r['reverse'])]['bank_s']
                                                                      for r in rows if r['stage']==stage for leg in r['legs']),
                                                  bank_limit_s={1:30,2:75}[stage],
                                                  max_reply_ms=max(r['bots'][int(r['reverse'])]['max_ms'] for r in rows if r['stage']==stage))
                                 for stage in (1,2)},
               match_wall_seconds_sum=sum(r['wall_s'] for r in rows), matrix_complete=True)
with (root / 'summary.json').open('x') as f:
    json.dump(summary, f, indent=2)

fmt = lambda values: '/'.join(map(str, values))
text = ['# Fresh PokerBots field test — 10 November 2026', '',
        f"**{fmt(summary['total']['wdl'])} wins/draws/losses across 96 full matches and {summary['total']['hands']:,} hands.**", '',
        'The exact current release was tested against the current teammate bot and five local synthetic opponent families. '
        'No playing-policy changes were made during this test.', '',
        '| Opponent | 400-hand W/D/L | 1,000-hand W/D/L | Overall W/D/L | Net chips / hand |',
        '|---|---:|---:|---:|---:|']
for name, group in summary['opponents'].items():
    text.append(f"| {labels[name]} | {fmt(group['by_stage']['1']['wdl'])} | {fmt(group['by_stage']['2']['wdl'])} | {fmt(group['wdl'])} | {group['raw_chips_per_hand']:+.3f} |")
friend = summary['opponents']['friend']
if friend['wdl'][2] > friend['wdl'][0]:
    text += ['', f"**The main observed weakness is the updated teammate bot: {friend['wdl'][0]} wins and {friend['wdl'][2]} losses.** "
             'Wins against local synthetic profiles do not establish a consistent advantage against that opponent. '
             'The earlier 2/4 check used different seeds; these runs are not evidence that the unchanged policy became worse.']
text += ['', '## What was run', '',
         '- Four newly generated seed blocks, both assignments, both official stages: 16 matches per opponent.',
         '- Each 400/1,000-hand match comprised two fresh-process 200/500-hand legs.',
         '- Official 30/75-second per-leg time banks and response limits were enabled.',
         '- Linux CPython 3.11.9, NumPy 2.2.6; four concurrent matches; BLAS thread limits set to one.',
         '- This broad run did not impose CPU affinity or an address-space limit. Separate constrained release validation is archived in the earlier daily review.',
         '- The updated organizer engine and all frozen opponents were unchanged.', '',
         '## Reliability and runtime', '',
         f"- Full matrix validation passed: {len(rows)}/96 unique expected matches, both legs and artifact hashes checked.",
         f"- Match forfeits: {len(summary['forfeits'])}.",
         f"- Our correction notices / diagnostic bytes: {summary['our_notices']} / {summary['our_diagnostics']}.",
         f"- All bots' correction notices / diagnostic bytes: {summary['all_bot_notices']} / {summary['all_bot_diagnostics']}."]
for stage, runtime in summary['by_stage_runtime'].items():
    text.append(f"- Stage {stage}: largest per-leg bank {runtime['max_leg_bank_s']:.2f}/{runtime['bank_limit_s']} s; largest response {runtime['max_reply_ms']:.2f} ms.")
text += ['', '## Interpretation', '',
         'These results measure this declared local pool, not a tournament-wide win probability. '
         'The five synthetic families share project infrastructure and are not five independently established strong entrants. '
         'Four seed blocks are limited evidence; assignment results within a seed are related. '
         'Opponent sampling is time-adaptive, so scheduling and host load can change action paths. '
         'Do not pool these fresh results with earlier inspected seeds as if they were a single untouched confirmation study.', '',
         '## Exact artifact and reproduction', '',
         f"- Current bot SHA-256: `{meta['candidate_sha256']}`.",
         '- Friend Git blob, checked again through the connected GitHub account before the run: `a5c8b01162763bb9c67051a5a625eb06607baf5a`.',
         '- Project: `C:\\Users\\varun\\OneDrive\\Documents\\ChatGPT\\PokerBots`.',
         '- Evidence directory: `experiments/requested-field-test-1110/`.',
         '- `plan.json`, `seeds.json`, `command.json`, `results.meta.json`, `results.jsonl`, `summary.json` and the frozen bot files preserve the exact setup and results.',
         '- Run the argument array in `command.json` from the project root, changing `--out` to a new path. Existing reports must not be overwritten.',
         '- Reusing these seeds is reproduction, not new holdout evidence.', '',
         'No submission upload, Git push or strategy promotion was performed by this test.']
with (root / 'RESULTS.md').open('x') as f:
    f.write('\n'.join(text) + '\n')
print(json.dumps(summary, indent=2))
