"""Final Jeopardy! wagering engine -- Tier 2 (best-response) layer.

Tier 1 (engine/fj_wager.py) answers "what wager can't hurt me if I'm
right?" using a worst-case guarantee that ignores probability entirely.
This module answers a different question: "given my actual confidence in
the category, and some model of how my opponents tend to wager and answer,
what wager maximizes my probability of winning?"

Ties for first place count as wins throughout, matching the show's actual
rule that co-champions both advance to the next game.

IMPORTANT -- the opponent wagering model here is illustrative, not
empirically calibrated. See docs/adr/0002-opponent-model-assumptions.md.
The default model anchors each opponent's plausible wagers on their own
Tier 1 breakpoints (their cover wager, their lock-tie wager, betting
everything, betting zero) and spreads probability uniformly across
whichever of those apply -- an honest "we don't know the real split, so
don't pretend to" placeholder, not a fitted distribution. Pass a different
`opponent_model_fn` once real calibration exists.
"""

from dataclasses import dataclass, field
from itertools import product
from typing import Callable, List, Optional, Sequence, Tuple

import fj_wager

WagerDist = List[Tuple[int, float]]

DEFAULT_OPPONENT_CORRECTNESS = 0.5  # placeholder, not a fitted value


def default_opponent_wager_model(scores: Sequence[int], opponent_index: int) -> WagerDist:
    """Illustrative opponent wager distribution, anchored on Tier 1 breakpoints.

    Not empirically calibrated -- see module docstring.
    """
    rec = fj_wager.analyze(list(scores), opponent_index)
    candidates = {0, rec.max_legal_wager}
    if rec.min_wager_to_guarantee_win is not None:
        candidates.add(rec.min_wager_to_guarantee_win)
    if rec.lock_tie_wager is not None:
        candidates.add(rec.lock_tie_wager)
    candidates = sorted(c for c in candidates if 0 <= c <= rec.max_legal_wager)
    if not candidates:
        candidates = [0]
    weight = 1.0 / len(candidates)
    return [(c, weight) for c in candidates]


@dataclass
class OpponentModel:
    score: int
    wager_dist: WagerDist
    p_correct: float = DEFAULT_OPPONENT_CORRECTNESS


@dataclass
class FJBestResponse:
    player_index: int
    recommended_wager: int
    win_probability: float
    wager_win_probabilities: List[Tuple[int, float]]
    tier1_cover_wager: Optional[int]
    notes: List[str] = field(default_factory=list)


def _final_score(score: int, wager: int, correct: bool) -> int:
    return score + wager if correct else score - wager


def _outcome_probabilities(
    self_score: int,
    self_wager: int,
    p_self_correct: float,
    opponents: List[OpponentModel],
) -> Tuple[float, float]:
    """Exact (tie-inclusive win probability, strict win probability) for a wager.

    Both are computed from the same enumeration over the discrete opponent
    wager distributions supplied -- exact arithmetic, not a Monte Carlo
    estimate, so there is no sampling noise here as long as the opponent
    models are themselves discrete and finite.

    The two numbers differ only in how a tie for first is scored: the first
    counts a tie as a win (matching the show's actual rule that co-champions
    both advance); the second requires an outright, undisputed lead. The gap
    between them exists purely to break ties in `analyze()` -- see the
    comment there for why that matters.
    """
    win_total = 0.0
    strict_total = 0.0
    for self_correct in (True, False):
        p_self = p_self_correct if self_correct else (1 - p_self_correct)
        if p_self == 0:
            continue
        self_final = _final_score(self_score, self_wager, self_correct)

        per_opponent_branches = []
        for opp in opponents:
            branches = []
            for wager, w_prob in opp.wager_dist:
                for correct in (True, False):
                    p = w_prob * (opp.p_correct if correct else (1 - opp.p_correct))
                    if p == 0:
                        continue
                    branches.append((_final_score(opp.score, wager, correct), p))
            per_opponent_branches.append(branches)

        if not per_opponent_branches:
            win_total += p_self  # solo game -- always "wins"
            strict_total += p_self
            continue

        for combo in product(*per_opponent_branches):
            p_combo = p_self
            opp_finals = []
            for final, p in combo:
                p_combo *= p
                opp_finals.append(final)
            if p_combo == 0:
                continue
            opp_max = max(opp_finals)
            if self_final >= opp_max:
                win_total += p_combo
            if self_final > opp_max:
                strict_total += p_combo
    return win_total, strict_total


def expected_win_probability(
    self_score: int,
    self_wager: int,
    p_self_correct: float,
    opponents: List[OpponentModel],
) -> float:
    """Exact expected P(self ties or beats every opponent) for a given wager.

    Kept as a standalone function (rather than folded away) because the
    hand-derived tests in tests/test_fj_bestresponse.py call it directly.
    """
    win, _strict = _outcome_probabilities(self_score, self_wager, p_self_correct, opponents)
    return win


def analyze(
    scores: List[int],
    player_index: int,
    p_self_correct: float,
    opponent_model_fn: Callable[[Sequence[int], int], WagerDist] = default_opponent_wager_model,
    opponent_correctness: float = DEFAULT_OPPONENT_CORRECTNESS,
    wager_step: int = 100,
) -> FJBestResponse:
    """Search for the wager maximizing expected win probability (ties count as wins)."""
    if not 0 <= player_index < len(scores):
        raise ValueError("player_index out of range")

    self_score = scores[player_index]
    max_wager = fj_wager.legal_max_wager(self_score)

    opponents = [
        OpponentModel(
            score=s,
            wager_dist=opponent_model_fn(scores, i),
            p_correct=opponent_correctness,
        )
        for i, s in enumerate(scores)
        if i != player_index
    ]

    tier1 = fj_wager.analyze(scores, player_index)

    candidate_wagers = set(range(0, max_wager + 1, wager_step))
    candidate_wagers.add(max_wager)
    if tier1.min_wager_to_guarantee_win is not None:
        candidate_wagers.add(tier1.min_wager_to_guarantee_win)
    if tier1.lock_tie_wager is not None:
        candidate_wagers.add(tier1.lock_tie_wager)
    candidate_wagers = sorted(w for w in candidate_wagers if 0 <= w <= max_wager)

    outcomes = {
        w: _outcome_probabilities(self_score, w, p_self_correct, opponents)
        for w in candidate_wagers
    }
    results = [(w, win) for w, (win, _strict) in outcomes.items()]

    best_prob = max(p for _, p in results)
    tied = [w for w, p in results if p >= best_prob - 1e-9]
    # Among wagers that achieve the same win probability (ties for first
    # counted as wins), prefer whichever wins *outright* more often, then the
    # smallest wager. Without this, the search is indifferent between a
    # wager that only ties the leader and one that beats them outright,
    # even when the larger wager costs nothing extra in expectation (e.g.
    # at 100% confidence, where there is no downside to betting the extra
    # dollar). Settling for a gratuitous tie when a free strict win is
    # available is a real defect, not a stylistic choice -- see the
    # CHANGELOG entry for the case that surfaced it.
    best_wager = min(tied, key=lambda w: (-outcomes[w][1], w))

    notes = [
        "Opponent wagering model is illustrative (uniform over each "
        "opponent's own Tier 1 breakpoints), not empirically calibrated -- "
        "see docs/adr/0002-opponent-model-assumptions.md.",
        f"Opponent correctness probability assumed at {opponent_correctness:.0%} "
        "for all opponents -- a placeholder, not a fitted value.",
    ]

    return FJBestResponse(
        player_index=player_index,
        recommended_wager=best_wager,
        win_probability=best_prob,
        wager_win_probabilities=results,
        tier1_cover_wager=tier1.min_wager_to_guarantee_win,
        notes=notes,
    )
