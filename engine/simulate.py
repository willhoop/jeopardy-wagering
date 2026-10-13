"""Monte Carlo game-continuation simulator, used by the Daily Double engine.

Simulates the remainder of a game -- any regular clues left in the round,
optionally future Daily Doubles, then Final Jeopardy -- from a hypothetical
point in the game, to estimate win probability. This is deliberately
simplified, and the simplifications are named here rather than hidden:

- Each remaining regular clue is independently "won" by a uniformly random
  player with a fixed probability; the model does not simulate buzzer
  competition, and a wrong answer does not pass the clue to another player
  the way it would on the real show.
- Final Jeopardy inside a rollout: the player being advised uses the Tier 1
  (fj_wager) cover-bet logic, for speed. Opponents draw a wager from the
  simulated contestant behavior in engine/behavior.py. Right/wrong outcomes
  are correlated across all players (engine/behavior.py).
- The result of a rollout is a win share under the tiebreaker rule: 1 for
  an outright win, 1/k for a k-way tie for first, 0 otherwise.
- Future Daily Doubles (when `remaining_dd_count` > 0) use a crude
  placeholder: a uniformly random player finds it and wagers a fixed
  fraction of their own score, at a fixed accuracy rate. This has not been
  validated and should be refined before trusting multi-DD-ahead results --
  see RISK_REGISTER.md.

Defaults marked "published" come from Tesauro et al. (2013) via engine/behavior.py;
the rest are placeholders, not fitted values. Override any of them
via RolloutConfig once better numbers exist.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional

import behavior
import fj_wager

DEFAULT_REGULAR_CLUE_SUCCESS_RATE = 0.6  # placeholder: P(someone answers a given clue correctly)
DEFAULT_FJ_CONFIDENCE = behavior.FJ_ACCURACY_AVERAGE  # published, Tesauro et al. (2013)
DEFAULT_FUTURE_DD_WAGER_FRACTION = 0.5  # placeholder: future-DD finder's bet as a fraction of their score
DEFAULT_FUTURE_DD_SUCCESS_RATE = behavior.DD_ACCURACY_AVERAGE  # published, Tesauro et al. (2013)


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


def tier1_wager(scores: List[int], i: int) -> int:
    """The advised player's Final Jeopardy wager inside a rollout."""
    rec = fj_wager.analyze(scores, i)
    if rec.lockout:
        return 0
    if rec.lock_tie_wager is not None:
        return rec.lock_tie_wager
    if rec.min_wager_to_guarantee_win is not None:
        return rec.min_wager_to_guarantee_win
    return rec.max_legal_wager


def simulate_final_jeopardy(
    scores: List[int],
    player_index: int,
    fj_confidence: float = DEFAULT_FJ_CONFIDENCE,
    opponent_accuracy: float = behavior.FJ_ACCURACY_AVERAGE,
    correlation: float = behavior.FJ_OUTCOME_CORRELATION,
    rng: Optional[random.Random] = None,
) -> List[int]:
    """Resolve Final Jeopardy: Tier 1 wager for the advised player,
    simulated human wagers for opponents, correlated right/wrong outcomes."""
    rng = rng or random
    scores = list(scores)
    wagers = []
    ps = []
    for i in range(len(scores)):
        if i == player_index:
            wagers.append(tier1_wager(scores, i))
            ps.append(fj_confidence)
        else:
            wagers.append(behavior.sample_wager(behavior.wager_distribution(scores, i), rng))
            ps.append(opponent_accuracy)
    r = behavior.latent_correlation(correlation) if correlation > 0 else 0.0
    correct = behavior.sample_correct(ps, r, rng)
    for i, w in enumerate(wagers):
        scores[i] += w if correct[i] else -w
    return scores


def wins(scores: List[int], player_index: int) -> float:
    """Win share under the tiebreaker rule (see behavior.win_share)."""
    return behavior.win_share(scores, player_index)


@dataclass
class RolloutConfig:
    remaining_clue_values: List[int] = field(default_factory=list)
    remaining_dd_count: int = 0
    regular_clue_success_rate: float = DEFAULT_REGULAR_CLUE_SUCCESS_RATE
    fj_confidence: float = DEFAULT_FJ_CONFIDENCE
    opponent_fj_accuracy: float = behavior.FJ_ACCURACY_AVERAGE
    fj_correlation: float = behavior.FJ_OUTCOME_CORRELATION
    future_dd_wager_fraction: float = DEFAULT_FUTURE_DD_WAGER_FRACTION
    future_dd_success_rate: float = DEFAULT_FUTURE_DD_SUCCESS_RATE


def rollout(
    scores: List[int],
    player_index: int,
    config: RolloutConfig,
    rng: Optional[random.Random] = None,
) -> float:
    """Simulate one game continuation from `scores`. Return player_index's win share."""
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
    s = simulate_final_jeopardy(
        s,
        player_index,
        config.fj_confidence,
        config.opponent_fj_accuracy,
        config.fj_correlation,
        rng,
    )
    return wins(s, player_index)
