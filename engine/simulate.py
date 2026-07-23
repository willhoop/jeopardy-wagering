"""Monte Carlo game-continuation simulator, used by the Daily Double engine.

Simulates the remainder of a game -- any regular clues left in the round,
optionally future Daily Doubles, then Final Jeopardy -- from a hypothetical
point in the game, to estimate win probability. This is deliberately
simplified, and the simplifications are named here rather than hidden:

- Each remaining regular clue is independently "won" by a uniformly random
  player with a fixed probability; the model does not simulate buzzer
  competition, and a wrong answer does not pass the clue to another player
  the way it would on the real show.
- Final Jeopardy inside a rollout is resolved using the Tier 1 (fj_wager)
  closed-form cover-bet logic, for speed -- not the full Tier 2
  opponent-modeled search. Tier 2 (fj_bestresponse) remains available as a
  standalone, more careful one-shot tool for an actual Final Jeopardy
  decision; running it inside every Monte Carlo trial here would be far too
  slow.
- Future Daily Doubles (when `remaining_dd_count` > 0) use a crude
  placeholder: a uniformly random player finds it and wagers a fixed
  fraction of their own score, at a fixed accuracy rate. This has not been
  validated and should be refined before trusting multi-DD-ahead results --
  see RISK_REGISTER.md.

All default rates below are placeholders, not fitted values. Override them
via RolloutConfig once better numbers exist.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional

import fj_wager

DEFAULT_REGULAR_CLUE_SUCCESS_RATE = 0.6  # placeholder: P(someone answers a given clue correctly)
DEFAULT_FJ_CONFIDENCE = 0.5  # placeholder: assumed average Final Jeopardy correctness
DEFAULT_FUTURE_DD_WAGER_FRACTION = 0.5  # placeholder: future-DD finder's bet as a fraction of their score
DEFAULT_FUTURE_DD_SUCCESS_RATE = 0.6  # placeholder: future-DD accuracy


def simulate_remaining_regular_clues(
    scores: List[int],
    clue_values: List[int],
    success_rate: float = DEFAULT_REGULAR_CLUE_SUCCESS_RATE,
    rng: Optional[random.Random] = None,
) -> List[int]:
    rng = rng or random
    scores = list(scores)
    n = len(scores)
    for value in clue_values:
        if rng.random() < success_rate:
            winner = rng.randrange(n)
            scores[winner] += value
    return scores


def simulate_future_daily_doubles(
    scores: List[int],
    count: int,
    wager_fraction: float = DEFAULT_FUTURE_DD_WAGER_FRACTION,
    success_rate: float = DEFAULT_FUTURE_DD_SUCCESS_RATE,
    rng: Optional[random.Random] = None,
) -> List[int]:
    rng = rng or random
    scores = list(scores)
    n = len(scores)
    for _ in range(count):
        finder = rng.randrange(n)
        wager = int(max(scores[finder], 0) * wager_fraction)
        if rng.random() < success_rate:
            scores[finder] += wager
        else:
            scores[finder] -= wager
    return scores


def simulate_final_jeopardy(
    scores: List[int],
    fj_confidence: float = DEFAULT_FJ_CONFIDENCE,
    rng: Optional[random.Random] = None,
) -> List[int]:
    """Resolve Final Jeopardy using each player's Tier 1 cover-bet wager."""
    rng = rng or random
    scores = list(scores)
    wagers = []
    for i in range(len(scores)):
        rec = fj_wager.analyze(scores, i)
        if rec.lockout:
            wagers.append(0)
        elif rec.lock_tie_wager is not None:
            wagers.append(rec.lock_tie_wager)
        elif rec.min_wager_to_guarantee_win is not None:
            wagers.append(rec.min_wager_to_guarantee_win)
        else:
            wagers.append(rec.max_legal_wager)
    for i, w in enumerate(wagers):
        if rng.random() < fj_confidence:
            scores[i] += w
        else:
            scores[i] -= w
    return scores


def wins(scores: List[int], player_index: int) -> bool:
    """True if player_index ties or beats every other player (ties count as wins)."""
    self_score = scores[player_index]
    others = [s for i, s in enumerate(scores) if i != player_index]
    return self_score >= max(others) if others else True


@dataclass
class RolloutConfig:
    remaining_clue_values: List[int] = field(default_factory=list)
    remaining_dd_count: int = 0
    regular_clue_success_rate: float = DEFAULT_REGULAR_CLUE_SUCCESS_RATE
    fj_confidence: float = DEFAULT_FJ_CONFIDENCE
    future_dd_wager_fraction: float = DEFAULT_FUTURE_DD_WAGER_FRACTION
    future_dd_success_rate: float = DEFAULT_FUTURE_DD_SUCCESS_RATE


def rollout(
    scores: List[int],
    player_index: int,
    config: RolloutConfig,
    rng: Optional[random.Random] = None,
) -> bool:
    """Simulate one full game continuation from `scores`. Return True if player_index wins."""
    rng = rng or random
    s = simulate_remaining_regular_clues(
        scores, config.remaining_clue_values, config.regular_clue_success_rate, rng
    )
    if config.remaining_dd_count:
        s = simulate_future_daily_doubles(
            s,
            config.remaining_dd_count,
            config.future_dd_wager_fraction,
            config.future_dd_success_rate,
            rng,
        )
    s = simulate_final_jeopardy(s, config.fj_confidence, rng)
    return wins(s, player_index)
