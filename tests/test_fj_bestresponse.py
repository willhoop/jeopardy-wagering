"""Tests for engine/fj_bestresponse.py.

Expected values are derived by hand (shown in comments) using a small,
explicit opponent model and independent outcomes (correlation 0), so the
tests do not depend on the shipped behavior defaults.

Hand derivation used throughout this file:
  Self score 9000, one opponent score 5000.
  Opponent wager distribution: bets $0 with probability 0.5 (score stays
  5000), bets everything ($5000) with probability 0.5, correct with
  probability 0.5.
  => Opponent's final-score distribution: 5000 (p=0.5), 10000 (p=0.25),
     0 (p=0.25).
  Self wagers w and is correct with probability 0.5:
    final = 9000 + w (correct) or 9000 - w (incorrect), each p=0.5.
  Tie rule (since November 2014): a tie for first goes to a tiebreaker, so
  a two-way tie is worth 0.5 of a win. Nobody wins at $0.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import fj_bestresponse as br  # noqa: E402

OPP_DIST = [(0, 0.5), (5000, 0.5)]


def fixed_model(scores, opponent_index):
    return OPP_DIST


def test_hand_derived_win_probability_no_wager():
    # w=0: self final is always 9000.
    # Beats 5000 (p .5) and 0 (p .25); loses to 10000 (p .25). = 0.75.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p = br.expected_win_probability(self_score=9000, self_wager=0, p_self_correct=0.5, opponents=[opp])
    assert abs(p - 0.75) < 1e-9


def test_hand_derived_win_probability_cover_bet():
    # w=1001: correct (p .5) -> 10001 beats every outcome -> 1.0.
    #         incorrect (p .5) -> 7999, loses only to 10000 -> 0.75.
    # Total = 0.5*1.0 + 0.5*0.75 = 0.875.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p = br.expected_win_probability(self_score=9000, self_wager=1001, p_self_correct=0.5, opponents=[opp])
    assert abs(p - 0.875) < 1e-9


def test_overbetting_is_worse_than_exact_cover():
    # w=9000: correct -> 18000 -> 1.0. incorrect -> 0, which at best ties the
    # opponent's 0 outcome; nobody wins at $0 -> 0.
    # Total = 0.5*1.0 + 0.5*0 = 0.5.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    p_cover = br.expected_win_probability(9000, 1001, 0.5, [opp])
    p_everything = br.expected_win_probability(9000, 9000, 0.5, [opp])
    assert abs(p_everything - 0.5) < 1e-9
    assert p_everything < p_cover


def test_tie_bet_is_worth_less_than_cover_bet():
    # The user's question: is betting to tie ever free? Under the tiebreaker
    # rule, no. w=1000: correct -> 10000: beats 5000 (.5) and 0 (.25), ties
    # 10000 (.25 * 0.5 = .125) -> .875. incorrect -> 8000 -> .75.
    # Total = 0.5*.875 + 0.5*.75 = 0.8125, below the cover bet's 0.875.
    opp = br.OpponentModel(score=5000, wager_dist=OPP_DIST, p_correct=0.5)
    assert abs(br.expected_win_probability(9000, 1000, 0.5, [opp]) - 0.8125) < 1e-9
    rec = br.analyze([9000, 5000], 0, 0.5, opponent_model_fn=fixed_model,
                     opponent_correctness=0.5, correlation=0.0)
    assert rec.recommended_wager == 1001
    assert abs(rec.win_probability - 0.875) < 1e-9


def test_exact_ceiling_tie_is_settled_by_tiebreaker():
    # Self 10000, opponent 5000 (ceiling exactly 10000), self wagers 0.
    # Self loses nothing except when the opponent lands on 10000, which is a
    # tie worth 0.5. If q = P(opponent bets all and is right), the win share
    # is 1 - q/2. Dist below: q = 0.2 * 0.5 = 0.1 -> 0.95.
    opp = br.OpponentModel(score=5000, wager_dist=[(0, 0.5), (2500, 0.3), (5000, 0.2)], p_correct=0.5)
    assert abs(br.expected_win_probability(10000, 0, 0.5, [opp]) - 0.95) < 1e-9
    # q = 1.0 * 0.9 = 0.9 -> 0.55.
    opp = br.OpponentModel(score=5000, wager_dist=[(5000, 1.0)], p_correct=0.9)
    assert abs(br.expected_win_probability(10000, 0, 0.5, [opp]) - 0.55) < 1e-9


def test_correlation_changes_the_answer_in_the_expected_direction():
    # One opponent who always bets everything. With positive correlation,
    # "I am wrong" makes "they are right" less likely, so the wrong-answer
    # branch gets better and the win share rises for a cover bet.
    opp = br.OpponentModel(score=5000, wager_dist=[(5000, 1.0)], p_correct=0.5)
    independent = br.expected_win_probability(9000, 1001, 0.5, [opp], correlation=0.0)
    correlated = br.expected_win_probability(9000, 1001, 0.5, [opp], correlation=0.3)
    # Hand check, independent: correct -> 1.0; wrong (7999) beats only the
    # opponent's 0 outcome (p .5) -> 0.5*1 + 0.5*0.5 = 0.75.
    assert abs(independent - 0.75) < 1e-9
    # Correlated: wrong branch wins when the opponent is also wrong.
    # P(both wrong) = 0.25 + 0.3*0.25 = 0.325 (binary correlation 0.3).
    # Total = 0.5 + 0.325 = 0.825.
    assert abs(correlated - 0.825) < 1e-4


def test_solo_game_always_wins():
    rec = br.analyze([8000], player_index=0, p_self_correct=0.3)
    assert rec.win_probability == 1.0


def test_third_place_can_win_when_both_leaders_bust():
    # Self 4000 (third), A=9000, B=10000, self 100% sure, independent
    # outcomes, explicit opponent dists:
    #   A: {0, 9000} each .5 -> finals 9000 (.5), 18000 (.25), 0 (.25).
    #   B: {0, 8001, 10000} each 1/3 -> finals 10000 (1/3), 18001 (1/6),
    #      1999 (1/6), 20000 (1/6), 0 (1/6).
    # Any self wager 0..4000 lands on 4000..8000. No opponent outcome lies
    # in that range, so self wins only when both bust:
    #   P(A = 0) = .25, P(B <= 1999) = 1/3 -> 1/12. Smallest wager: 0.
    dists = {1: [(0, 0.5), (9000, 0.5)], 2: [(0, 1 / 3), (8001, 1 / 3), (10000, 1 / 3)]}
    rec = br.analyze([4000, 9000, 10000], 0, 1.0, opponent_model_fn=lambda s, i: dists[i],
                     opponent_correctness=0.5, correlation=0.0)
    assert abs(rec.win_probability - (1 / 12)) < 1e-9
    assert rec.recommended_wager == 0


def test_shipped_defaults_never_recommend_a_tie_only_cover():
    # Regression for the reported case: leader whose cover is 2B-A+1. Under
    # the old "tie = win" rule Tier 2 picked 2B-A (a tie if B doubles).
    # With the tiebreaker rule the extra $1 turns that tie into a win.
    for scores, p in (([10000, 8000, 3400], 0.89), ([12000, 9000, 3000], 0.89)):
        rec = br.analyze(scores, 0, p)
        tie_bet = 2 * scores[1] - scores[0]
        assert rec.recommended_wager != tie_bet, (scores, rec.recommended_wager)
