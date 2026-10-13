"""Simulated contestant behavior and the current tie rule.

This module is the one home for every number that describes how real
Jeopardy! contestants behave and how a game is scored. Tier 2
(engine/fj_bestresponse.py), the Daily Double rollouts (engine/simulate.py)
and the app's JavaScript port (app/index.html) all read from it.

Sources:
  [T13] Tesauro, Gondek, Lenchner, Fan & Prager (2013), "Analysis of
        Watson's Strategies for Playing Jeopardy!", JAIR 47:205-251,
        section 2.2 (Daily Double), section 2.3 (Final Jeopardy).
  [TB]  Jeopardy! tie rule, in force since the 24 November 2014 episode:
        a tie for first after Final Jeopardy is settled by a tiebreaker
        clue. Before that date, tied players both returned as co-champions.
        https://www.theringer.com/2021/01/23/tv/jeopardy-tiebreaker-scenario-rules-changes

Every value is marked CALIBRATED (fitted privately to modern-era data,
see ADR-0004), PUBLISHED (from a cited source) or ASSUMED (our choice).
See docs/adr/0003-simulated-contestant-behavior.md and
docs/adr/0004-modern-era-calibration.md.
"""

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

WagerDist = List[Tuple[int, float]]

# ---------------------------------------------------------------------------
# CONFIGURATION BLOCK -- every value that can change lives here.
# ---------------------------------------------------------------------------

# Tie rule [TB]. A tie for first goes to a tiebreaker clue. We give each
# tied player an equal chance, so a k-way tie is worth 1/k of a win.
# If every player finishes at $0 or less, nobody wins.
TIEBREAKER_RULE = True

# ERA. Contestant behavior changed sharply in the 2010s (Daily Double
# hunting, aggressive betting). Values marked CALIBRATED come from a private
# calibration on J! Archive season statistics for Seasons 38-41 (2021-2025).
# J! Archive's terms forbid republishing its data, so the source statistics
# are not kept in this repository and are not quoted in any document
# (ADR-0004). Values marked PUBLISHED [T13] describe 1990s-2012 play and are
# kept only where no modern calibration exists.

# Final Jeopardy accuracy by score rank entering FJ (leader, second, third).
# CALIBRATED.
FJ_ACCURACY_BY_RANK = (0.51, 0.46, 0.40)
# Average over all players. CALIBRATED. Used for the advised player's own
# Final Jeopardy inside Daily Double rollouts.
FJ_ACCURACY_OVERALL = 0.45
# Right/wrong outcomes are positively correlated across players. CALIBRATED
# as the pairwise correlation of the binary outcomes. We convert it to the
# latent normal correlation with Sheppard's formula, r = sin(rho * pi / 2),
# which is exact at 50% accuracy and close to it nearby.
FJ_OUTCOME_CORRELATION = 0.16

# Daily Double accuracy. CALIBRATED.
DD_ACCURACY = 0.65
# A future Daily Double's wager, as a fraction of the finder's score, by
# round. Round 2 uses the second Double Jeopardy! DD, because a DD still
# hidden after the current one is usually that one. CALIBRATED.
DD_WAGER_FRACTION_BY_ROUND = {1: 0.87, 2: 0.46}
# Who finds a future Daily Double, by score rank. CALIBRATED from finds by
# lectern; the returning champion's lectern stands in for the leader.
DD_FINDER_WEIGHTS_BY_RANK = (0.41, 0.30, 0.29)

# Second-place ("B") wager mix. PUBLISHED [T13 s2.3] for the regime
# B >= 3/4 A and B >= 2C, from 1990s-2012 games: no modern calibration
# exists, so this is the oldest part of the model. ASSUMED to hold in the
# other five regimes and in the modern era: when a
# bet type does not exist in a regime, its weight is shared out
# proportionally among the bet types that do.
B_WEIGHTS = {
    "bankroll": 0.26,    # bet everything
    "keepout_c": 0.27,   # stay above C's doubled score (or cover it)
    "overtake_a": 0.15,  # A - B + 1
    "two_thirds": 0.08,  # just below 3B - 2A
    "random": 0.24,      # spread over the random grid below
}

# Leader ("A") wager mix, not locked out. The share that covers second
# place (cover + cover_tie + bankroll, plus the covering part of "random")
# is CALIBRATED. The split between the bet types is ASSUMED.
A_WEIGHTS = {
    "cover": 0.80,       # 2B - A + 1
    "cover_tie": 0.04,   # 2B - A
    "bankroll": 0.04,
    "random": 0.12,
}
# Leader in a lockout (A > 2B). ASSUMED split.
A_LOCKOUT_WEIGHTS = {"zero": 0.5, "max_safe": 0.5}

# Third place ("C"). [T13 s2.3, note 5] PUBLISHED that C's wagers do not
# vary with the game state. The flat shape over the random grid is ASSUMED.
# The random grid: 0, 1/4, 1/2, 3/4 and all of the score.
RANDOM_GRID_QUARTERS = (0, 1, 2, 3, 4)

# Numerical integration over the shared "how hard was this clue" factor.
QUAD_HALF_WIDTH = 6.0
QUAD_STEP = 0.25

# ---------------------------------------------------------------------------


def latent_correlation(binary_correlation: float) -> float:
    """Latent normal correlation that gives `binary_correlation` at p = 0.5."""
    return math.sin(binary_correlation * math.pi / 2)


def normal_cdf(x: float) -> float:
    if x == math.inf:
        return 1.0
    if x == -math.inf:
        return 0.0
    return 0.5 * math.erfc(-x / math.sqrt(2))


def inverse_normal_cdf(p: float) -> float:
    if p <= 0:
        return -math.inf
    if p >= 1:
        return math.inf
    # Acklam's approximation, then one Halley step (the app uses the same).
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= 1 - pl:
        q = p - 0.5
        r = q * q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    e = normal_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


# --- Scoring ----------------------------------------------------------------

def win_share(final_scores: Sequence[int], player_index: int) -> float:
    """This player's share of a win under the tiebreaker rule.

    1 for an outright win, 1/k for a k-way tie for first, 0 otherwise.
    Nobody wins if the top score is $0 or less.
    """
    top = max(final_scores)
    me = final_scores[player_index]
    if me < top:
        return 0.0
    if len(final_scores) > 1 and top <= 0:
        return 0.0
    tied = sum(1 for s in final_scores if s == top)
    if not TIEBREAKER_RULE:
        return 1.0
    return 1.0 / tied


# --- Wager behavior ---------------------------------------------------------

def _roles(scores: Sequence[int]) -> List[int]:
    """Player indices ordered A, B, C (higher score first, then lower index)."""
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


def _grid(score: int) -> List[int]:
    return [score * k // 4 for k in RANDOM_GRID_QUARTERS]


def _mix(score: int, weights: Dict[str, float], bets: Dict[str, Optional[int]]) -> WagerDist:
    """Turn bet types into a wager distribution.

    `bets` maps a bet type to its wager, or None when it does not exist in
    this state. Missing types give their weight to the others in proportion.
    Wagers are clamped to the legal range [0, score].
    """
    live = {k: w for k, w in weights.items() if k == "random" or bets.get(k) is not None}
    total = sum(live.values())
    out: Dict[int, float] = {}
    for kind, w in live.items():
        share = w / total
        if kind == "random":
            grid = _grid(score)
            for g in grid:
                out[g] = out.get(g, 0.0) + share / len(grid)
        else:
            wager = min(max(bets[kind], 0), score)
            out[wager] = out.get(wager, 0.0) + share
    return sorted(out.items())


def wager_distribution(scores: Sequence[int], player_index: int) -> WagerDist:
    """Simulated human Final Jeopardy wager distribution for one player."""
    me = scores[player_index]
    if me <= 0:
        return [(0, 1.0)]
    order = _roles(scores)
    rank = order.index(player_index)
    ranked = [scores[i] for i in order] + [0, 0]
    a, b, c = ranked[0], ranked[1], ranked[2]
    has_b = len(scores) >= 2 and b > 0
    has_c = len(scores) >= 3 and c > 0

    if rank == 0:
        if not has_b:
            return [(0, 1.0)]
        if a > 2 * b:
            return _mix(me, A_LOCKOUT_WEIGHTS, {"zero": 0, "max_safe": a - 2 * b - 1})
        return _mix(me, A_WEIGHTS, {
            "cover": 2 * b - a + 1,
            "cover_tie": 2 * b - a,
            "bankroll": me,
        })

    if rank == 1:
        if has_c:
            keepout = b - 2 * c - 1 if b > 2 * c else 2 * c - b + 1
            if keepout > b:
                keepout = None
        else:
            keepout = None
        overtake = a - b + 1 if a - b + 1 <= b else None
        two_thirds = 3 * b - 2 * a - 1 if 3 * b - 2 * a > 0 else None
        return _mix(me, B_WEIGHTS, {
            "bankroll": me,
            "keepout_c": keepout,
            "overtake_a": overtake,
            "two_thirds": two_thirds,
        })

    return _mix(me, {"random": 1.0}, {})


def score_rank(scores: Sequence[int], player_index: int) -> int:
    """0 for the leader, 1 for second, 2 for third (ties: lower index first)."""
    return _roles(scores).index(player_index)


def fj_accuracy(scores: Sequence[int], player_index: int) -> float:
    """Final Jeopardy accuracy for a simulated contestant, by score rank."""
    rank = min(score_rank(scores, player_index), len(FJ_ACCURACY_BY_RANK) - 1)
    return FJ_ACCURACY_BY_RANK[rank]


def sample_dd_finder(scores: Sequence[int], rng: random.Random) -> int:
    """Pick who finds a future Daily Double, weighted by score rank."""
    order = _roles(scores)
    weights = [DD_FINDER_WEIGHTS_BY_RANK[min(k, len(DD_FINDER_WEIGHTS_BY_RANK) - 1)]
               for k in range(len(order))]
    u = rng.random() * sum(weights)
    acc = 0.0
    for k, w in enumerate(weights):
        acc += w
        if u < acc:
            return order[k]
    return order[-1]


# --- Correlated right/wrong outcomes ----------------------------------------

def quadrature_nodes() -> List[Tuple[float, float]]:
    """(factor value, weight) pairs for the shared clue-difficulty factor."""
    n = int(round(QUAD_HALF_WIDTH / QUAD_STEP))
    xs = [k * QUAD_STEP for k in range(-n, n + 1)]
    ws = [math.exp(-x * x / 2) for x in xs]
    total = sum(ws)
    return [(x, w / total) for x, w in zip(xs, ws)]


def conditional_accuracy(p: float, factor: float, r: float) -> float:
    """P(correct | shared factor) in a one-factor Gaussian copula."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    if r <= 0:
        return p
    return normal_cdf((inverse_normal_cdf(p) - math.sqrt(r) * factor) / math.sqrt(1 - r))


def sample_correct(ps: Sequence[float], r: float, rng: random.Random) -> List[bool]:
    """Draw correlated right/wrong outcomes, one per player."""
    f = rng.gauss(0.0, 1.0)
    out = []
    for p in ps:
        z = math.sqrt(r) * f + math.sqrt(1 - r) * rng.gauss(0.0, 1.0)
        out.append(z < inverse_normal_cdf(p))
    return out


def sample_wager(dist: WagerDist, rng: random.Random) -> int:
    u = rng.random()
    acc = 0.0
    for wager, p in dist:
        acc += p
        if u < acc:
            return wager
    return dist[-1][0]
