"""Final Jeopardy rules, checked against the known game-theory results.

Two kinds of check:
1. Tier 1 against brute force: every legal wager and right/wrong outcome of
   every opponent, on small integer scores. Brute force needs no formula, so
   it checks the shut-out (cover) and lockout logic independently.
2. The standard rules, derived by hand: the leader's shut-out bet 2B - A + 1,
   the two-thirds limit 3B - 2A for second place (Dupee, 1998, as cited by
   Tesauro et al., 2013), and lockout A > 2B. Scored with the shipped
   tiebreaker rule (behavior.win_share).
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import behavior  # noqa: E402
import fj_wager  # noqa: E402


def reachable(score):
    """Every final score a player can reach: any legal wager, right or wrong."""
    if score <= 0:
        return {score}
    return {score + w for w in range(score + 1)} | {score - w for w in range(score + 1)}


def brute_force(scores, i):
    """(lockout, smallest wager that wins outright whenever right) by enumeration."""
    me = scores[i]
    others = [reachable(s) for j, s in enumerate(scores) if j != i]
    best_other = max(max(o) for o in others)
    if me > best_other:
        return True, 0
    for w in range(max(me, 0) + 1):
        if me + w > best_other:
            return False, w
    return False, None


def test_tier1_matches_brute_force_on_every_small_game():
    for k in (2, 3):
        for scores in itertools.product(range(-2, 13), repeat=k):
            for i in range(k):
                rec = fj_wager.analyze(list(scores), i)
                assert (rec.lockout, rec.min_wager_to_guarantee_win) == brute_force(list(scores), i), (scores, i)


def finals(scores, wagers, right):
    return [s + (w if r else -w) for s, w, r in zip(scores, wagers, right)]


def test_shut_out_bet_beats_every_second_place_outcome_when_right():
    # A = 10,000, B = 7,000. Shut-out bet 2B - A + 1 = 4,001.
    # A right: 14,001. B's best possible: 14,000. A wins outright for every B wager.
    a, b = 10000, 7000
    cover = 2 * b - a + 1
    assert cover == 4001
    for wb in range(0, b + 1, 50):
        for b_right in (True, False):
            assert behavior.win_share(finals([a, b], [cover, wb], [True, b_right]), 0) == 1.0
    # One dollar less (4,000) only ties B's all-in, which is half a win.
    assert behavior.win_share(finals([a, b], [cover - 1, b], [True, True]), 0) == 0.5


def test_two_thirds_rule():
    # A = 9,000, B = 6,600 (more than 2/3 of A).
    # A covers: 2B - A + 1 = 4,201. If A misses: 4,799.
    # B's two-thirds limit: 3B - 2A = 1,800. If B also misses with 1,800:
    # 4,800 > 4,799, so B still wins. One dollar more (1,801): 4,799, a tie.
    a, b = 9000, 6600
    cover = 2 * b - a + 1
    limit = 3 * b - 2 * a
    assert (cover, limit) == (4201, 1800)
    for b_right in (True, False):
        assert behavior.win_share(finals([a, b], [cover, limit], [False, b_right]), 1) == 1.0
    assert behavior.win_share(finals([a, b], [cover, limit + 1], [False, False]), 1) == 0.5
    # If A is right, the cover bet beats B whatever B does.
    assert behavior.win_share(finals([a, b], [cover, b], [True, True]), 0) == 1.0


def test_two_thirds_rule_needs_two_thirds():
    # Below 2/3 (A = 9,000, B = 5,900): 3B - 2A = -300 < 0, so no wager lets
    # B survive a miss when A covers and misses: A ends on 2A - 2B - 1 = 6,199
    # and B's $0 bet keeps only 5,900.
    a, b = 9000, 5900
    assert 3 * b - 2 * a < 0
    assert behavior.win_share(finals([a, b], [2 * b - a + 1, 0], [False, False]), 1) == 0.0


def test_lockout_and_exact_double():
    # A = 12,001 > 2 x 6,000: lockout, A wins at $0 whatever B does.
    assert fj_wager.analyze([12001, 6000], 0).lockout
    for wb in (0, 3000, 6000):
        for b_right in (True, False):
            assert behavior.win_share(finals([12001, 6000], [0, wb], [False, b_right]), 0) == 1.0
    # A = 12,000 = 2 x 6,000: not a lockout. B all-in and right ties A's $0
    # bet, which is a tiebreaker (half a win), not a win.
    assert not fj_wager.analyze([12000, 6000], 0).lockout
    assert behavior.win_share(finals([12000, 6000], [0, 6000], [False, True]), 0) == 0.5
