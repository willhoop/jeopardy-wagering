"""Final Jeopardy! wagering engine -- Tier 2 (best-response) layer.

Tier 1 (engine/fj_wager.py) answers "what wager can't hurt me if I'm
right?" using a worst-case guarantee that ignores probability entirely.
This module answers a different question: "given my actual confidence in
the category, and how real contestants tend to wager and answer, what
wager maximizes my chance of winning?"

Scoring follows the current tie rule (since November 2014): a tie for first
goes to a tiebreaker clue, so a k-way tie is worth 1/k of a win, and nobody
wins at $0. See engine/behavior.py.

Opponents follow the simulated contestant behavior in engine/behavior.py:
role-based wager mixes (leader, second, third) anchored on Tesauro et al.
(2013) and calibrated to modern-era play (ADR-0004), accuracy by score
rank, and right/wrong outcomes that are correlated across all players (a
hard clue is hard for everyone). The result is exact: we
integrate over the shared difficulty factor and enumerate every wager and
right/wrong branch, so there is no sampling noise.
"""

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import behavior
import fj_wager

WagerDist = behavior.WagerDist

DEFAULT_CORRELATION = behavior.FJ_OUTCOME_CORRELATION


def default_opponent_wager_model(scores: Sequence[int], opponent_index: int) -> WagerDist:
    """Simulated human wager distribution (see engine/behavior.py)."""
    return behavior.wager_distribution(scores, opponent_index)


@dataclass
class OpponentModel:
    score: int
    wager_dist: WagerDist
    p_correct: float = behavior.FJ_ACCURACY_OVERALL


@dataclass
class FJBestResponse:
    player_index: int
    recommended_wager: int
    win_probability: float
    wager_win_probabilities: List[Tuple[int, float]]
    tier1_cover_wager: Optional[int]
    notes: List[str] = field(default_factory=list)


def _opponent_table(
    opponents: List[OpponentModel], p_self: float, binary_correlation: float
) -> List[Tuple[float, float, Dict[Tuple[int, int], float]]]:
    """For each quadrature node: (weight, P(self right | node), opponent table).

    The opponent table maps (best opponent final score, how many opponents
    share it) to its probability, given the node.
    """
    r = behavior.latent_correlation(binary_correlation) if binary_correlation > 0 else 0.0
    nodes = behavior.quadrature_nodes() if r > 0 else [(0.0, 1.0)]
    table = []
    for factor, weight in nodes:
        branches = []
        for opp in opponents:
            pc = behavior.conditional_accuracy(opp.p_correct, factor, r)
            b: Dict[int, float] = {}
            for wager, wp in opp.wager_dist:
                for correct, p in ((True, pc), (False, 1 - pc)):
                    if wp * p == 0:
                        continue
                    final = opp.score + wager if correct else opp.score - wager
                    b[final] = b.get(final, 0.0) + wp * p
            branches.append(list(b.items()))
        tops: Dict[Tuple[int, int], float] = {}
        for combo in product(*branches):
            p = 1.0
            finals = []
            for final, pp in combo:
                p *= pp
                finals.append(final)
            if not finals:
                key = (None, 0)
            else:
                m = max(finals)
                key = (m, finals.count(m))
            tops[key] = tops.get(key, 0.0) + p
        table.append((weight, behavior.conditional_accuracy(p_self, factor, r), tops))
    return table


def _share(self_final: int, top, count: int) -> float:
    if top is None:
        return 1.0
    if self_final > top:
        return 1.0 if self_final > 0 else 0.0  # nobody wins at $0 or less
    if self_final == top:
        return behavior.win_share([self_final] + [top] * count, 0)
    return 0.0


def _expected_outcome(self_score: int, wager: int, table) -> Tuple[float, float]:
    """(expected win share, expected winnings) for one wager.

    Winnings are the final score times the win share: the winner keeps
    their total, everyone else keeps nothing of it.
    """
    share = money = 0.0
    up, down = self_score + wager, self_score - wager
    for weight, ps, tops in table:
        for (top, count), p in tops.items():
            s_up, s_down = _share(up, top, count), _share(down, top, count)
            share += weight * p * (ps * s_up + (1 - ps) * s_down)
            money += weight * p * (ps * s_up * up + (1 - ps) * s_down * down)
    return share, money


def _expected_share(self_score: int, wager: int, table) -> float:
    return _expected_outcome(self_score, wager, table)[0]


def expected_win_probability(
    self_score: int,
    self_wager: int,
    p_self_correct: float,
    opponents: List[OpponentModel],
    correlation: float = 0.0,
) -> float:
    """Exact expected win share for one wager (ties settled by tiebreaker).

    `correlation` defaults to 0 here so hand-derived tests can use
    independent outcomes; `analyze()` uses the published value.
    """
    table = _opponent_table(opponents, p_self_correct, correlation)
    return _expected_share(self_score, self_wager, table)


def analyze(
    scores: List[int],
    player_index: int,
    p_self_correct: float,
    opponent_model_fn: Callable[[Sequence[int], int], WagerDist] = default_opponent_wager_model,
    opponent_correctness: Optional[float] = None,
    correlation: float = DEFAULT_CORRELATION,
    wager_step: int = 100,
) -> FJBestResponse:
    """Search for the wager with the highest expected win share.

    `opponent_correctness=None` gives each opponent the calibrated accuracy
    for their score rank; a float gives every opponent that accuracy.
    """
    if not 0 <= player_index < len(scores):
        raise ValueError("player_index out of range")

    self_score = scores[player_index]
    max_wager = fj_wager.legal_max_wager(self_score)

    opponents = [
        OpponentModel(
            score=s,
            wager_dist=opponent_model_fn(scores, i),
            p_correct=(behavior.fj_accuracy(scores, i)
                       if opponent_correctness is None else opponent_correctness),
        )
        for i, s in enumerate(scores)
        if i != player_index
    ]

    tier1 = fj_wager.analyze(scores, player_index)

    candidate_wagers = set(range(0, max_wager + 1, wager_step))
    candidate_wagers.add(max_wager)
    if tier1.min_wager_to_guarantee_win is not None:
        candidate_wagers.add(tier1.min_wager_to_guarantee_win)
        candidate_wagers.add(tier1.min_wager_to_guarantee_win - 1)
    if tier1.lock_tie_wager is not None:
        candidate_wagers.add(tier1.lock_tie_wager)
    # Breakpoints: the wagers that just pass, tie, or just stay above each
    # possible opponent final score. Win share only changes at these
    # points, so the best wager in each flat stretch is always tried.
    for opp in opponents:
        for wager, _p in opp.wager_dist:
            for final in (opp.score + wager, opp.score - wager):
                for w in (final - self_score, final - self_score + 1,
                          self_score - final, self_score - final - 1):
                    candidate_wagers.add(w)
    candidate_wagers = sorted(w for w in candidate_wagers if 0 <= w <= max_wager)

    table = _opponent_table(opponents, p_self_correct, correlation)
    outcomes = {w: _expected_outcome(self_score, w, table) for w in candidate_wagers}
    results = [(w, outcomes[w][0]) for w in candidate_wagers]

    best_prob = max(p for _, p in results)
    # Win chance first, money second. Among wagers that tie on win share
    # (within rounding), take the one with the highest expected winnings,
    # then the smallest. A solo player, or a leader in a lockout, wins
    # whatever they bet, so only the money can separate the wagers.
    tied = [w for w, p in results if p >= best_prob - 1e-9]
    best_wager = max(tied, key=lambda w: (round(outcomes[w][1], 6), -w))

    notes = [
        "Ties for first go to a tiebreaker clue (rule since November 2014), "
        "scored as an equal share of the win.",
        "Opponents follow simulated contestant behavior, calibrated to "
        "modern-era play -- see engine/behavior.py, ADR-0003 and ADR-0004.",
        "Opponent accuracy: "
        + ("by score rank" if opponent_correctness is None else f"{opponent_correctness:.0%}")
        + f"; outcome correlation {correlation:.2f} across all players.",
    ]

    return FJBestResponse(
        player_index=player_index,
        recommended_wager=best_wager,
        win_probability=best_prob,
        wager_win_probabilities=results,
        tier1_cover_wager=tier1.min_wager_to_guarantee_win,
        notes=notes,
    )
