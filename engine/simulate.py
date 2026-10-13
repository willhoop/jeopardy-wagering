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
- Future Daily Doubles (when `remaining_dd_count` > 0) fall at a uniformly
  random point among the remaining clues. The finder is drawn by score rank
  and wagers a calibrated, round-specific fraction of their score, at a
  calibrated accuracy (engine/behavior.py, ADR-0004). Real finders choose
  their wager from the game state; this model does not.

Defaults marked "calibrated" come from engine/behavior.py (ADR-0004). The
regular-clue success rate is still a placeholder, not a fitted value.
Override any of them via RolloutConfig.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional

import behavior
import fj_wager

DEFAULT_REGULAR_CLUE_SUCCESS_RATE = 0.6  # placeholder: P(someone answers a given clue correctly)
DEFAULT_FJ_CONFIDENCE = behavior.FJ_ACCURACY_OVERALL  # calibrated, ADR-0004
DEFAULT_FUTURE_DD_SUCCESS_RATE = behavior.DD_ACCURACY  # calibrated, ADR-0004


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
    wager_fraction: Optional[float] = None,
    success_rate: float = DEFAULT_FUTURE_DD_SUCCESS_RATE,
    rng: Optional[random.Random] = None,
    round_number: int = 2,
) -> List[int]:
    """Play `count` Daily Doubles found by simulated contestants.

    `wager_fraction=None` uses the calibrated fraction for `round_number`.
    """
    rng = rng or random
    scores = list(scores)
    if wager_fraction is None:
        wager_fraction = behavior.DD_WAGER_FRACTION_BY_ROUND.get(
            round_number, behavior.DD_WAGER_FRACTION_BY_ROUND[2])
    for _ in range(count):
        finder = behavior.sample_dd_finder(scores, rng)
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
    opponent_accuracy: Optional[float] = None,
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
            ps.append(behavior.fj_accuracy(scores, i) if opponent_accuracy is None else opponent_accuracy)
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
    opponent_fj_accuracy: Optional[float] = None  # None: by score rank
    fj_correlation: float = behavior.FJ_OUTCOME_CORRELATION
    future_dd_wager_fraction: Optional[float] = None  # None: calibrated, by round
    future_dd_success_rate: float = DEFAULT_FUTURE_DD_SUCCESS_RATE
    round_number: int = 2


def rollout(
    scores: List[int],
    player_index: int,
    config: RolloutConfig,
    rng: Optional[random.Random] = None,
) -> float:
    """Simulate one game continuation from `scores`. Return player_index's win share."""
    rng = rng or random
    clues = config.remaining_clue_values
    # Each future Daily Double falls at a random point among the remaining clues.
    slots = sorted(rng.randrange(len(clues) + 1) for _ in range(config.remaining_dd_count))
    s = list(scores)
    done = 0
    for slot in slots:
        s = simulate_remaining_regular_clues(s, clues[done:slot], config.regular_clue_success_rate, rng)
        done = slot
        s = simulate_future_daily_doubles(
            s,
            1,
            config.future_dd_wager_fraction,
            config.future_dd_success_rate,
            rng,
            config.round_number,
        )
    s = simulate_remaining_regular_clues(s, clues[done:], config.regular_clue_success_rate, rng)
    s = simulate_final_jeopardy(
        s,
        player_index,
        config.fj_confidence,
        config.opponent_fj_accuracy,
        config.fj_correlation,
        rng,
    )
    return wins(s, player_index)
