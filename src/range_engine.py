"""Vectorised postflop: NumPy hand evaluator, opponent range model, discard search
and street-by-street betting policy."""
import sys
import json
import time
import math
import random
import base64
import gc
import zlib
import struct
import itertools
import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

try:
    import numpy as np
    HAVE_NP = True
except Exception:
    np = None
    HAVE_NP = False

DEBUG = False

PARAMS = {
    "max_reply_s": 0.8,
    "clock_share": 0.25,
    "clock_decisions_per_hand": 2.5,
    "emergency_floor_ms": 4000,
    "emergency_ms_per_hand": 15,
    "fallback_call_frac": 0.1,
    "kd_flush_draw": 0.80,
    "kd_nut_flush_draw": 0.12,
    "kd_backdoor": 0.08,
    "kd_oesd": 0.7,
    "kd_gutshot": 0.3,
    "kd_overcard": 0.06,
    "kd_pocket": 0.06,
    "kd_ace": 0.08,
    "keep_beta": 6.0,
    "discard_samples": 3000,
    "discard_batch": 400,
    "discard_tie": 0.010,
    "rm_alpha": 8.0,
    "rm_floor": 0.015,
    "rm_aggr_prior": (0.4, 0.2, 0.1, 0.06),
    "rm_cont_base": 0.75,
    "rm_cont_slope": 0.39,
    "rm_size_shift": 0.16,
    "eq_flop_samples": 2000,
    "eq_batch": 400,
    "eq_min_samples": 400,
    "eq_turn_epochs": 2,
    "eq_cont_alpha": 12.0,
    "pf_open_cut": 0.25,
    "pf_limp_cut": 0.05,
    "pf_open_size": 4,
    "pf_open_size_loose": 5,
    "pf_loose_fold": 0.22,
    "pf_iso_cut": 0.60,
    "pf_iso_size": 6,
    "pf_call_margin": 0.012,
    "pf_oop_margin": 0.01,
    "pf_big_margin": 0.01,
    "pf_shove_margin": 0.030,
    "pf_shove_rate": 0.62,
    "pf_big_frac": 0.4,
    "pf_value_eq": 0.63,
    "pf_jam_eq": 0.68,
    "pf_value_freq": 0.85,
    "pf_raise_mult": 3.5,
    "pf_bluff_freq": 0.10,
    "pf_bluff_fold": 0.28,
    "pf_prior_small": (0.35, 0.15, 0.08, 0.06, 0.25),
    "pf_prior_big": (0.12, 0.10, 0.10, 0.10, 0.10),
    "pf_size_ref": (5.0, 14.0, 30.0, 60.0, 6.0),
    "pf_fold_prior": 0.45,
    "opp_prior_n": 6.0,
    "agg_prior": 0.35,
    "agg_min_n": 20,
    "rm_floor_min": 0.004,
    "rm_floor_max": 0.08,
    "bluff_prior": 0.24,
    "bluff_prior_n": 5.0,
    "bluff_pct": 0.45,
    "static_min_n": 30,
    "static_share": 0.90,
    "static_margin": 0.02,
    "alpha_cap": 1.25,
    "alpha_sep_ref": 0.4,
    "keep_prior_rate": 0.80,
    "beta_cap": 1.8,
    "pf_steal_base": 0.54,
    "pf_steal_slope": 1.5,
    "bet_sizes": (0.33, 0.5, 0.75, 1.0, 1.5),
    "fold_prior": {
        "flop": (0.28, 0.36, 0.42, 0.48),
        "turn": (0.32, 0.40, 0.46, 0.52),
        "river": (0.34, 0.44, 0.50, 0.55),
    },
    "fold_edges": (0.4, 0.8, 1.2),
    "fold_raise_mult": 0.75,
    "sel_floor": 0.22,
    "real_ip": {"flop": 0.95, "turn": 0.97, "river": 1.0},
    "real_oop": {"flop": 0.88, "turn": 0.92, "river": 1.0},
    "reraise_prob": 0.15,
    "rr_range": 0.15,
    "mix_eps": 0.03,
    "spr_shove": 1.75,
    "max_shove_spr": 2.0,
    "mdf_slack": 0.012,
    "mdf_aggr": 0.38,
    "big_call_tax": 0.02,
    "big_call_min": 33,
    "big_call_odds": 0.3,
    "cbet_freq": 0.75,
    "cbet_fold_min": 0.30,
    "cbet_tol": 0.08,
    "sd_str_n": 4.0,
    "rr_fold_mult": 0.6,
    "raise_tax": 0.20,
    "raise_sel_hi": 0.22,
    "raise_sel_lo": 0.08,
    "raise_size_lo": 0.35,
    "raise_size_hi": 0.75,
}

RANKS = "23456789TJQKA"
STREETS = ("preflop", "flop", "turn", "river")
STREET_WEIGHT = {"preflop": 0.2, "flop": 1.0, "discard": 1.0, "turn": 1.2, "river": 1.0}

_LOG_BUDGET = [8000]


def range_log(*parts):
    # stderr only, capped so a match never produces more than a few KB
    if not DEBUG or _LOG_BUDGET[0] <= 0:
        return
    text = " ".join(str(p) for p in parts) + "\n"
    _LOG_BUDGET[0] -= len(text)
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
    except Exception:
        pass


def send(obj):
    # the only place that writes to stdout
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def rank_of(card):
    return RANKS.index(card[0])


def as_int(x, default=0):
    try:
        if isinstance(x, bool):
            return default
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return default


SUITS = "shdc"


def parse_card(card):
    # card int is rank * 4 + suit, rank 0..12 for 2..A, suit order s h d c
    return RANKS.index(card[0]) * 4 + SUITS.index(card[1])


def card_str(c):
    return RANKS[c >> 2] + SUITS[c & 3]


# Hand score: category in bits 20+, then five 4-bit rank fields (0..12).
# Categories: 0 high card .. 8 straight flush, same order as the engine tuples.

def _build_tables():
    hb = [0] * 8192
    top5 = [0] * 8192
    sh = [0] * 8192
    for m in range(1, 8192):
        ranks = [r for r in range(12, -1, -1) if m >> r & 1]
        hb[m] = ranks[0]
        enc = 0
        for i in range(5):
            enc = (enc << 4) | (ranks[i] if i < len(ranks) else 0)
        top5[m] = enc
        for high in range(12, 3, -1):
            window = 0x1F << (high - 4)
            if m & window == window:
                sh[m] = high + 2
                break
        else:
            if m & 0x100F == 0x100F:
                sh[m] = 5
    return hb, top5, sh


_HB, _TOP5, _SH = _build_tables()
STRAIGHT_HIGH = _SH
TOP5 = _TOP5

if HAVE_NP:
    _HB_NP = np.array(_HB, dtype=np.int64)
    _TOP5_NP = np.array(_TOP5, dtype=np.int64)
    _SH_NP = np.array(_SH, dtype=np.int64)


def eval_one(cards):
    """Score of 5 to 7 card ints; same encoding as eval_batch."""
    cnt = [0] * 13
    scnt = [0, 0, 0, 0]
    smask = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        r = c >> 2
        s = c & 3
        cnt[r] += 1
        scnt[s] += 1
        smask[s] |= 1 << r
        mask |= 1 << r
    m2 = m3 = m4 = 0
    for r in range(13):
        n = cnt[r]
        if n > 1:
            if n == 2:
                m2 |= 1 << r
            elif n == 3:
                m3 |= 1 << r
            else:
                m4 |= 1 << r
    fm = 0
    for s in range(4):
        if scnt[s] >= 5:
            fm = smask[s]
    if fm:
        v = _SH[fm]
        if v:
            return (8 << 20) | ((v - 2) << 16)
    if m4:
        q = _HB[m4]
        return (7 << 20) | (q << 16) | (_HB[mask & ~(1 << q)] << 12)
    if m3:
        t = _HB[m3]
        pc = (m3 & ~(1 << t)) | m2
        if pc:
            return (6 << 20) | (t << 16) | (_HB[pc] << 12)
    if fm:
        return (5 << 20) | _TOP5[fm]
    v = _SH[mask]
    if v:
        return (4 << 20) | ((v - 2) << 16)
    if m3:
        t = _HB[m3]
        return (3 << 20) | (t << 16) | ((_TOP5[mask & ~(1 << t)] >> 4) & 0xFF00)
    if m2:
        p = _HB[m2]
        rest = m2 & ~(1 << p)
        if rest:
            p2 = _HB[rest]
            k = _HB[mask & ~(1 << p) & ~(1 << p2)]
            return (2 << 20) | (p << 16) | (p2 << 12) | (k << 8)
        return (1 << 20) | (p << 16) | ((_TOP5[mask & ~(1 << p)] >> 4) & 0xFFF0)
    return _TOP5[mask]


def eval_batch(H):
    """Scores for an (N, k) array of card ints, k in 5..7."""
    if not HAVE_NP:
        return [eval_one(row) for row in H]
    H = np.asarray(H, dtype=np.int64)
    rank = H >> 2
    suit = H & 3
    bits = np.left_shift(1, rank)
    mask = np.bitwise_or.reduce(bits, axis=1)
    # Three bits per rank or suit hold its count without overflow (at most seven cards).
    rank_shift = 3 * rank
    rank_counts = np.left_shift(1, rank_shift).sum(axis=1)
    same = (rank_counts[:, None] >> rank_shift) & 7
    m2 = np.bitwise_or.reduce(np.where(same == 2, bits, 0), axis=1)
    m3 = np.bitwise_or.reduce(np.where(same == 3, bits, 0), axis=1)
    m4 = np.bitwise_or.reduce(np.where(same == 4, bits, 0), axis=1)
    suit_shift = 3 * suit
    suit_counts = np.left_shift(1, suit_shift).sum(axis=1)
    ssame = (suit_counts[:, None] >> suit_shift) & 7
    fm = np.bitwise_or.reduce(np.where(ssame >= 5, bits, 0), axis=1)

    score = _TOP5_NP[mask]

    # one pair
    p = _HB_NP[m2]
    rest = mask & ~np.left_shift(1, p)
    pair = (1 << 20) | (p << 16) | ((_TOP5_NP[rest] >> 4) & 0xFFF0)
    score = np.where(m2 != 0, pair, score)

    # two pair, the best two of up to three pairs
    p2 = _HB_NP[m2 & ~np.left_shift(1, p)]
    k = _HB_NP[rest & ~np.left_shift(1, p2)]
    two = (2 << 20) | (p << 16) | (p2 << 12) | (k << 8)
    score = np.where((m2 & (m2 - 1)) != 0, two, score)

    # trips
    t = _HB_NP[m3]
    rest3 = mask & ~np.left_shift(1, t)
    trips = (3 << 20) | (t << 16) | ((_TOP5_NP[rest3] >> 4) & 0xFF00)
    score = np.where(m3 != 0, trips, score)

    # straight
    sv = _SH_NP[mask]
    score = np.where(sv != 0, (4 << 20) | ((sv - 2) << 16), score)

    # flush
    score = np.where(fm != 0, (5 << 20) | _TOP5_NP[fm], score)

    # full house, the second trip counts as the pair
    pc = (m3 & ~np.left_shift(1, t)) | m2
    full = (6 << 20) | (t << 16) | (_HB_NP[pc] << 12)
    score = np.where((m3 != 0) & (pc != 0), full, score)

    # quads
    q = _HB_NP[m4]
    kq = _HB_NP[mask & ~np.left_shift(1, q)]
    quads = (7 << 20) | (q << 16) | (kq << 12)
    score = np.where(m4 != 0, quads, score)

    # straight flush
    fv = _SH_NP[fm]
    score = np.where(fv != 0, (8 << 20) | ((fv - 2) << 16), score)
    return score


class Clock:
    """Per-decision time budget derived from the remaining bank."""

    def __init__(self):
        self.bank_ms = 30000
        self.per_response_ms = 5000
        self.total_hands = 200
        self.hand_id = 1
        self.time_left_ms = 30000

    def configure(self, msg):
        self.bank_ms = max(1, as_int(msg.get("time_bank_ms"), 30000))
        self.per_response_ms = max(1, as_int(msg.get("per_response_ms"), 5000))
        self.total_hands = max(1, as_int(msg.get("total_hands"), 200))
        self.time_left_ms = self.bank_ms
        self.hand_id = 1

    def observe(self, msg):
        left = msg.get("time_left_ms")
        if isinstance(left, (int, float)) and not isinstance(left, bool) and left == left:
            self.time_left_ms = left
        hand_id = as_int(msg.get("hand_id"))
        if hand_id > 0:
            self.hand_id = hand_id

    def hands_left(self):
        return max(1, self.total_hands - self.hand_id + 1)

    def emergency(self):
        floor = max(PARAMS["emergency_floor_ms"],
                    PARAMS["emergency_ms_per_hand"] * self.hands_left())
        return self.time_left_ms < floor

    def budget(self, street="flop"):
        """Seconds available for the current decision; 0 means table-only."""
        if self.emergency():
            return 0.0
        decisions = self.hands_left() * PARAMS["clock_decisions_per_hand"]
        share = PARAMS["clock_share"] * (self.time_left_ms / 1000.0) / decisions
        cap = min(PARAMS["max_reply_s"], 0.5 * self.per_response_ms / 1000.0)
        return min(cap, share * STREET_WEIGHT.get(street, 1.0))

    def deadline(self, street="flop"):
        return time.perf_counter() + self.budget(street)


def parse_history(history, my_seat="button", stack=200, small_blind=1, big_blind=2):
    """Replay the voluntary actions from the blinds and describe each one."""
    me = 0 if my_seat == "button" else 1
    committed = [small_blind, big_blind]
    bets = [small_blind, big_blind]
    street = "preflop"
    raises = 1
    actions = []
    for entry in history or []:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("action")
        who = {"me": me, "opp": 1 - me}.get(entry.get("actor"))
        if who is None or kind not in ("fold", "check", "call", "raise"):
            continue
        if entry.get("street") in STREETS and entry["street"] != street:
            street = entry["street"]
            bets = [0, 0]
            raises = 0
        own, other = bets[who], bets[1 - who]
        pot_before = sum(committed)
        amount = entry.get("amount")
        if kind == "call":
            to = as_int(amount, other)
        elif kind == "raise":
            to = as_int(amount, other + big_blind)
        else:
            to = own
        add = max(0, to - own) if kind in ("call", "raise") else 0
        add = min(add, stack - committed[who])
        to = own + add
        bets[who] = to
        committed[who] += add
        if kind == "raise":
            raises += 1
        actions.append({
            "street": street,
            "actor": "me" if who == me else "opp",
            "action": kind,
            "to": to,
            "added": add,
            "to_call": max(0, other - own),
            "pot_before": pot_before,
            "frac": add / pot_before if kind == "raise" and pot_before else 0.0,
            "is_raise": kind == "raise",
            "is_bet": kind == "raise" and other == 0,
            "is_allin": kind in ("call", "raise") and committed[who] >= stack,
            "raise_no": raises,
        })
    return ParsedHistory(actions, committed, bets, street, raises)


class ParsedHistory:
    def __init__(self, actions, committed, bets, street, raises):
        self.actions = actions
        self.committed = committed
        self.bets = bets
        self.street = street
        self.raises = raises

    @property
    def pot(self):
        return sum(self.committed)


class HandState:
    def __init__(self, hand_id, seat, hole):
        self.hand_id = hand_id
        self.seat = seat
        self.hole = list(hole)
        self.board = []
        self.pot = 3
        self.street = "preflop"
        self.my_discard = None
        self.opp_discard = None

    def observe(self, req):
        board = req.get("board")
        if isinstance(board, list):
            self.board = [c for c in board if isinstance(c, str)]
        if req.get("street") in STREETS:
            self.street = req["street"]
        self.pot = as_int(req.get("pot"), self.pot)
        hole = req.get("hole_cards")
        if isinstance(hole, list) and hole:
            self.hole = [c for c in hole if isinstance(c, str)]

    def on_discard(self, msg):
        self.my_discard = msg.get("my_discard")
        self.opp_discard = msg.get("opp_discard")
        hole = msg.get("hole_cards")
        if isinstance(hole, list) and hole:
            self.hole = [c for c in hole if isinstance(c, str)]


class OppModel:
    """Running opponent statistics with pseudo-count priors."""

    def __init__(self):
        self.pf_opps = [0] * 5
        self.pf_small = [0] * 5
        self.pf_big = [0] * 5
        self.pf_fold = [0, 0]
        self.pf_fold3 = [0, 0]
        self.agg = [0, 0]
        self.fold_c = {}
        self.hands = 0
        self.pf_acted = 0
        self.vpip = 0
        self.pfr = 0
        self.limps = 0
        self.pf_allin = [0] * 5
        self.bet_chk = [0, 0]
        self.face = [0, 0]
        self.chk_raise = [0, 0]
        self.bet_frac = [0.0, 0]
        self.kinds = {"fold": 0, "check": 0, "call": 0, "raise": 0}
        self.sd_agg = [0, 0.0]
        self.sd_pas = [0, 0.0]
        self.keep_hits = [0, 0]
        self.bluffs = [0, 0]
        self.sd_str = {}
        self._mean_tab = {}

    @staticmethod
    def bucket(ratio):
        return sum(1 for e in PARAMS["fold_edges"] if ratio >= e)

    def update(self, msg, seat, stack):
        parsed = parse_history(msg.get("history"), seat, stack)
        opp_bb = seat == "button"
        prev = None
        first = True
        checked = set()
        for a in parsed.actions:
            if a["actor"] == "opp":
                self.kinds[a["action"]] += 1
                if a["street"] == "preflop":
                    k = a["raise_no"] - 1 - (1 if a["is_raise"] else 0)
                    key = 4 if (k <= 0 and opp_bb) else min(max(k, 0), 3)
                    self.pf_opps[key] += 1
                    if first:
                        first = False
                        self.pf_acted += 1
                        if a["action"] in ("call", "raise"):
                            self.vpip += 1
                        if a["is_raise"]:
                            self.pfr += 1
                        elif a["action"] == "call" and k <= 0 and not opp_bb:
                            self.limps += 1
                    if a["is_allin"] and a["is_raise"]:
                        self.pf_allin[key] += 1
                    if a["is_raise"]:
                        big = a["is_allin"] or a["to"] >= PARAMS["pf_big_frac"] * stack
                        (self.pf_big if big else self.pf_small)[key] += 1
                else:
                    self.agg[1] += 1
                    if a["is_raise"]:
                        self.agg[0] += 1
                        self.bet_frac[0] += min(3.0, a["frac"])
                        self.bet_frac[1] += 1
                    if a["to_call"] <= 0:
                        self.bet_chk[1] += 1
                        if a["is_raise"]:
                            self.bet_chk[0] += 1
                        else:
                            checked.add(a["street"])
                    else:
                        self.face[1] += 1
                        if a["is_raise"]:
                            self.face[0] += 1
                        if a["street"] in checked:
                            self.chk_raise[1] += 1
                            if a["is_raise"]:
                                self.chk_raise[0] += 1
                if prev is not None and prev["actor"] == "me" and prev["is_raise"] \
                        and prev["street"] == a["street"]:
                    folded = 1 if a["action"] == "fold" else 0
                    if a["street"] == "preflop":
                        self.pf_fold[0] += folded
                        self.pf_fold[1] += 1
                        if prev["raise_no"] >= 3:
                            self.pf_fold3[0] += folded
                            self.pf_fold3[1] += 1
                    else:
                        b = self.bucket(prev["frac"])
                        lvl = min(2, max(0, prev["raise_no"] - 1))
                        cell = self.fold_c.setdefault((a["street"], lvl, b), [0, 0])
                        cell[0] += folded
                        cell[1] += 1
            prev = a
        self.hands += 1
        try:
            self.showdown(msg, parsed)
        except Exception as exc:
            range_log("showdown stats error", repr(exc))

    def showdown(self, msg, parsed):
        """Learn how honest his actions and discards are from the cards he showed."""
        hole = msg.get("opp_hole_cards")
        gone = msg.get("opp_discard")
        board = msg.get("board")
        if not (isinstance(hole, list) and len(hole) == 2 and isinstance(gone, str)
                and isinstance(board, list) and len(board) >= 3):
            return
        three = [parse_card(c) for c in hole] + [parse_card(gone)]
        flop = [parse_card(c) for c in board[:3]]
        if len(set(three) | set(flop)) != 6:
            return
        cls = class_of(three)
        if cls >= 0:
            pct = PF_PCT[cls]
            for a in parsed.actions:
                if a["actor"] == "opp" and a["street"] == "preflop" and a["action"] != "fold":
                    side = self.sd_agg if a["is_raise"] else self.sd_pas
                    side[0] += 1
                    side[1] += pct
        self.bet_honesty(hole, board, parsed)
        ks = keep_scores([three], flop)[0]
        top = max(range(3), key=lambda i: ks[i])
        self.keep_hits[1] += 1
        if top == 2:
            self.keep_hits[0] += 1

    def bet_honesty(self, hole, board, parsed):
        """Count his showdown bets that were made with a clearly below-median hand."""
        if not HAVE_NP or len(board) < 5:
            return
        pair = [parse_card(c) for c in hole]
        cards = [parse_card(c) for c in board[:5]]
        seen = set()
        for a in parsed.actions:
            if (a["actor"] != "opp" or not a["is_raise"] or a["street"] in seen
                    or a["street"] == "preflop"):
                continue
            seen.add(a["street"])
            bd = cards[:{"flop": 3, "turn": 4, "river": 5}[a["street"]]]
            dead = set(pair) | set(bd)
            live = np.array([c for c in range(52) if c not in dead], dtype=np.int64)
            i, j = np.triu_indices(len(live), 1)
            rows = np.concatenate([np.stack([live[i], live[j]], axis=1), _rows(bd, len(i))],
                                  axis=1)
            theirs = eval_one(pair + bd)
            sc = eval_batch(rows)
            pct = float(((sc < theirs).sum() + 0.5 * (sc == theirs).sum()) / len(sc))
            key = (a["street"] == "flop", a["is_bet"], self.bucket(a["frac"]))
            cell = self.sd_str.setdefault(key, [0, 0.0])
            cell[0] += 1
            cell[1] += pct
            self.bluffs[1] += 1
            if pct < PARAMS["bluff_pct"]:
                self.bluffs[0] += 1

    def center(self, street, is_bet, frac, prior, a):
        """Postflop bet threshold, moved toward the strength he showed with this size."""
        if street == "preflop" or a <= 0:
            return prior
        n, tot = self.sd_str.get((street == "flop", is_bet, self.bucket(frac)), (0, 0.0))
        if n == 0:
            return prior
        key = round(a, 1)
        if key not in self._mean_tab:
            grid = np.linspace(0.0, 1.0, 201)
            cs = np.linspace(-0.5, 1.0, 151)
            wt = 1.0 / (1.0 + np.exp(-key * (grid[None, :] - cs[:, None])))
            self._mean_tab[key] = (cs, (wt * grid).sum(axis=1) / wt.sum(axis=1))
        cs, means = self._mean_tab[key]
        obs = float(np.interp(tot / n, means, cs))
        k = PARAMS["sd_str_n"]
        return (prior * k + obs * n) / (k + n)

    def floor(self):
        """Likelihood floor for hands outside his betting range; small when he never bluffs."""
        s = PARAMS["bluff_prior_n"]
        b = (PARAMS["bluff_prior"] * s + self.bluffs[0]) / (s + self.bluffs[1])
        lo = PARAMS["rm_floor_min"]
        v = lo + (PARAMS["rm_floor"] - lo) * b / PARAMS["bluff_prior"]
        return min(PARAMS["rm_floor_max"], max(lo, v))

    def pf_rate(self, key, big):
        table = PARAMS["pf_prior_big" if big else "pf_prior_small"]
        hits = self.pf_big if big else self.pf_small
        s = PARAMS["opp_prior_n"]
        return (table[key] * s + hits[key]) / (s + self.pf_opps[key])

    def pf_jam_rate(self, key):
        s = PARAMS["opp_prior_n"]
        return (PARAMS["pf_prior_big"][key] * s + self.pf_allin[key]) / (s + self.pf_opps[key])

    def pf_range(self, key, big, size):
        """Share of hands he raises with at this spot and size."""
        if big:
            return min(1.0, max(0.02, self.pf_rate(key, True)))
        p = self.pf_rate(key, False) + self.pf_rate(key, True)
        ref = PARAMS["pf_size_ref"][key]
        p *= min(1.2, max(0.6, (ref / max(size, 1)) ** 0.5))
        return min(1.0, max(0.03, p))

    def pf_fold_to_raise(self):
        s = PARAMS["opp_prior_n"]
        return (PARAMS["pf_fold_prior"] * s + self.pf_fold[0]) / (s + self.pf_fold[1])

    def pf_fold_to_3bet(self):
        s = PARAMS["opp_prior_n"]
        return (PARAMS["pf_fold_prior"] * s + self.pf_fold3[0]) / (s + self.pf_fold3[1])

    def aggression(self):
        """Postflop bet/raise share of his actions, None until enough are seen."""
        if self.agg[1] < PARAMS["agg_min_n"]:
            return None
        s = PARAMS["opp_prior_n"]
        return (PARAMS["agg_prior"] * s + self.agg[0]) / (s + self.agg[1])

    def fold_prob(self, street, ratio, facing_raise=0):
        """Chance he folds to a bet of this size (fraction of the pot).

        facing_raise: 0 for our bet, 1 for our raise over his bet, 2 for a re-raise over his raise."""
        lvl = min(2, int(facing_raise))
        b = self.bucket(ratio)
        prior = PARAMS["fold_prior"].get(street, PARAMS["fold_prior"]["river"])[b]
        s = PARAMS["opp_prior_n"]
        if lvl:
            # a selective bettor rarely folds the hand he just bet
            prior *= PARAMS["fold_raise_mult"] * self.bet_selectivity()
        if lvl == 2:
            prior *= PARAMS["rr_fold_mult"]
        # sparse size cells borrow from the other sizes of the same street and kind
        pooled = [0, 0]
        for key, cell in self.fold_c.items():
            if key[0] == street and key[1] == lvl:
                pooled[0] += cell[0]
                pooled[1] += cell[1]
        prior = (prior * s + pooled[0]) / (s + pooled[1])
        hit, n = self.fold_c.get((street, lvl, b), (0, 0))
        return (prior * s + hit) / (s + n)

    def bet_selectivity(self):
        """Scale 0.2..1 from how often he bets when checked to; rare bets mean strength."""
        s = PARAMS["opp_prior_n"]
        ref = PARAMS["rm_aggr_prior"][0]
        rate = (ref * s + self.bet_chk[0]) / (s + self.bet_chk[1])
        return min(1.0, max(PARAMS["sel_floor"], rate / ref))

    def reraise_prob(self):
        """Chance he raises when a postflop bet faces him."""
        s = PARAMS["opp_prior_n"]
        return (PARAMS["reraise_prob"] * s + self.face[0]) / (s + self.face[1])

    def static_kind(self):
        """The one action nearly every decision was (fold, call or raise), else None."""
        k = self.kinds
        groups = (("fold", k["fold"]), ("call", k["check"] + k["call"]), ("raise", k["raise"]))
        n = sum(g[1] for g in groups)
        if n < PARAMS["static_min_n"]:
            return None
        name, top = max(groups, key=lambda g: g[1])
        return name if top >= PARAMS["static_share"] * n else None

    def static(self):
        """True once nearly every decision he made was the same action."""
        return self.static_kind() is not None

    def alpha(self):
        """Steepness of his action-versus-strength link, shrunk toward the default."""
        base = PARAMS["rm_alpha"]
        if self.static():
            return 0.0
        n = min(self.sd_agg[0], self.sd_pas[0])
        if n == 0:
            return base
        sep = self.sd_agg[1] / self.sd_agg[0] - self.sd_pas[1] / self.sd_pas[0]
        est = base * min(PARAMS["alpha_cap"], max(0.0, sep / PARAMS["alpha_sep_ref"]))
        s = PARAMS["opp_prior_n"]
        return (base * s + est * n) / (s + n)

    def alpha_post(self):
        """Steepness for his postflop actions.

        The preflop showdown gap says little about postflop play: someone who opens
        any three cards can still bet strictly for value later. When the bets he
        showed down were rarely weak hands, keep the full steepness after the flop."""
        a = self.alpha()
        if self.static():
            return a
        s = PARAMS["bluff_prior_n"]
        weak = (PARAMS["bluff_prior"] * s + self.bluffs[0]) / (s + self.bluffs[1])
        span = PARAMS["bluff_pct"] - PARAMS["bluff_prior"]
        honest = min(1.0, max(0.0, (PARAMS["bluff_pct"] - weak) / span))
        return max(a, PARAMS["rm_alpha"] * honest)

    def beta(self):
        """Discard sharpness: a one-in-three match with our keep model means random."""
        base = PARAMS["keep_beta"]
        if self.static():
            return 0.0
        s = PARAMS["opp_prior_n"]
        rate = (PARAMS["keep_prior_rate"] * s + self.keep_hits[0]) / (s + self.keep_hits[1])
        span = PARAMS["keep_prior_rate"] - 1.0 / 3.0
        return base * min(PARAMS["beta_cap"], max(0.0, (rate - 1.0 / 3.0) / span))

    def freq(self, street, depth):
        """Share of his range that makes the depth-th bet or raise on this street."""
        s = PARAMS["opp_prior_n"]
        prior = PARAMS["rm_aggr_prior"]
        if street == "preflop":
            key = min(max(depth, 1) - 1, 3)
            return self.pf_rate(key, False) + self.pf_rate(key, True)
        if depth <= 1:
            return (prior[0] * s + self.bet_chk[0]) / (s + self.bet_chk[1])
        return (prior[1] * s + self.face[0]) / (s + self.face[1])

    def cont(self, street, faced, raised=0):
        """Share of his range that continues against a bet of this size."""
        if street == "preflop":
            return None
        return 1.0 - self.fold_prob(street, faced, raised)

    def range_args(self):
        return {"alpha": self.alpha(), "alpha_post": self.alpha_post(),
                "beta": self.beta(), "freq_fn": self.freq,
                "cont_fn": self.cont, "floor": self.floor(),
                "center_fn": self.center if HAVE_NP else None}


class MatchState:
    def __init__(self):
        self.clock = Clock()
        self.stack = 200
        self.net = 0
        self.hands_done = 0
        self.hand = None
        self.opp = OppModel()

    def configure(self, msg):
        self.clock.configure(msg)
        self.stack = max(1, as_int(msg.get("starting_stack"), 200))

    def new_hand(self, msg):
        self.clock.observe(msg)
        seat = msg.get("seat") if msg.get("seat") in ("button", "big_blind") else "button"
        self.hand = HandState(as_int(msg.get("hand_id"), self.clock.hand_id), seat,
                              msg.get("hole_cards") or [])

    def observe(self, req):
        self.clock.observe(req)
        if self.hand is None:
            self.hand = HandState(self.clock.hand_id, "button", req.get("hole_cards") or [])
        self.hand.observe(req)

    def discard_result(self, msg):
        if self.hand is not None:
            self.hand.on_discard(msg)

    def hand_result(self, msg):
        net = as_int(msg.get("net"))
        self.net += net
        self.hands_done += 1
        seat = self.hand.seat if self.hand is not None else "button"
        try:
            self.opp.update(msg, seat, self.stack)
        except Exception as exc:
            range_log("opp model error", repr(exc))
        self.hand = None


STATE = MatchState()


def fallback_action(req):
    legal = req.get("legal_actions") or []
    if "check" in legal:
        return {"type": "action", "action": "check"}
    pot = as_int(req.get("pot"))
    to_call = as_int(req.get("to_call"))
    if "call" in legal and to_call <= PARAMS["fallback_call_frac"] * pot:
        return {"type": "action", "action": "call"}
    if "fold" in legal:
        return {"type": "action", "action": "fold"}
    if "call" in legal:
        return {"type": "action", "action": "call"}
    return {"type": "action", "action": "check"}


def legalize(action, req):
    """Last check: force the reply into the set of legal actions."""
    legal = req.get("legal_actions") or []
    kind = action.get("action")
    if kind == "raise":
        if "raise" in legal:
            lo = as_int(req.get("min_raise"))
            hi = as_int(req.get("max_raise"), lo)
            amount = as_int(action.get("amount"), lo)
            amount = max(lo, min(hi, amount))
            return {"type": "action", "action": "raise", "amount": amount}
        kind = "call" if as_int(req.get("to_call")) > 0 else "check"
    if kind in legal:
        return {"type": "action", "action": kind}
    return fallback_action(req)


def fallback_discard(req):
    cards = [c for c in (req.get("hole_cards") or []) if isinstance(c, str) and len(c) >= 2]
    if not cards:
        return None
    ranks = [rank_of(c) for c in cards]
    paired = {r for r in ranks if ranks.count(r) > 1}
    pool = [c for c in cards if rank_of(c) not in paired] or cards
    return min(pool, key=rank_of)

# ---- keep model: how a hand of three cards is likely to be trimmed to two

def _build_outs():
    # ranks that would complete a straight, for every rank mask
    outs = [0] * 8192
    for m in range(8192):
        if _SH[m]:
            continue
        n = 0
        for r in range(13):
            if not m >> r & 1 and _SH[m | (1 << r)]:
                n += 1
        outs[m] = n
    return outs


_OUTS = _build_outs()
if HAVE_NP:
    _OUTS_NP = np.array(_OUTS, dtype=np.int64)


def _keep_score_one(kept, flop):
    """Value of keeping two cards on the given flop (scalar form of keep_scores)."""
    val = eval_one(list(kept) + list(flop)) / 1048576.0
    fmask = 0
    fsuit = [0, 0, 0, 0]
    fmax = 0
    for c in flop:
        fmask |= 1 << (c >> 2)
        fsuit[c & 3] += 1
        fmax = max(fmax, c >> 2)
    mask = fmask
    for c in kept:
        mask |= 1 << (c >> 2)
    if not _SH[mask]:
        gain = _OUTS[mask] - _OUTS[fmask]
        if gain >= 2:
            val += PARAMS["kd_oesd"]
        elif gain == 1:
            val += PARAMS["kd_gutshot"]
    for s in range(4):
        ks = sum(1 for c in kept if c & 3 == s)
        tot = ks + fsuit[s]
        if tot == 4 and ks >= 1:
            val += PARAMS["kd_flush_draw"]
            if any(c & 3 == s and c >> 2 == 12 for c in kept):
                val += PARAMS["kd_nut_flush_draw"]
        elif tot == 3 and ks >= 1:
            val += PARAMS["kd_backdoor"]
    a, b = kept[0] >> 2, kept[1] >> 2
    val += PARAMS["kd_overcard"] * ((a > fmax) + (b > fmax))
    if a == b:
        val += PARAMS["kd_pocket"] * (1 + a / 12.0)
    if a == 12 or b == 12:
        val += PARAMS["kd_ace"]
    return val


def keep_scores(triples, flop):
    """Row per three-card hand; column i is the value of the hand left after discarding card i."""
    if not HAVE_NP:
        out = []
        for t in triples:
            out.append([_keep_score_one((t[(i + 1) % 3], t[(i + 2) % 3]), flop) for i in range(3)])
        return out
    T = np.asarray(triples, dtype=np.int64).reshape(-1, 3)
    F = np.asarray(flop, dtype=np.int64)
    n = T.shape[0]
    frank = F >> 2
    fsuit = np.bincount(F & 3, minlength=4)
    fmask = int(np.bitwise_or.reduce(np.left_shift(1, frank)))
    fmax = int(frank.max())
    fouts = _OUTS[fmask]
    out = np.empty((n, 3), dtype=np.float64)
    hands = np.empty((n, 5), dtype=np.int64)
    hands[:, 2:] = F
    for i in range(3):
        a = T[:, (i + 1) % 3]
        b = T[:, (i + 2) % 3]
        hands[:, 0] = a
        hands[:, 1] = b
        val = eval_batch(hands) / 1048576.0
        ra = a >> 2
        rb = b >> 2
        sa = a & 3
        sb = b & 3
        mask = np.left_shift(1, ra) | np.left_shift(1, rb) | fmask
        gain = _OUTS_NP[mask] - fouts
        no_straight = (_SH_NP[mask] == 0)
        val = val + no_straight * np.where(gain >= 2, PARAMS["kd_oesd"],
                                           np.where(gain == 1, PARAMS["kd_gutshot"], 0.0))
        for s in range(4):
            ks = (sa == s).astype(np.int64) + (sb == s)
            tot = ks + int(fsuit[s])
            nut = ((ra == 12) & (sa == s)) | ((rb == 12) & (sb == s))
            draw = (tot == 4) & (ks >= 1)
            val = val + draw * (PARAMS["kd_flush_draw"] + PARAMS["kd_nut_flush_draw"] * nut)
            val = val + ((tot == 3) & (ks >= 1)) * PARAMS["kd_backdoor"]
        val = val + PARAMS["kd_overcard"] * ((ra > fmax).astype(np.int64) + (rb > fmax))
        val = val + (ra == rb) * PARAMS["kd_pocket"] * (1 + ra / 12.0)
        val = val + ((ra == 12) | (rb == 12)) * PARAMS["kd_ace"]
        out[:, i] = val
    return out


def keep_probs(scores, beta):
    """Softmax over the three keep options; beta 0 is a random discarder."""
    if not HAVE_NP:
        res = []
        for row in scores:
            top = max(row)
            e = [math.exp(beta * (v - top)) for v in row]
            tot = sum(e)
            res.append([v / tot for v in e])
        return res
    sc = np.asarray(scores, dtype=np.float64)
    z = np.exp(beta * (sc - sc.max(axis=1, keepdims=True)))
    return z / z.sum(axis=1, keepdims=True)


# ---- preflop tables: 1755 suit-isomorphic three-card classes

PF_P = (0.05, 0.10, 0.20, 0.35, 0.50, 0.75)
PF_BLOB = (
    "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"
    "1mqmNe7CQbbAOSlNrZC1iO5KmtgTkS4OgEEUstYl7/FgQ+sLfsfpq7JdhaxVEslhrVnXXkOHsbXA3FLEkIfgsM1AF2WQexWy"
    "VkXn15RzxjJyxf6RrkBNOpJwltHd2oyn9yZmskot/P6XY5Ykrek81pjHHIWs9YVTNrjb/BY5ag37HDWZxFMnjIbgC8LC/E3U"
    "ZJEn1fPme+QvSnkjMRJKtv+PszX4nBWlIXaW3cOqBJmgmpnLrL12CfDX+6jJIdPUHfMt0pUW/opsKamQtZqq50DHJ+xrtAPv"
    "jxq4le5BmtrdWG9krbo49zzylq5BuiHNbxHnkAoUstYeddashIz0Bh+H7lHIWlVC01Jq0p7om8ruMU8hayXV58EL1ljaGue1"
    "S6jC34KTl4IOeZ9+wN7mSUcha41Qy4zCXw59kb8tLOyTRTaphcZcMgq5pYn4GzWJQCldxbpr72ajxUfwOIWs5Wpq5dtn6RDe"
    "F+lYIWv1dpuTefQ06+8slSdQk0fm6HFkAFgiyxkk31MKWatG6FxKf/q+s1od0YavHv4W3HjjT/jwZZYU5aVC1pqtWhkLyAl6"
    "ix3j3zgKWeu45MEb1jgk8Uf4MaGQtUaozsZUMg41FcUZ1GSRb9Rio7jdB5k2W/wKJdt/W00y3iD/2AvZyof7JMgz2rYO2y57"
    "wKPOVbxWDpmn61lz0DtXeY5THkeY6/+lfjXeJLfscex18QCrkmS23kEq0JZcOUXUHNTkkWruLLKJjuDlZQ1VWStkrR66UeGn"
    "3JnnvClXKIWsNS28PnhZrFcvuB96LUMKWeu4amhE7Ga0Jn9XvC8VstZuVddcb48G454Uq6EkAl11uvmavR1O1Ns5BiWHFNHr"
    "za/tduw4H+FkY+dkwHAnkX9oUrSTQ1U7rZC1aruapLJxvK1sonprhaw1OvwgSJzDarvL/D4hhaw1SdUwujz8d1nmiz5SIWvd"
    "Vv8a1+EEJ/gFMRVK4buy1YKtyE77OPuTH3IUslZHPcJcAW8oK7phcihkrRE6ZLWkXdnHIkOug5Lr/6GKmY+DSdrw+s5x7JMk"
    "7yCdTqWreL4sUKtwPHmku1sRE0GKIXKqWgYl3z+oy5D6dAe/4sTVI1oha22K7LZn6Y5uBb9WaHVYIWuVdDtaOfQ4+0rUkcuV"
    "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"
    "Pup+AYJOQzf96NmsQAwDm250E1Dy/WNuR/oLZ+pz3dLd6aahm+bEOsWy4vvjU+KT4348Dd20LXY99Vqsb7x7PDV+LZZeNiPQ"
    "K3QusILtdxzd1O2FIJxJrMjHxuPokzXeMf/RcHrZbHIpbBrLnPl6iHfFz4GSIPfCF4zxsoF7w7vrD4GSS+6HhXHT2ab7ee0e"
    "rkqSU5E15Loa77UJVQ4/gJJPZkTGwPl+8MqEaoe/Cafjvv8cuWSV0pb3nN8r1BNKAlQy1SzCvuAlnN3Imem47+nup2YFdgMJ"
    "9jU5SqXjvi/xHHsNv+68qzfqSW467nu297pdX8yQLXEW99103PfjkbkkX3/lWaELISOSjvv+tHvd3M/2Ytaelbd0Ou57G7eq"
    "NZbdwD0cqCZByfXX6lzzGDX5dTFL/qTScd+7eLPtGeKUvKjvuq29dNz3vt42u5MYKTfrYe4bUPL96l5PspDnyne07bZw03Hf"
    "RepIfT10I7w9UiP6CawyGajjVWKHnIp6rZvh3fLScd9HeaXoEXFB/qAPuVfddNz3Y9GPdMfwrfDsSIXo17DTJLnoDaIHBFf1"
    "sGqil477vsK7RQeJ/irDveBWgJLv1/Oa28v5JtlZt3NXu+m4771jXWL58QXxl+Kl4xdj6bjvG2J7Y9diteM149nxObHMrOwA"
    "j9S0JBLco15df00oE9enf/Qgq+ft9wNhFtkayczKJa2iP7DXvG/94uFD4QZQkmRS9Bj3/f2hz8PzIveh5JOMKOVTvPv+8ZCK"
    "rIlk4txvRt9Sg0JGmEQ+jYyDMSYD+z2Hx+QjeOL7eFu8zEShF/QEbczS1PvEaw1QyCW3orPV0tDL4YaRU5FRMM8k2eRNgzd8"
    "pwd5af4LqMkjmf5gXl1ORKZ8gGuYiXNPelmsjPOHWuN299Z5mTj3AbG1sd9iHeAg7eLfxjJx7m/HqsaOxv6NdY6nx6fHEjm5"
    "gfLRCuquXy70V6h+ZG4kgdeakZoRuhUJRU9H70THpCZy8sn81F/9YHRWNJ7aNnVuagI794rNxX+T4hnx3HggnsDOM2I3Yp3i"
    "C9FfI+JnYsm8/ECRWK3YIeT28bHhsSdj/we+3Ck7"
)

_PERMS = list(itertools.permutations(range(4)))


def canon(cards):
    """Canonical form of a set of card ints under suit relabelling."""
    best = None
    for perm in _PERMS:
        t = tuple(sorted((c & ~3) | perm[c & 3] for c in cards))
        if best is None or t < best:
            best = t
    return best


PF_INDEX = {}
PF_COMBOS = []
PF_EQ = []
PF_EQ_TOP = []
PF_PCT = []
PF_READY = False


def _decode_preflop(blob):
    global PF_READY
    if not blob:
        return
    raw = zlib.decompress(base64.b64decode(blob))
    rec = struct.Struct("<4B7H")
    for off in range(0, len(raw), rec.size):
        v = rec.unpack_from(raw, off)
        PF_INDEX[(v[0], v[1], v[2])] = len(PF_COMBOS)
        PF_COMBOS.append(v[3])
        PF_EQ.append(v[4] / 10000.0)
        PF_EQ_TOP.append([x / 10000.0 for x in v[5:]])
    order = sorted(range(len(PF_EQ)), key=PF_EQ.__getitem__)
    total = float(sum(PF_COMBOS))
    pct = [0.0] * len(PF_EQ)
    below = 0
    for i in order:
        pct[i] = (below + PF_COMBOS[i] / 2.0) / total
        below += PF_COMBOS[i]
    PF_PCT.extend(pct)
    PF_READY = len(PF_EQ) == 1755 and below == 22100


_decode_preflop("".join(PF_BLOB) if isinstance(PF_BLOB, tuple) else PF_BLOB)


def class_of(three):
    """Table index of a three-card hand (ints), -1 when the table is unavailable."""
    if not PF_READY:
        return -1
    return PF_INDEX.get(canon(three), -1)


def pf_equity_vs_range(cls, p):
    """Equity of a class against the top fraction p of starting hands (1.0 = random hand)."""
    xs = PF_P + (1.0,)
    ys = PF_EQ_TOP[cls] + [PF_EQ[cls]]
    p = min(1.0, max(0.01, p))
    if p <= xs[0]:
        slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return min(1.0, max(0.0, ys[0] + slope * (p - xs[0])))
    for i in range(1, len(xs)):
        if p <= xs[i]:
            t = (p - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


# ---- discard decision

_RNG = np.random.default_rng() if HAVE_NP else random.Random()


def _kept_pair(T, j):
    # cards left in each row after discarding column j[row]
    rows = np.arange(T.shape[0])
    return T[rows, (j + 1) % 3], T[rows, (j + 2) % 3]


def _flop_sim(my3, flop, live, n, beta, rng):
    """Sampled opponent triples, results for our keeps, and opponent keep scores."""
    idx = np.argsort(rng.random((n, live.shape[0])), axis=1)[:, :5]
    draw = live[idx]
    opp = draw[:, :3]
    board = np.concatenate([np.broadcast_to(np.asarray(flop, dtype=np.int64), (n, 3)),
                            draw[:, 3:5]], axis=1)
    ks = keep_scores(opp, flop)
    if beta is None:
        a, b = _kept_pair(opp, ks.argmax(axis=1))
        oscore = [eval_batch(np.concatenate([a[:, None], b[:, None], board], axis=1))]
        probs = None
    else:
        probs = keep_probs(ks, beta)
        oscore = []
        for j in range(3):
            oscore.append(eval_batch(np.concatenate(
                [opp[:, (j + 1) % 3, None], opp[:, (j + 2) % 3, None], board], axis=1)))
    res = np.empty((n, 3), dtype=np.float64)
    for i in range(3):
        k1, k2 = my3[(i + 1) % 3], my3[(i + 2) % 3]
        mine = eval_batch(np.concatenate(
            [np.full((n, 1), k1, dtype=np.int64), np.full((n, 1), k2, dtype=np.int64), board],
            axis=1))
        if probs is None:
            res[:, i] = (mine > oscore[0]) + 0.5 * (mine == oscore[0])
        else:
            acc = 0.0
            for j in range(3):
                acc = acc + probs[:, j] * ((mine > oscore[j]) + 0.5 * (mine == oscore[j]))
            res[:, i] = acc
    return opp, res, ks


def _discard_batch(my3, flop, live, n, weight_fn, beta, rng):
    """Weighted win+tie mass for each of my three keeps over n sampled runouts."""
    opp, res, _ = _flop_sim(my3, flop, live, n, beta, rng)
    if weight_fn is None:
        w = np.ones(n)
    else:
        w = np.asarray(weight_fn(opp), dtype=np.float64)
    return [float((w * res[:, i]).sum()) for i in range(3)], float(w.sum())


def _discard_plain(my3, flop, live, n, rng):
    # no numpy: scalar loop with the same sampling scheme
    mass = [0.0, 0.0, 0.0]
    for _ in range(n):
        d = rng.sample(live, 5)
        opp, board = d[:3], list(flop) + d[3:]
        ks = keep_scores([opp], flop)[0]
        j = ks.index(max(ks))
        o = eval_one([opp[(j + 1) % 3], opp[(j + 2) % 3]] + board)
        for i in range(3):
            m = eval_one([my3[(i + 1) % 3], my3[(i + 2) % 3]] + board)
            mass[i] += (m > o) + 0.5 * (m == o)
    return mass, float(n)


def _reveal(card, flop):
    # how much discarding this card tells the opponent about the rest of the hand
    r, s = card >> 2, card & 3
    franks = [c >> 2 for c in flop]
    score = 2.0 * (r in franks)
    score += 1.0 * (sum(1 for c in flop if c & 3 == s) >= 2)
    score += 0.5 * sum(1 for x in franks if x != r and abs(x - r) <= 2)
    return score


def discard_equities(my3, flop, n=None, deadline=None, weight_fn=None, beta=None, rng=None):
    """Estimated equity of each keep (index = discarded card) and the samples used."""
    n = PARAMS["discard_samples"] if n is None else n
    dead = set(my3) | set(flop)
    live_list = [c for c in range(52) if c not in dead]
    batch = PARAMS["discard_batch"]
    mass = [0.0, 0.0, 0.0]
    total = 0.0
    used = 0
    if HAVE_NP:
        rng = _RNG if rng is None else rng
        live = np.array(live_list, dtype=np.int64)
    else:
        rng = random.Random() if rng is None or not hasattr(rng, "sample") else rng
        n = max(20, n // 10)
        batch = max(10, batch // 10)
    while used < n:
        m = min(batch, n - used)
        if HAVE_NP:
            part, w = _discard_batch(my3, flop, live, m, weight_fn, beta, rng)
        else:
            part, w = _discard_plain(my3, flop, live_list, m, rng)
        for i in range(3):
            mass[i] += part[i]
        total += w
        used += m
        if deadline is not None and time.perf_counter() >= deadline:
            break
    total = total or 1.0
    return [v / total for v in mass], used


def pick_discard(my3, flop, eq):
    """Index to discard: best equity, near ties go to the card that reveals less."""
    best = max(eq)
    near = [i for i in range(3) if eq[i] >= best - PARAMS["discard_tie"]]
    return min(near, key=lambda i: (_reveal(my3[i], flop), my3[i] >> 2, -eq[i]))


def range_discard(req, weight_fn=None, beta=None, n=None, rng=None):
    hole = req.get("hole_cards")
    board = req.get("board")
    if not (isinstance(hole, list) and isinstance(board, list) and len(hole) == 3
            and len(board) >= 3 and len(set(hole)) == 3):
        return fallback_discard(req)
    my3 = [parse_card(c) for c in hole]
    flop = [parse_card(c) for c in board[:3]]
    if len(set(my3) | set(flop)) != 6:
        return fallback_discard(req)
    budget = STATE.clock.budget("discard")
    if budget <= 0.0 and n is None:
        ks = keep_scores([my3], flop)[0]
        return hole[max(range(3), key=lambda i: ks[i])]
    deadline = None if n is not None else time.perf_counter() + budget
    eq, _ = discard_equities(my3, flop, n=n, deadline=deadline, weight_fn=weight_fn,
                             beta=beta, rng=rng)
    return hole[pick_discard(my3, flop, eq)]


# ---- opponent range model and equity

_PF_NP = {}


def _pf_np():
    if not _PF_NP:
        triples = np.array(list(itertools.combinations(range(52), 3)), dtype=np.int64)
        ranks = triples & ~3
        suits = triples & 3
        best = np.full(len(triples), 1 << 18, dtype=np.int64)
        for perm in _PERMS:
            cards = np.sort(ranks | np.asarray(perm)[suits], axis=1)
            keys = (cards[:, 0] << 12) | (cards[:, 1] << 6) | cards[:, 2]
            np.minimum(best, keys, out=best)
        indices = np.fromiter(
            (PF_INDEX.get((key >> 12, (key >> 6) & 63, key & 63), -1) for key in best),
            dtype=np.int16, count=len(best),
        )
        lookup = np.full((52, 52, 52), -1, dtype=np.int16)
        for a, b, c in itertools.permutations(range(3)):
            lookup[triples[:, a], triples[:, b], triples[:, c]] = indices
        _PF_NP.update(lookup=lookup, pct=np.array(PF_PCT, dtype=np.float64))
    return _PF_NP


def class_batch(T):
    """Table index for each row of an (N, 3) array of card ints, -1 when unknown."""
    T = np.asarray(T, dtype=np.int64)
    return _pf_np()["lookup"][T[:, 0], T[:, 1], T[:, 2]]


def _sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30.0, 30.0)))


def _wpct(x, w=None):
    """Percentile of each value among all values (weighted), ties share the middle."""
    order = np.argsort(x, kind="stable")
    xs = x[order]
    ws = np.ones(len(x)) if w is None else w[order]
    cum = np.concatenate([[0.0], np.cumsum(ws)])
    lo = cum[np.searchsorted(xs, x, side="left")]
    hi = cum[np.searchsorted(xs, x, side="right")]
    total = cum[-1]
    if total <= 0:
        return np.full(len(x), 0.5)
    return (lo + hi) / (2.0 * total)


class RangeModel:
    """Likelihood of an opponent holding a sampled hand given what he did and discarded."""

    def __init__(self, spots=(), opp_discard=None, my_discard=None, alpha=None, beta=None,
                 freq_fn=None, cont_fn=None, floor=None, center_fn=None, alpha_post=None):
        self.spots = list(spots)
        self.opp_discard = opp_discard
        self.my_discard = my_discard
        self.alpha = PARAMS["rm_alpha"] if alpha is None else alpha
        self.alpha_post = self.alpha if alpha_post is None else alpha_post
        self.beta = PARAMS["keep_beta"] if beta is None else beta
        self.freq_fn = freq_fn
        self.cont_fn = cont_fn
        self.center_fn = center_fn
        self.floor = PARAMS["rm_floor"] if floor is None else floor
        self.dead = {c for c in (opp_discard, my_discard) if c is not None}

    @classmethod
    def from_hand(cls, history, hand, stack=200, freq_fn=None, cont_fn=None, alpha=None,
                  beta=None, floor=None, center_fn=None, alpha_post=None):
        parsed = parse_history(history, hand.seat, stack)
        spots = []
        for a in parsed.actions:
            if a["actor"] != "opp" or a["action"] == "fold":
                continue
            base = 1 if a["street"] == "preflop" else 0
            before = a["raise_no"] - base - (1 if a["is_raise"] else 0)
            owed = a["to_call"]
            spots.append({
                "street": a["street"],
                "kind": a["action"],
                "before": max(0, before),
                "faced": owed / max(1, a["pot_before"] - owed),
                "frac": a["frac"],
            })

        def card(x):
            return parse_card(x) if isinstance(x, str) and len(x) == 2 else None

        return cls(spots, card(hand.opp_discard), card(hand.my_discard), alpha=alpha, beta=beta,
                   freq_fn=freq_fn, cont_fn=cont_fn, floor=floor, center_fn=center_fn,
                   alpha_post=alpha_post)

    def freq(self, street, depth):
        """Share of his range that makes the depth-th bet or raise on this street."""
        if self.freq_fn is not None:
            v = self.freq_fn(street, depth)
            if v is not None:
                return min(0.95, max(0.02, v))
        prior = PARAMS["rm_aggr_prior"]
        return prior[min(depth, len(prior)) - 1]

    def _lik(self, sp, s):
        street = sp["street"]
        a = self.alpha if street == "preflop" else self.alpha_post
        if sp["kind"] == "raise":
            shift = PARAMS["rm_size_shift"] * (min(2.5, max(0.2, sp["frac"])) - 0.66)
            mid = 1.0 - self.freq(street, sp["before"] + 1) + shift
            if self.center_fn is not None:
                mid = self.center_fn(street, sp["before"] == 0, sp["frac"], mid, a)
            lik = _sig(a * (s - mid))
        elif sp["kind"] == "check":
            lik = 1.0 - _sig(a * (s - (1.0 - self.freq(street, 1))))
        else:
            cont = None
            if self.cont_fn is not None:
                cont = self.cont_fn(street, sp["faced"], min(2, max(0, sp["before"] - 1)))
            if cont is None:
                cont = PARAMS["rm_cont_base"] - PARAMS["rm_cont_slope"] * min(3.0, sp["faced"])
            cont = min(0.95, max(0.15, cont))
            stay = _sig(a * (s - (1.0 - cont)))
            punch = _sig(a * (s - (1.0 - self.freq(street, sp["before"] + 1))))
            lik = stay * (1.0 - punch)
        return np.maximum(lik, self.floor)

    def weights(self, T, flop, turn=None, river=None, *, known_keeps=None):
        """Weights and a current-street strength for sampled opponent hands.

        T has three columns (kept pair plus the discard once it is known, or the
        undecided triple on the flop) or two columns (kept pair only)."""
        T = np.asarray(T, dtype=np.int64)
        n = T.shape[0]
        full = T.shape[1] == 3
        cache = {}
        if known_keeps is not None:
            cache["ks"] = known_keeps

        def keeps():
            if "ks" not in cache:
                cache["ks"] = keep_scores(T, flop)
            return cache["ks"]

        def made(board):
            key = len(board)
            if key not in cache:
                B = np.broadcast_to(np.asarray(board, dtype=np.int64), (n, key))
                cache[key] = eval_batch(np.concatenate([T[:, :2], B], axis=1))
            return cache[key]

        board4 = list(flop) + [turn] if turn is not None else None
        board5 = board4 + [river] if board4 is not None and river is not None else None
        w = np.ones(n)
        strengths = {}
        for sp in self.spots:
            street = sp["street"]
            if street in strengths:
                s = strengths[street]
            elif street == "preflop" and full:
                cls = class_batch(T)
                s = np.where(cls >= 0, _pf_np()["pct"][np.maximum(cls, 0)], 0.5)
            elif street == "flop" and full:
                s = _wpct(keeps().max(axis=1))
            elif street == "turn" and board4 is not None:
                s = _wpct(made(board4))
            elif street == "river" and board5 is not None:
                s = _wpct(made(board5))
            else:
                continue
            strengths[street] = s
            w = w * self._lik(sp, s)
        if full and board4 is not None and self.opp_discard is not None:
            w = w * keep_probs(keeps(), self.beta)[:, 2]
        if board5 is not None:
            cur = made(board5)
        elif board4 is not None:
            cur = made(board4)
        elif full:
            cur = keeps().max(axis=1)
        else:
            cur = np.zeros(n)
        return w, cur


class EquityInfo:
    """Per-sample results against a weighted range, with continue-fraction reweighting."""

    def __init__(self, res, w, cur, n, keep=None, keeps=None):
        self.n = n
        self.keep = keep
        self.keeps = keeps
        if HAVE_NP:
            self.res = np.asarray(res, dtype=np.float64)
            self.w = np.asarray(w, dtype=np.float64)
            if self.w.sum() <= 0:
                self.w = np.ones(len(self.res))
            self.s = _wpct(np.asarray(cur, dtype=np.float64), self.w)
            self.e_all = float((self.w * self.res).sum() / self.w.sum())
        else:
            self.res = list(res)
            self.w = list(w)
            order = sorted(range(len(cur)), key=cur.__getitem__)
            self.s = [0.0] * len(cur)
            for rank, i in enumerate(order):
                self.s[i] = (rank + 0.5) / len(cur)
            self.e_all = sum(a * b for a, b in zip(self.w, self.res)) / sum(self.w)

    def e_vs_continue(self, f):
        """Equity against the strongest fraction f of his range (soft cut)."""
        f = min(1.0, max(0.02, f))
        if f >= 0.999:
            return self.e_all
        k = PARAMS["eq_cont_alpha"]
        if HAVE_NP:
            c = self.w * _sig(k * (self.s - (1.0 - f)))
            tot = float(c.sum())
            return float((c * self.res).sum() / tot) if tot > 0 else self.e_all
        c = [a / (1.0 + math.exp(-max(-30.0, min(30.0, k * (s - (1.0 - f))))))
             for a, s in zip(self.w, self.s)]
        tot = sum(c)
        return sum(a * r for a, r in zip(c, self.res)) / tot if tot > 0 else self.e_all


def _finish_flop(R, w, cur, n):
    tot = float(sum(w)) or 1.0
    if HAVE_NP:
        mass = [float((w * R[:, i]).sum()) for i in range(3)]
    else:
        mass = [sum(a * r[i] for a, r in zip(w, R)) for i in range(3)]
    best = max(range(3), key=mass.__getitem__)
    col = R[:, best] if HAVE_NP else [r[best] for r in R]
    return EquityInfo(col, w, cur, n, keep=best, keeps=[m / tot for m in mass])


def _equity_plain(street, mine, board, dead, n):
    # no numpy: uniform range and scalar sampling with one tenth of the samples
    rng = random.Random()
    live = [c for c in range(52) if c not in dead]
    n = max(20, n // 10)
    rows, cur = [], []
    for _ in range(n):
        if street == "flop":
            d = rng.sample(live, 5)
            ks = keep_scores([d[:3]], board)[0]
            j = ks.index(max(ks))
            b = list(board) + d[3:]
            o = eval_one([d[(j + 1) % 3], d[(j + 2) % 3]] + b)
            rows.append([(m > o) + 0.5 * (m == o) for m in
                         (eval_one([mine[(i + 1) % 3], mine[(i + 2) % 3]] + b) for i in range(3))])
            cur.append(max(ks))
        else:
            d = rng.sample(live, 3 if street == "turn" else 2)
            b = list(board) + d[2:]
            o = eval_one(d[:2] + b)
            m = eval_one(list(mine) + b)
            rows.append([(m > o) + 0.5 * (m == o)])
            cur.append(eval_one(d[:2] + list(board)))
    w = [1.0] * n
    if street == "flop":
        return _finish_flop(rows, w, cur, n)
    return EquityInfo([r[0] for r in rows], w, cur, n)


def equity_flop(my3, flop, rm=None, budget=None, n=None, rng=None):
    """Best keep on the flop against the weighted range; keep is the index to discard."""
    rm = rm or RangeModel()
    n = PARAMS["eq_flop_samples"] if n is None else n
    if not HAVE_NP:
        return _equity_plain("flop", my3, flop, set(my3) | set(flop), n)
    rng = _RNG if rng is None else rng
    dead = set(my3) | set(flop)
    live = np.array([c for c in range(52) if c not in dead], dtype=np.int64)
    deadline = None if budget is None else time.perf_counter() + budget
    opps, ress, keeps = [], [], []
    used = 0
    while used < n:
        m = min(PARAMS["eq_batch"], n - used)
        opp, res, ks = _flop_sim(my3, flop, live, m, rm.beta, rng)
        opps.append(opp)
        ress.append(res)
        keeps.append(ks)
        used += m
        if deadline is not None and used >= PARAMS["eq_min_samples"] \
                and time.perf_counter() >= deadline:
            break
    O = np.concatenate(opps)
    R = np.concatenate(ress)
    w, cur = rm.weights(O, flop, known_keeps=np.concatenate(keeps))
    return _finish_flop(R, w, cur, used)


def _pair_table(my2, board, rm):
    dead = set(my2) | set(board) | rm.dead
    live = np.array([c for c in range(52) if c not in dead], dtype=np.int64)
    i, j = np.triu_indices(len(live), 1)
    pair = np.stack([live[i], live[j]], axis=1)
    if rm.opp_discard is not None:
        pair = np.concatenate([pair, np.full((len(pair), 1), rm.opp_discard, dtype=np.int64)],
                              axis=1)
    return live, i, j, pair


def _rows(cards, n):
    return np.broadcast_to(np.asarray(list(cards), dtype=np.int64), (n, len(cards)))


def equity_turn(my2, board4, rm=None, budget=None, epochs=None, rng=None):
    """Equity on the turn: every opponent pair once per epoch, each with a fresh river."""
    rm = rm or RangeModel()
    if not HAVE_NP:
        return _equity_plain("turn", my2, board4, set(my2) | set(board4) | rm.dead,
                             PARAMS["eq_flop_samples"])
    rng = _RNG if rng is None else rng
    epochs = PARAMS["eq_turn_epochs"] if epochs is None else epochs
    live, i, j, T = _pair_table(my2, board4, rm)
    p = len(T)
    w, cur = rm.weights(T, board4[:3], turn=board4[3])
    mine_by_river = eval_batch(np.concatenate([
        _rows(list(my2) + list(board4), len(live)), live[:, None],
    ], axis=1))
    opp_base = np.concatenate([T[:, :2], _rows(board4, p)], axis=1)
    deadline = None if budget is None else time.perf_counter() + budget
    total = np.zeros(p)
    done = 0
    while done < epochs:
        r = rng.integers(0, len(live) - 2, size=p)
        idx = r + (r >= i)
        idx = idx + (idx >= j)
        river = live[idx][:, None]
        mine = mine_by_river[idx]
        opp = eval_batch(np.concatenate([opp_base, river], axis=1))
        total += (mine > opp) + 0.5 * (mine == opp)
        done += 1
        if deadline is not None and time.perf_counter() >= deadline:
            break
    return EquityInfo(total / done, w, cur, p * done)


def equity_river(my2, board5, rm=None):
    """Exact equity on the river over every live opponent pair."""
    rm = rm or RangeModel()
    if not HAVE_NP:
        return _equity_plain("river", my2, board5, set(my2) | set(board5) | rm.dead,
                             PARAMS["eq_flop_samples"])
    live, i, j, T = _pair_table(my2, board5, rm)
    p = len(T)
    w, cur = rm.weights(T, board5[:3], turn=board5[3], river=board5[4])
    mine = eval_one(list(my2) + list(board5))
    res = (mine > cur) + 0.5 * (mine == cur)
    return EquityInfo(res, w, cur, p)


# ---- betting policy

def _act(kind, amount=None):
    out = {"type": "action", "action": kind}
    if amount is not None:
        out["amount"] = int(amount)
    return out


def _raise_range(req):
    lo = as_int(req.get("min_raise"))
    hi = as_int(req.get("max_raise"), lo)
    return lo, max(lo, hi)


def decide_preflop(req, hole, opp=None, rng=random):
    """Table-driven preflop play from the embedded class equities."""
    opp = opp or STATE.opp
    legal = req.get("legal_actions") or []
    mb = as_int(req.get("my_bet"))
    ob = as_int(req.get("opp_bet"))
    c = as_int(req.get("to_call"))
    pot = max(1, as_int(req.get("pot"), mb + ob))
    my_stack = as_int(req.get("my_stack"))
    opp_stack = as_int(req.get("opp_stack"))
    seat = STATE.hand.seat if STATE.hand is not None else "button"
    start = STATE.stack
    can_raise = "raise" in legal
    cls = class_of(hole)
    pct = PF_PCT[cls] if cls >= 0 else 0.5
    parsed = parse_history(req.get("history"), seat, start)
    k = parsed.raises - 1
    if ob > 2 and k < 1:
        k = 1

    if c <= 0:
        if can_raise and pct >= PARAMS["pf_iso_cut"]:
            return _act("raise", PARAMS["pf_iso_size"])
        return _act("check")

    if k == 0:
        # Key 1 covers the big blind facing our first raise, after the open.
        jam_rate = opp.pf_jam_rate(1)
        if seat == "button" and jam_rate >= PARAMS["pf_shove_rate"]:
            jam = max(0, start - PARAMS["pf_open_size"])
            need = jam / float(2 * start) + PARAMS["pf_shove_margin"]
            eq = pf_equity_vs_range(cls, jam_rate) if cls >= 0 else 0.4
            if eq <= need:
                return _act("fold")
        steal = PARAMS["pf_steal_slope"] * max(0.0, opp.pf_fold_to_raise() - PARAMS["pf_steal_base"])
        if can_raise and pct >= max(0.0, PARAMS["pf_open_cut"] - steal):
            loose = opp.pf_fold_to_raise() < PARAMS["pf_loose_fold"]
            return _act("raise", PARAMS["pf_open_size_loose" if loose else "pf_open_size"])
        if pct >= PARAMS["pf_limp_cut"]:
            return _act("call")
        return _act("fold")

    prev_raises = k - 1
    key = 4 if (prev_raises == 0 and seat == "button") else min(prev_raises, 3)
    big = ob >= PARAMS["pf_big_frac"] * start or opp_stack <= 0
    p = opp.pf_range(key, big, ob)
    eq = pf_equity_vs_range(cls, p) if cls >= 0 else 0.4
    odds = c / float(pot + c)
    if big:
        margin = PARAMS["pf_big_margin"]
        if p >= 0.9 or opp.static_kind() == "raise":
            margin = PARAMS["pf_shove_margin"]
    else:
        margin = PARAMS["pf_call_margin"] + (PARAMS["pf_oop_margin"] if seat == "big_blind" else 0.0)

    if can_raise:
        if big and eq >= PARAMS["pf_jam_eq"]:
            return _act("raise", as_int(req.get("max_raise")))
        if not big and eq >= PARAMS["pf_value_eq"] and rng.random() < PARAMS["pf_value_freq"]:
            if prev_raises == 0:
                return _act("raise", ob * PARAMS["pf_raise_mult"])
            return _act("raise", as_int(req.get("max_raise")))
        has_ace = any((x >> 2) == 12 for x in hole)
        if (not big and prev_raises == 0 and has_ace and eq < odds + margin + 0.05
                and opp.pf_fold_to_raise() > PARAMS["pf_bluff_fold"]
                and rng.random() < PARAMS["pf_bluff_freq"]):
            return _act("raise", ob * PARAMS["pf_raise_mult"])
    if eq > odds + margin:
        return _act("call")
    return _act("fold")


def _realization(req, street, ip):
    c = as_int(req.get("to_call"))
    if street == "river" or as_int(req.get("my_stack")) <= c or as_int(req.get("opp_stack")) <= 0:
        return 1.0
    return PARAMS["real_ip" if ip else "real_oop"].get(street, 1.0)


def _dry_board(board):
    ranks = sorted(c >> 2 for c in board[:3])
    suits = [c & 3 for c in board[:3]]
    return len(set(suits)) == 3 and len(set(ranks)) == 3 and ranks[-1] - ranks[0] >= 5


def _call_tax(street, P, c, opp):
    """Equity discount on big flop and turn calls: such raises are stronger than the range model says."""
    if street == "river" or c < PARAMS["big_call_min"] or c < PARAMS["big_call_odds"] * (P + c):
        return 0.0
    agg = opp.aggression()
    return PARAMS["big_call_tax"] if agg is None or agg <= PARAMS["mdf_aggr"] else 0.0


def decide(req, info, opp=None, rng=random):
    """Pick the highest-EV action (chips relative to folding now) from an equity summary."""
    opp = opp or STATE.opp
    legal = req.get("legal_actions") or []
    street = req.get("street")
    P = max(1, as_int(req.get("pot")))
    c = as_int(req.get("to_call"))
    mb = as_int(req.get("my_bet"))
    ob = as_int(req.get("opp_bet"))
    my_stack = as_int(req.get("my_stack"))
    opp_stack = as_int(req.get("opp_stack"))
    left = as_int(req.get("raises_left"), 1)
    hand = STATE.hand
    ip = hand is None or hand.seat == "button"
    R = _realization(req, street, ip)
    e = info.e_all

    # Facing a raise over our own bet, discount our equity on the continue lines. A rare
    # raiser is a strong raiser, and a big raise is a strong raise; a small raise from a
    # frequent raiser (polarized or merged) is left alone. Never applied to a check.
    rtax = 0.0
    if c > 0 and mb > 0:
        hi, lo = PARAMS["raise_sel_hi"], PARAMS["raise_sel_lo"]
        sel = min(1.0, max(0.0, (hi - opp.reraise_prob()) / (hi - lo)))
        # Size by the raise fraction (added/pot-before), the same measure the size
        # buckets were cut on, so a half-pot raise scores the way it was studied.
        ofrac = c / float(P)
        try:
            ph = parse_history(req.get("history"),
                               hand.seat if hand is not None else "button", STATE.stack)
            for a in reversed(ph.actions):
                if a["actor"] == "opp" and a["is_raise"] and not a["is_bet"] \
                        and a["street"] == street:
                    ofrac = a["frac"]
                    break
        except Exception:
            ofrac = c / float(P)
        slo, shi = PARAMS["raise_size_lo"], PARAMS["raise_size_hi"]
        sizef = min(1.0, max(0.0, (ofrac - slo) / (shi - slo)))
        rtax = PARAMS["raise_tax"] * sel * sizef

    evs = {}
    if "fold" in legal:
        evs[("fold", 0)] = 0.0
    if "check" in legal:
        evs[("check", 0)] = R * e * P
    if "call" in legal:
        evs[("call", 0)] = R * (e - _call_tax(street, P, c, opp) - rtax) * (P + c) - c
    raise_to = []
    if "raise" in legal:
        lo, hi = _raise_range(req)
        targets = set()
        for frac in PARAMS["bet_sizes"]:
            targets.add(max(lo, min(hi, int(round(ob + frac * (P + c))))))
        if min(my_stack, opp_stack + c) <= PARAMS["max_shove_spr"] * (P + c):
            targets.add(hi)
        for to in sorted(targets):
            a = to - mb
            if a <= 0:
                continue
            d = max(0, min(to - ob, opp_stack))
            ratio = a / float(P)
            f = opp.fold_prob(street, ratio, 0 if c <= 0 else (2 if mb > 0 else 1))
            e_c = info.e_vs_continue(1.0 - f) - rtax
            q = P + a + d
            show = R * e_c * q - a
            rr = opp.reraise_prob() if (left > 1 and opp_stack - d > 0 and my_stack - a > 0) \
                else 0.0
            if rr > 0:
                y = min(my_stack - a, opp_stack - d, q)
                e_rr = info.e_vs_continue(max(0.02, (1.0 - f) * PARAMS["rr_range"])) - rtax
                hit = max(-a, R * e_rr * (q + 2 * y) - a - y)
                show = (1.0 - rr) * show + rr * hit
            evs[("raise", to)] = f * P + (1.0 - f) * show
            raise_to.append(to)

    if not evs:
        return fallback_action(req)
    best = max(evs.values())
    eps = PARAMS["mix_eps"] * P
    pick = max(evs, key=evs.get)

    allin_to = max(raise_to) if raise_to else None
    spr = min(my_stack, opp_stack + c) / float(P)
    passive = [v for k_, v in evs.items() if k_[0] in ("check", "call", "fold")]
    if (allin_to is not None and spr < PARAMS["spr_shove"] and evs[("raise", allin_to)] > 0
            and evs[("raise", allin_to)] >= max(passive or [0.0]) - 0.05 * P):
        pick = ("raise", allin_to)
    elif pick[0] != "fold":
        near = [k_ for k_, v in evs.items() if k_[0] != "fold" and v >= best - eps]
        if len(near) > 1:
            ws = [math.exp(-(best - evs[k_]) / (0.5 * eps)) for k_ in near]
            r = rng.random() * sum(ws)
            for k_, w in zip(near, ws):
                r -= w
                if r <= 0:
                    pick = k_
                    break

    if c > 0 and "call" in legal and opp.static_kind() == "raise":
        # he raises whatever he holds, so only our equity against a random hand matters
        need = c / float(P + c) + PARAMS["static_margin"]
        keep_raise = (pick[0] == "raise" and evs[pick] > 0
                      and evs[pick] >= evs.get(("call", 0), 0.0))
        if not keep_raise:
            pick = ("call", 0) if e > need else ("fold", 0)
    elif pick[0] == "fold" and "call" in legal:
        agg = opp.aggression()
        if agg is not None and agg > PARAMS["mdf_aggr"] \
                and e > c / float(P + c) - PARAMS["mdf_slack"]:
            pick = ("call", 0)

    if pick[0] != "raise" and street == "flop" and c == 0 and raise_to and hand is not None:
        pick = _cbet_floor(req, evs, raise_to, pick, opp, P, rng)

    return _act(pick[0], pick[1] if pick[0] == "raise" else None)


def _cbet_floor(req, evs, raise_to, pick, opp, P, rng):
    """Keep a minimum continuation-bet rate as the preflop aggressor on dry flops."""
    board = [parse_card(x) for x in (req.get("board") or [])[:3]]
    if len(board) < 3 or not _dry_board(board):
        return pick
    parsed = parse_history(req.get("history"), STATE.hand.seat, STATE.stack)
    last = [a for a in parsed.actions if a["street"] == "preflop" and a["is_raise"]]
    if not last or last[-1]["actor"] != "me":
        return pick
    to = min(raise_to)
    ratio = (to - as_int(req.get("my_bet"))) / float(P)
    if opp.fold_prob("flop", ratio, False) < PARAMS["cbet_fold_min"]:
        return pick
    if evs[("raise", to)] < -PARAMS["cbet_tol"] * P:
        return pick
    if rng.random() < PARAMS["cbet_freq"]:
        return ("raise", to)
    return pick


def street_equity(req, hand, hole, board):
    """Equity summary for the current street against the weighted opponent range."""
    street = req["street"]
    rm = RangeModel.from_hand(req.get("history"), hand, STATE.stack, **STATE.opp.range_args())
    budget = STATE.clock.budget(street)
    if street == "flop":
        if len(hole) != 3:
            raise ValueError("flop needs three cards")
        if budget <= 0.0:
            return equity_flop(hole, board, rm, n=200)
        return equity_flop(hole, board, rm, budget=budget)
    if len(hole) != 2:
        raise ValueError("turn and river need two cards")
    if street == "turn":
        if budget <= 0.0:
            return equity_turn(hole, board, rm, epochs=1)
        return equity_turn(hole, board, rm, budget=budget)
    return equity_river(hole, board, rm)


def range_action(req):
    hand = STATE.hand
    street = req.get("street")
    if hand is None or street not in STREETS:
        return fallback_action(req)
    hole = [parse_card(x) for x in hand.hole]
    if street == "preflop":
        if len(hole) != 3:
            return fallback_action(req)
        return decide_preflop(req, hole)
    board = [parse_card(x) for x in (req.get("board") or [])]
    if len(board) != {"flop": 3, "turn": 4, "river": 5}[street]:
        return fallback_action(req)
    if len(set(hole) | set(board)) != len(hole) + len(board):
        return fallback_action(req)
    info = street_equity(req, hand, hole, board)
    return decide(req, info)
