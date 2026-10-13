"""Tests for engine/behavior.py. Expected values are derived by hand."""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import behavior  # noqa: E402


def as_dict(dist):
    return {w: p for w, p in dist}


def test_win_share_tiebreaker_rule():
    assert behavior.win_share([300, 100, 200], 0) == 1.0
    assert behavior.win_share([100, 100], 0) == 0.5       # two-way tie
    assert behavior.win_share([100, 100, 100], 2) == 1 / 3  # three-way tie
    assert behavior.win_share([100, 100, 50], 2) == 0.0
    assert behavior.win_share([0, 0, 0], 0) == 0.0        # nobody wins at $0
    assert behavior.win_share([0, -500], 0) == 0.0
    assert behavior.win_share([1], 0) == 1.0              # solo


def test_b_published_regime_weights():
    # Scores A=10000, B=8000, C=3000: B >= 3/4 A and B >= 2C, the regime
    # Tesauro et al. publish. Bets:
    #   bankroll 8000 (.26), keepout C: 8000-6000-1 = 1999 (.27),
    #   overtake A: 2001 (.15), two-thirds: 3*8000-2*10000-1 = 3999 (.08),
    #   random grid {0, 2000, 4000, 6000, 8000} at .24/5 = .048 each.
    d = as_dict(behavior.wager_distribution([10000, 8000, 3000], 1))
    expected = {8000: 0.308, 1999: 0.27, 2001: 0.15, 3999: 0.08,
                0: 0.048, 2000: 0.048, 4000: 0.048, 6000: 0.048}
    assert d.keys() == expected.keys()
    for w, p in expected.items():
        assert abs(d[w] - p) < 1e-12, w


def test_b_two_player_redistributes_missing_bet_types():
    # A=9000, B=5000, no C. keepout C and two-thirds (3B-2A < 0) do not
    # exist. Live weights: bankroll .26, overtake .15, random .24 = .65.
    #   5000: .26/.65 + .048/.65 = .4 + .073846 = .473846
    #   4001 (overtake): .15/.65 = .230769
    #   0, 1250, 2500, 3750: .048/.65 = .073846 each
    d = as_dict(behavior.wager_distribution([9000, 5000], 1))
    r = 0.048 / 0.65
    expected = {5000: 0.4 + r, 4001: 0.15 / 0.65, 0: r, 1250: r, 2500: r, 3750: r}
    assert d.keys() == expected.keys()
    for w, p in expected.items():
        assert abs(d[w] - p) < 1e-12, w


def test_a_cover_and_lockout():
    # A=10000, B=8000: cover 6001 (.75), tie 6000 (.10), all-in 10000 (.05),
    # grid {0, 2500, 5000, 7500, 10000} at .02 each.
    d = as_dict(behavior.wager_distribution([10000, 8000, 3000], 0))
    assert abs(d[6001] - 0.75) < 1e-12
    assert abs(d[6000] - 0.10) < 1e-12
    assert abs(d[10000] - 0.07) < 1e-12
    # Lockout A=20000 > 2*8000: 0 or 20000-16000-1 = 3999, half each.
    assert as_dict(behavior.wager_distribution([20000, 8000], 0)) == {0: 0.5, 3999: 0.5}


def test_c_is_state_independent_and_non_positive_scores_do_not_bet():
    assert as_dict(behavior.wager_distribution([10000, 8000, 4000], 2)) == {
        0: 0.2, 1000: 0.2, 2000: 0.2, 3000: 0.2, 4000: 0.2}
    assert behavior.wager_distribution([10000, 8000, -400], 2) == [(0, 1.0)]


def test_distributions_sum_to_one_and_stay_legal():
    rng = random.Random(7)
    for _ in range(300):
        scores = [rng.randrange(-20, 400) * 100 for _ in range(rng.choice([1, 2, 3]))]
        for i, s in enumerate(scores):
            d = behavior.wager_distribution(scores, i)
            assert abs(sum(p for _, p in d) - 1.0) < 1e-9
            assert all(0 <= w <= max(s, 0) for w, _ in d)


def test_quadrature_reproduces_published_correlation():
    # Two players at 50%. Binary correlation 0.3 means
    # P(both right) = 0.25 + 0.3 * 0.25 = 0.325 (Sheppard's formula gives
    # exactly this for r = sin(0.3 * pi / 2)).
    r = behavior.latent_correlation(0.3)
    both = sum(w * behavior.conditional_accuracy(0.5, f, r) ** 2 for f, w in behavior.quadrature_nodes())
    assert abs(both - 0.325) < 1e-4


def test_sampled_correlation_matches():
    rng = random.Random(11)
    r = behavior.latent_correlation(0.3)
    n = 40000
    both = sum(all(behavior.sample_correct([0.5, 0.5], r, rng)) for _ in range(n)) / n
    assert abs(both - 0.325) < 0.01  # 4 standard errors at n=40000


def test_inverse_normal_round_trip():
    for p in (0.01, 0.2, 0.5, 0.89, 0.999):
        assert abs(behavior.normal_cdf(behavior.inverse_normal_cdf(p)) - p) < 1e-12
