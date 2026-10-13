"""Daily Double wagering engine -- Monte Carlo expected-value search.

Given a player's own confidence in a Daily Double clue and a description of
what's left in the game, this searches candidate wagers for the one that
maximizes simulated win probability. A tie for first goes to a tiebreaker
clue, so it counts as an equal share of a win (engine/behavior.py). See engine/simulate.py for exactly what is and isn't modeled --
this is deliberately simplified and documented as such.

Legal wager bounds: a Daily Double wager may be up to the greater of the
player's current score or the maximum clue value showing on the board for
that round ($1,000 in Single Jeopardy, $2,000 in Double Jeopardy, under the
rules current as of this writing).

STATISTICAL METHOD (rewritten 2026-07-23, second review). Each candidate
wager's win probability is a Monte Carlo *estimate*. Choosing a wager from
these estimates is a statistical decision, and getting it wrong caused two
successive, documented defects:

1. The original engine took a bare argmax with a 1e-9 tolerance, treating
   noisy estimates as exact -- a two-point confidence change swung the
   recommendation from $350 to $4,200 for identical scores.

2. The first fix introduced a "plateau" of statistically-indistinguishable
   wagers, but computed the comparison variance with the INDEPENDENT
   two-sample formula sqrt(se_w**2 + se_best**2). That formula is wrong for
   this simulator, because the simulator uses common random numbers (CRN):
   every candidate wager is evaluated on the SAME replayed rest-of-game
   randomness within each trial. CRN makes the per-wager win indicators
   strongly positively correlated (empirically, correlation rises toward 1.0
   for nearby wagers), so the variance of the *difference* between two
   wagers is far smaller than the independent formula claims:
       Var(p_w - p_best) = Var(p_w) + Var(p_best) - 2 Cov(p_w, p_best),
   and Cov > 0 here. Using the independent formula threw away exactly the
   variance reduction CRN was added to buy, producing a spuriously wide
   plateau that systematically *under-bet* (it recommended ~$0 even in spots
   where betting was clearly better).

The current method fixes both:

  * Comparison variance is estimated with the PAIRING. For each trial we
    record whether each candidate wager won, then the standard error of the
    difference (candidate vs. the empirical best wager) is the sample
    standard deviation of the per-trial paired difference divided by
    sqrt(trials). This respects the CRN design instead of contradicting it.

  * Multiplicity is controlled. We compare ~k candidate wagers against the
    single empirical best, which is a multiple-comparisons-with-the-best
    (MCB) problem (Hsu, 1996). Using a per-comparison z would re-introduce
    the instability, because the empirical best is itself selected as the
    max of k noisy estimates. We therefore use a Bonferroni band,
    z* = Phi^{-1}(1 - alpha/k), which adapts to the number of candidate
    wagers. This restores stable recommendations (verified across seeds and
    across neighbouring confidence levels) while still recommending a
    positive wager when the signal is real.

KNOWN LIMITATIONS (documented, not silently ignored -- see
docs/reviews/statistical-review-2026-07-23-v2.md and RISK_REGISTER.md):

  * `win_probability` is the in-sample maximum over candidate wagers, so it
    is an optimistic (selection-biased / "winner's curse") estimate of the
    true best win probability. The *recommended wager* is far less affected,
    because it is the smallest wager on a multiplicity-controlled plateau,
    not the raw argmax -- but treat the reported percentage as a mild
    upper bound, not an unbiased point estimate.

  * Win probability is not monotone in the wager, because opponents' modeled
    Final Jeopardy wagers depend on the player's own score (see
    engine/simulate.py). CRN gives a fair *paired comparison*, not a
    monotonicity guarantee.
"""

import math
import random
import statistics
from dataclasses import dataclass, field, replace
from typing import List, Optional, Tuple

from simulate import RolloutConfig, rollout

ROUND_MAX_CLUE_VALUE = {1: 1000, 2: 2000}


def _standard_error(p: float, trials: int) -> float:
    """Marginal standard error of a Monte Carlo estimate of a probability p.

    This is the standard error of a single wager's win-probability estimate
    on its own. It is reported for context, but it is NOT the right quantity
    for *comparing* two wagers under common random numbers -- see
    `_paired_standard_error` and the module docstring.
    """
    return math.sqrt(max(p * (1 - p), 0.0) / trials)


def _paired_standard_error(wins_a: List[int], wins_b: List[int]) -> float:
    """Standard error of the mean paired difference between two wagers.

    `wins_a` and `wins_b` are per-trial win shares (0, 1/k or 1) for two candidate
    wagers evaluated on the SAME common random numbers. Because the two
    estimates are paired trial-by-trial, the variance of their difference is
    estimated directly from the per-trial differences, which correctly
    captures the CRN-induced correlation.
    """
    n = len(wins_a)
    if n < 2:
        return 0.0
    diffs = [wins_a[i] - wins_b[i] for i in range(n)]
    return statistics.pstdev(diffs) / math.sqrt(n)


def _bonferroni_z(num_candidates: int, alpha: float) -> float:
    """One-sided Bonferroni critical value for comparisons-with-the-best.

    We test each of `num_candidates` wagers against the single empirical best
    wager, so the family-wise one-sided level alpha is split across the
    comparisons: z* = Phi^{-1}(1 - alpha / num_candidates). This is a
    deliberately conservative (Bonferroni) bound on the exact MCB constant
    (Hsu, 1996), which keeps the recommendation stable without an external
    dependency.
    """
    num_candidates = max(int(num_candidates), 1)
    q = 1.0 - alpha / num_candidates
    q = min(max(q, 0.5 + 1e-12), 1.0 - 1e-12)
    return statistics.NormalDist().inv_cdf(q)


def legal_max_dd_wager(score: int, round_number: int) -> int:
    """Largest legal Daily Double wager: the greater of current score or the round cap."""
    floor = ROUND_MAX_CLUE_VALUE.get(round_number, 1000)
    return max(score, floor, 0)


@dataclass
class DDRecommendation:
    player_index: int
    player_score: int
    round_number: int
    p_correct: float
    recommended_wager: int
    win_probability: float
    wager_win_probabilities: List[Tuple[int, float]]
    standard_errors: List[Tuple[int, float]]
    comparison_standard_errors: List[Tuple[int, float]]
    plateau: List[int]
    z_score_used: float
    trials_per_wager: int
    notes: List[str] = field(default_factory=list)


def analyze(
    scores: List[int],
    player_index: int,
    round_number: int,
    p_correct: float,
    config: Optional[RolloutConfig] = None,
    wager_step: int = 100,
    trials_per_wager: int = 3000,
    z_score: Optional[float] = None,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> DDRecommendation:
    """Search for the best Daily Double wager under CRN + MCB.

    Parameters
    ----------
    z_score:
        If None (default), a multiplicity-aware Bonferroni band is computed
        from the number of candidate wagers and `alpha`. Pass a float to
        override with a fixed band (used by regression tests and for
        experimentation).
    alpha:
        Family-wise one-sided error level for the Bonferroni band. Ignored
        when `z_score` is given explicitly.
    """
    if not 0 <= player_index < len(scores):
        raise ValueError("player_index out of range")
    if config is None:
        config = RolloutConfig()
    # Future Daily Doubles in a rollout belong to the same round as this one.
    config = replace(config, round_number=round_number)

    player_score = scores[player_index]
    max_wager = legal_max_dd_wager(player_score, round_number)
    candidate_wagers = sorted(set(range(0, max_wager + 1, wager_step)) | {max_wager})

    # Common random numbers: each trial draws one shared "trial seed" used to
    # replay the *same* rest-of-game randomness (which clues go to whom,
    # future DD outcomes, everyone's Final Jeopardy correctness) for every
    # candidate wager. Only the wager itself differs between candidates
    # within a trial. We record the full per-trial win indicator for every
    # wager so the comparison variance can be estimated WITH the pairing
    # (see _paired_standard_error), which is the whole point of using CRN.
    base_rng = random.Random(seed)
    win_indicators = {w: [] for w in candidate_wagers}
    for _ in range(trials_per_wager):
        trial_seed = base_rng.randrange(2**31)
        for w in candidate_wagers:
            rng = random.Random(trial_seed)
            correct = rng.random() < p_correct
            trial_scores = list(scores)
            if correct:
                trial_scores[player_index] += w
            else:
                trial_scores[player_index] -= w
            win_indicators[w].append(rollout(trial_scores, player_index, config, rng))

    results: List[Tuple[int, float]] = [
        (w, sum(win_indicators[w]) / trials_per_wager) for w in candidate_wagers
    ]
    standard_errors: List[Tuple[int, float]] = [
        (w, _standard_error(p, trials_per_wager)) for w, p in results
    ]

    best_prob = max(p for _, p in results)
    best_wager = min(w for w, p in results if p == best_prob)
    best_indicator = win_indicators[best_wager]

    # Paired comparison SE of each wager against the empirical best wager.
    comparison_standard_errors: List[Tuple[int, float]] = [
        (w, _paired_standard_error(win_indicators[w], best_indicator))
        for w in candidate_wagers
    ]
    comp_se_by_wager = dict(comparison_standard_errors)

    z = z_score if z_score is not None else _bonferroni_z(len(candidate_wagers), alpha)

    # A wager is on the plateau if it cannot be distinguished from the best
    # using the PAIRED comparison SE and the multiplicity-aware band. The
    # best wager itself is always included (paired SE against itself is 0).
    plateau = []
    for w, p in results:
        if w == best_wager or (best_prob - p) <= z * comp_se_by_wager[w]:
            plateau.append(w)
    plateau.sort()

    # Among the plateau, prefer the smallest wager: never bet more than a
    # statistically-justified amount.
    recommended_wager = min(plateau)

    # Exact ties: wagers with the same outcome as the recommendation on
    # EVERY trial (for example, a solo game, which is always won). They
    # cannot differ in win chance, so pick by money: the Daily Double itself
    # adds (2p - 1) * wager on average, so bet the most when p > 0.5.
    rec_vector = win_indicators[recommended_wager]
    exact = [w for w in candidate_wagers if win_indicators[w] == rec_vector]
    if p_correct > 0.5:
        recommended_wager = max(exact)

    notes = [
        f"Win probabilities are Monte Carlo estimates ({trials_per_wager} trials "
        "per candidate wager, evaluated on common random numbers so wagers can "
        "be compared trial-by-trial).",
        f"Wagers from ${min(plateau):,} to ${max(plateau):,} are statistically "
        "indistinguishable from the best estimate, using the paired (CRN-aware) "
        f"comparison and a multiplicity-adjusted band of z*={z:.2f} across "
        f"{len(candidate_wagers)} candidate wagers. The smallest is recommended: "
        "there is no statistical reason to risk more."
        if len(plateau) > 1
        else "No other wager is statistically close to this one at this trial count.",
        "The reported win probability is the in-sample maximum over candidate "
        "wagers, so it is a mild optimistic (selection-biased) estimate; the "
        "recommended wager is far less affected -- see the module docstring.",
        "Regular-clue and future-Daily-Double dynamics use simplified placeholder "
        "models -- see engine/simulate.py module docstring and RISK_REGISTER.md.",
    ]

    return DDRecommendation(
        player_index=player_index,
        player_score=player_score,
        round_number=round_number,
        p_correct=p_correct,
        recommended_wager=recommended_wager,
        win_probability=best_prob,
        wager_win_probabilities=results,
        standard_errors=standard_errors,
        comparison_standard_errors=comparison_standard_errors,
        plateau=plateau,
        z_score_used=z,
        trials_per_wager=trials_per_wager,
        notes=notes,
    )
