"""Tests for engine/fj_wager.py.

Expected values below are derived by hand from the classic Final Jeopardy
guarantee formula (wager >= 2 * opponent_score - own_score + 1 to beat that
opponent's worst case of betting everything and answering correctly), not
copied from the module's own output. Work is shown in each test's comment.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import fj_wager  # noqa: E402


def test_two_player_lockout():
    # A=12000, B=5000. B's worst case if betting everything and right: 10000.
    # 12000 > 10000, so A is in lockout and needs no wager.
    rec = fj_wager.analyze([12000, 5000], player_index=0)
    assert rec.lockout is True
    assert rec.min_wager_to_guarantee_win == 0


def test_two_player_cover_bet():
    # A=9000, B=5000. B's worst case: 2*5000 = 10000.
    # A needs 9000 + wager > 10000 -> wager > 1000 -> min integer wager 1001.
    rec = fj_wager.analyze([9000, 5000], player_index=0)
    assert rec.lockout is False
    assert rec.min_wager_to_guarantee_win == 1001
    assert rec.max_legal_wager == 9000


def test_two_player_exact_double_boundary():
    # A=10000, B=5000. B's worst case: 2*5000 = 10000, exactly equal to A.
    # A is NOT in lockout (a $0 wager only guarantees a tie, not sole first).
    # A needs 10000 + wager > 10000 -> wager > 0 -> min integer wager 1.
    rec = fj_wager.analyze([10000, 5000], player_index=0)
    assert rec.lockout is False
    assert rec.min_wager_to_guarantee_win == 1


def test_three_player_binding_constraint_is_largest_threat():
    # A=10000, B=6000, C=3000.
    # B's worst case: 12000. C's worst case: 6000. B is the binding threat.
    # A needs 10000 + wager > 12000 -> wager > 2000 -> min integer wager 2001.
    rec = fj_wager.analyze([10000, 6000, 3000], player_index=0)
    assert rec.lockout is False
    assert rec.binding_opponent_index == 1
    assert rec.min_wager_to_guarantee_win == 2001


def test_three_player_order_independence():
    # Same game as above, but scores listed in a different order and asking
    # for the same logical player (A, score 10000) now at list position 2.
    # Result must be identical: binding opponent is whichever index holds
    # 6000, and required wager is still 2001.
    scores = [6000, 3000, 10000]  # B, C, A
    rec = fj_wager.analyze(scores, player_index=2)
    assert rec.lockout is False
    assert rec.binding_opponent_index == 0  # index of the 6000 score
    assert rec.min_wager_to_guarantee_win == 2001


def test_lock_tie_scenario():
    # A=10000 (index 0), B=5000 (index 1), C=1000 (index 2).
    # From B's perspective: opponents are A (worst case 20000) and C (worst
    # case 2000). A is the binding threat. B cannot cover 20000 with a max
    # wager of 5000, so no outright-win wager exists.
    # Lock-tie check: is A already safe against C without wagering?
    # A's score (10000) > C's worst case (2000) -> yes, A has no reason to
    # wager. B's score is exactly half of A's (5000 * 2 == 10000), so B can
    # wager everything (5000) and, if correct, tie A at 10000.
    rec = fj_wager.analyze([10000, 5000, 1000], player_index=1)
    assert rec.lockout is False
    assert rec.min_wager_to_guarantee_win is None  # can't guarantee outright win
    assert rec.lock_tie_wager == 5000


def test_zero_score_cannot_wager():
    # A player with $0 has no legal wager and can't guarantee a win by
    # betting, regardless of opponents' scores.
    rec = fj_wager.analyze([0, 4000], player_index=0)
    assert rec.max_legal_wager == 0
    assert rec.lockout is False
    assert rec.min_wager_to_guarantee_win is None


def test_solo_game():
    # No opponents -- any wager preserves first place.
    rec = fj_wager.analyze([8000], player_index=0)
    assert rec.lockout is True
    assert rec.min_wager_to_guarantee_win == 0
    assert rec.opponent_scores == []


def test_analyze_all_returns_one_recommendation_per_player():
    recs = fj_wager.analyze_all([10000, 6000, 3000])
    assert len(recs) == 3
    assert [r.player_index for r in recs] == [0, 1, 2]
