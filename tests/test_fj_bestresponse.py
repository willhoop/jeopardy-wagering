"""Tests for engine/fj_bestresponse.py.

Where possible, expected values are derived by hand (shown in comments)
using a small, explicit opponent model -- not the module's illustrative
default -- so the test is independent of whatever default placeholder
numbers the module ships with.

Hand derivation used throughout this file:
  Self score 9000, one opponent score 5000.
  Opponent wager distribution: bets $0 with probability 0.5 (score stays
  5000), bets everything ($5000) with probability 0.5, and if betting
  everything is correct with probability 0.5.
  => Opponent's final-score distribution: 5000 (p=0.5), 10000 (p=0.25),
     0 (p=0.25).
  Self wagers w and is correct with probability 0.5:
    final = 9000 + w (correct) or 9000 - w (incorrect), each p=0.5.
  Win (tie counts as win) when self final >= opponent final.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import fj_bestresponse as br  # noqa: E402

OPP_DIST = [(0, 0.5), (5000, 0.5)]


def test_hand_derived_win_probability_no_wager():
    # w=0: self final is always 9000.
    # Beats opponent final of 5000 (p .5) and 0 (p .25); loses to 10000 (p .25).
    # Win probability = 0.5 + 0.25 = 0.75.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p = br.expected_win_probability(self_score=9000, self_wager=0, p_self_correct=0.5, opponents=[opp])
    assert abs(p - 0.75) < 1e-9


def test_hand_derived_win_probability_cover_bet():
    # w=1001 (Tier 1 cover bet: 2*5000 - 9000 + 1 = 1001):
    #   correct (p .5) -> 10001, beats all three opponent outcomes -> win prob 1.0 in this branch
    #   incorrect (p .5) -> 7999, beats 5000 and 0, loses to 10000 -> win prob 0.75 in this branch
    # Total = 0.5*1.0 + 0.5*0.75 = 0.875
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p = br.expected_win_probability(self_score=9000, self_wager=1001, p_self_correct=0.5, opponents=[opp])
    assert abs(p - 0.875) < 1e-9


def test_overbetting_is_worse_than_exact_cover():
    # Betting everything (9000): incorrect branch (p .5) drops to 0, which
    # only beats the opponent's own 0 outcome (p .25) -- worse downside than
    # the cover bet's 7999, with no extra upside beyond the cover bet's
    # already-guaranteed win when correct. Hand check: 0.5*1.0 + 0.5*0.25 = 0.625.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p_cover = br.expected_win_probability(9000, 1001, 0.5, [opp])
    p_everything = br.expected_win_probability(9000, 9000, 0.5, [opp])
    assert abs(p_everything - 0.625) < 1e-9
    assert p_everything < p_cover


def test_analyze_prefers_strict_win_over_gratuitous_tie():
    # CHANGED 2026-07-23: this test previously asserted the *opposite*
    # conclusion -- that wager=1000 (a tie) should be preferred over 1001
    # (a strict win) because both scored the same 0.875 win probability.
    # That was a real defect, caught by Will pointing out that a wager
    # settling for a tie "is dumb" when a strictly better wager is
    # available at zero extra cost in expectation. Tier 2 now uses strict
    # win probability as a secondary objective: among wagers tied on
    # tie-inclusive win probability, prefer whichever wins outright more
    # often, then the smallest wager.
    #
    # Hand check, same opponent model as above (self=9000, opp=5000):
    #   w=1000: correct -> 10000 (ties the opponent's 10000 branch, not a
    #     strict win); strict-win contribution in that branch = 0.75 (wins
    #     vs 5000 and 0, ties vs 10000). incorrect -> 8000, strict = 0.75.
    #     Total strict = 0.5*0.75 + 0.5*0.75 = 0.75.
    #   w=1001: correct -> 10001 (beats all three opponent outcomes
    #     outright); strict = 1.0 in that branch. incorrect -> 7999, same
    #     bucket as before, strict = 0.75. Total strict = 0.5*1.0 + 0.5*0.75
    #     = 0.875.
    # Both wagers tie on win probability (0.875, tie-inclusive), but 1001
    # has the higher strict-win probability, so it's preferred.
    def fixed_model(scores, opponent_index):
        return OPP_DIST

    rec = br.analyze(
        [9000, 5000],
        player_index=0,
        p_self_correct=0.5,
        opponent_model_fn=fixed_model,
        opponent_correctness=0.5,
    )
    assert rec.recommended_wager == 1001
    assert abs(rec.win_probability - 0.875) < 1e-9
    assert rec.tier1_cover_wager == 1001  # Tier 1 already targeted the strict win here


def test_exact_ceiling_boundary_guarantees_win_regardless_of_opponent_model():
    # When self score exactly equals the opponent's worst-case ceiling
    # (2 * opponent score), wagering 0 must guarantee a win (tie counts as a
    # win) no matter the opponent's wager distribution or correctness --
    # the opponent's own final score can never exceed that ceiling. This
    # holds for ANY opponent model, so it's a strong cross-check on the
    # exact-expectation math, not just one hand-picked scenario.
    self_score = 10000
    opp_score = 5000  # ceiling = 2 * 5000 = 10000, exactly matches self_score
    distributions = [
        [(0, 1.0)],
        [(5000, 1.0)],
        [(0, 0.5), (2500, 0.3), (5000, 0.2)],
    ]
    for dist in distributions:
        for p_correct in (0.1, 0.5, 0.9):
            opp = br.OpponentModel(score=opp_score, wager_dist=dist, p_correct=p_correct)
            p = br.expected_win_probability(self_score, 0, 0.5, [opp])
            assert abs(p - 1.0) < 1e-9, (dist, p_correct, p)


def test_default_opponent_model_matches_hand_derived_case():
    # For scores [9000, 5000], the opponent's (index 1) own Tier 1 analysis
    # has no cover wager (can't catch a potential 18000 ceiling) and no
    # lock-tie, so the default model's candidate set collapses to exactly
    # {0, 5000} with equal weight -- identical to OPP_DIST used above.
    dist = br.default_opponent_wager_model([9000, 5000], opponent_index=1)
    assert sorted(dist) == sorted(OPP_DIST)


def test_solo_game_always_wins():
    rec = br.analyze([8000], player_index=0, p_self_correct=0.3)
    assert rec.win_probability == 1.0


def test_third_place_can_win_when_both_leaders_bust():
    # Reproduces Will's exact reported scenario: self=4000 (3rd place),
    # A=9000, B=10000, 100% self-confidence, default opponent model. He
    # asked for the model to make sure it accounts for the case where he
    # wins because *both* leaders bet big and miss. This test proves the
    # math already does exactly that, using the module's own shipped
    # default opponent model -- not a hand-picked one -- so it checks the
    # real end-to-end behavior, not just the underlying arithmetic.
    #
    # Hand derivation (opponent_correctness=0.5, the module default, for both):
    #   A's own Tier 1 view (index 1, vs self=4000 and B=10000): B is the
    #     binding opponent (ceiling 20000); A can't cover it (required
    #     12001 > A's max wager 9000), and no lock-tie applies. Default
    #     model candidates: {0, 9000}, weight 0.5 each.
    #     => A's final-score distribution: 9000 (p=.5), 18000 (p=.25), 0 (p=.25).
    #   B's own Tier 1 view (index 2, vs self=4000 and A=9000): A is the
    #     binding opponent (ceiling 18000); B *can* cover it (required
    #     8001 <= B's max wager 10000), no lock-tie applies. Default model
    #     candidates: {0, 8001, 10000}, weight 1/3 each.
    #     => B's final-score distribution: 10000 (p=1/3), 18001 (p=1/6),
    #        1999 (p=1/6), 20000 (p=1/6), 0 (p=1/6).
    #   Self wagers $0 (see below for why), so self's final score is a
    #   fixed $4000. Self wins (tie-or-better) exactly when BOTH A and B
    #   land at or below $4000 -- i.e., both busted after betting big:
    #     P(A <= 4000) = P(A wagered 9000 and missed) = 0.25
    #     P(B <= 4000) = P(B landed at 1999 or 0) = 1/6 + 1/6 = 1/3
    #   Independent opponents, so P(self wins) = 0.25 * (1/3) = 1/12 (~8.3%),
    #   matching what the app displayed.
    #
    #   Why $0 and not the full $4000. self is 100% confident, so betting
    #   more is risk-free and only ever raises the final score -- but
    #   neither opponent has any possible outcome strictly between $4000
    #   and $8000 (the range reachable by wagering $0 to the $4000 max), so
    #   raising the wager doesn't cross any new threshold and cannot
    #   change the win probability. Every wager from $0 to $4000 therefore
    #   ties at 1/12, and the smallest-wager tiebreak picks $0. Betting
    #   more here would not be wrong, just not necessary.
    scores = [4000, 9000, 10000]
    rec = br.analyze(scores, player_index=0, p_self_correct=1.0, opponent_correctness=0.5)
    assert abs(rec.win_probability - (1 / 12)) < 1e-9
    assert rec.recommended_wager == 0
