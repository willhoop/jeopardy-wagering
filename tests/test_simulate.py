"""Tests for engine/simulate.py."""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import simulate  # noqa: E402


def test_wins_hand_derived():
    # Tie for first goes to a tiebreaker: a two-way tie is half a win.
    assert simulate.wins([100, 100], 0) == 0.5
    # Player 0 (50) strictly behind player 1 (100) -> not a win.
    assert simulate.wins([50, 100], 0) == 0.0
    # Player 0 strictly ahead of both others -> win.
    assert simulate.wins([300, 100, 200], 0) == 1.0
    # Solo game -- always a win.
    assert simulate.wins([1], 0) == 1.0


def test_remaining_regular_clues_deterministic_with_seed():
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    clue_values = [200, 400, 600, 800, 1000]
    result1 = simulate.simulate_remaining_regular_clues([0, 0, 0], clue_values, rng=rng1)
    result2 = simulate.simulate_remaining_regular_clues([0, 0, 0], clue_values, rng=rng2)
    assert result1 == result2


def test_remaining_regular_clues_conserves_or_adds_value_only():
    # Every clue either adds its value to exactly one player or changes
    # nothing -- total score can only go up, never down, since these are
    # regular (non-Daily-Double) clues in this simplified model.
    rng = random.Random(1)
    clue_values = [200, 400, 600]
    start = [1000, 1000, 1000]
    result = simulate.simulate_remaining_regular_clues(start, clue_values, rng=rng)
    assert sum(result) >= sum(start)
    assert sum(result) <= sum(start) + sum(clue_values)


def test_simulate_final_jeopardy_lockout_player_does_not_wager():
    # Player 0 has 12000, player 1 has 5000 -- a Tier 1 lockout (12000 > 2*5000).
    # Regardless of fj_confidence, player 0's wager should be 0, so their
    # score is unchanged whether "correct" or not.
    rng_correct = random.Random(1)
    result_correct = simulate.simulate_final_jeopardy([12000, 5000], 0, fj_confidence=1.0, rng=rng_correct)
    rng_wrong = random.Random(1)
    result_wrong = simulate.simulate_final_jeopardy([12000, 5000], 0, fj_confidence=0.0, rng=rng_wrong)
    assert result_correct[0] == 12000
    assert result_wrong[0] == 12000


def test_simulate_final_jeopardy_cover_bet_player_wagers_and_can_lose():
    # Player 0 has 9000, player 1 has 5000 -- Tier 1 cover wager is 1001.
    # With fj_confidence=0.0 (guaranteed wrong), player 0 should drop by 1001.
    rng = random.Random(2)
    result = simulate.simulate_final_jeopardy([9000, 5000], 0, fj_confidence=0.0, rng=rng)
    assert result[0] == 9000 - 1001
