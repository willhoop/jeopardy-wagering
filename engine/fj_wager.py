"""Final Jeopardy! wagering engine — Tier 1 (guarantee / worst-case) layer.

This module answers a narrow, fully-determined question: given the scores of
up to three players entering Final Jeopardy, what wager guarantees the best
possible finishing position, assuming every opponent makes the single most
threatening legal play against you — betting their full score and answering
correctly?

It does not model opponent psychology, category confidence, or the odds of
answering correctly. That is the Tier 2 (best-response) layer, which lives
in engine/fj_bestresponse.py. Tier 1 answers "what wager can't hurt me if
I'm right?", not "what wager maximizes my win probability?".

References: Williams, K., "How to wager in Final Jeopardy!," The Final Wager
(https://thefinalwager.wordpress.com/tutorial/); Dupée, M. (1998), How to Get
on Jeopardy!--and Win!, as cited by Tesauro, Gondek, Lenchner, Fan & Prager
(2013), JAIR 47:205-251, doi:10.1613/jair.3834.
"""

from dataclasses import dataclass, field
from typing import List, Optional


def legal_max_wager(score: int) -> int:
    """Largest legal Final Jeopardy wager for a given current score.

    A player may wager up to their full current score. A player with a score
    of zero or less has no winnings to stake and cannot wager.
    """
    return max(score, 0)


def worst_case_ceiling(score: int) -> int:
    """Highest score this player could reach: bet the legal max and win.

    This is the number an opponent must beat, or tie, to be safe against
    this player, under the worst-case assumption that the player bets
    everything and answers correctly.
    """
    if score <= 0:
        return score
    return 2 * score


@dataclass
class FJRecommendation:
    player_index: int
    player_score: int
    opponent_scores: List[int]
    lockout: bool
    binding_opponent_index: Optional[int]
    min_wager_to_guarantee_win: Optional[int]
    max_legal_wager: int
    lock_tie_wager: Optional[int]
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = []
        if self.lockout:
            lines.append(
                f"Player {self.player_index}: lockout. Wagering $0 guarantees "
                f"first place regardless of the Final Jeopardy outcome."
            )
        elif self.min_wager_to_guarantee_win is not None:
            lines.append(
                f"Player {self.player_index}: no lockout. Wager at least "
                f"${self.min_wager_to_guarantee_win} to guarantee the win if "
                f"correct, covering opponent {self.binding_opponent_index}'s "
                f"worst-case doubled score."
            )
        else:
            lines.append(
                f"Player {self.player_index}: cannot guarantee an outright win. "
                f"Opponent {self.binding_opponent_index}'s worst-case score "
                f"exceeds what this player can cover even at the maximum "
                f"legal wager (${self.max_legal_wager})."
            )
        if self.lock_tie_wager is not None:
            lines.append(
                f"Lock-tie available: wagering ${self.lock_tie_wager} and "
                f"answering correctly ties for first if opponent "
                f"{self.binding_opponent_index} bets $0 (they have no need to "
                f"bet). It is not a guarantee: if they bet and are right, "
                f"they pass you. A tie goes to a tiebreaker clue."
            )
        lines.extend(self.notes)
        return "\n".join(lines)


def analyze(scores: List[int], player_index: int) -> FJRecommendation:
    """Compute the Tier 1 guarantee-based Final Jeopardy wager for one player.

    Parameters
    ----------
    scores:
        Every player's score entering Final Jeopardy, in any order. Supports
        1, 2, or 3 players (or more; the underlying logic generalizes to any
        number of opponents).
    player_index:
        Index into `scores` of the player to recommend a wager for.
    """
    if not 0 <= player_index < len(scores):
        raise ValueError("player_index out of range")

    player_score = scores[player_index]
    opponents = [(i, s) for i, s in enumerate(scores) if i != player_index]
    max_wager = legal_max_wager(player_score)

    if not opponents:
        return FJRecommendation(
            player_index=player_index,
            player_score=player_score,
            opponent_scores=[],
            lockout=True,
            binding_opponent_index=None,
            min_wager_to_guarantee_win=0,
            max_legal_wager=max_wager,
            lock_tie_wager=None,
            notes=[
                "Solo game -- no opponents. Any wager keeps first place; "
                "wager choice only matters for this player's own score target."
            ],
        )

    # The binding constraint is whichever opponent's worst-case ceiling is
    # highest. Every opponent can reach their own ceiling in the same game,
    # so beating the highest ceiling beats them all; no independence is
    # needed.
    ceilings = [(i, worst_case_ceiling(s)) for i, s in opponents]
    binding_index, binding_ceiling = max(ceilings, key=lambda pair: pair[1])

    lockout = player_score > binding_ceiling
    notes: List[str] = []
    min_wager: Optional[int]

    if lockout:
        min_wager = 0
        notes.append(
            f"Player {player_index}'s current score (${player_score}) already "
            f"exceeds every opponent's worst-case doubled score (highest is "
            f"${binding_ceiling}, opponent {binding_index})."
        )
    else:
        required = binding_ceiling - player_score + 1
        if required <= max_wager:
            min_wager = required
        else:
            min_wager = None
            notes.append(
                f"Guaranteeing an outright win needs ${required}, more than "
                f"this player's max legal wager of ${max_wager}."
            )

    # Lock-tie check: wagering everything lands on an exact tie with the
    # binding opponent's current score, when that opponent is themselves
    # already safely ahead of everyone else and so has no reason to wager.
    lock_tie_wager = None
    if not lockout:
        binding_score = scores[binding_index]
        other_scores = [
            s for i, s in enumerate(scores) if i not in (player_index, binding_index)
        ]
        binding_opponent_is_locked_out = (
            all(binding_score > worst_case_ceiling(s) for s in other_scores)
            if other_scores
            else True
        )
        if binding_opponent_is_locked_out and player_score * 2 == binding_score:
            lock_tie_wager = player_score
            notes.append(
                f"Player {player_index}'s score is exactly half of opponent "
                f"{binding_index}'s, and that opponent has no reason to wager "
                f"(already safely ahead of everyone else at $0). Betting "
                f"everything (${lock_tie_wager}) and answering correctly ties "
                f"for first."
            )

    return FJRecommendation(
        player_index=player_index,
        player_score=player_score,
        opponent_scores=[s for _, s in opponents],
        lockout=lockout,
        binding_opponent_index=binding_index,
        min_wager_to_guarantee_win=min_wager,
        max_legal_wager=max_wager,
        lock_tie_wager=lock_tie_wager,
        notes=notes,
    )


def analyze_all(scores: List[int]) -> List[FJRecommendation]:
    """Convenience wrapper: compute the recommendation for every player."""
    return [analyze(scores, i) for i in range(len(scores))]
