# ADR-0002: Opponent-model assumptions in the Tier 2 / Monte Carlo engines

Status: accepted (as a documented placeholder, not a final calibration)
Date: 2026-07-23

## Context

Tier 1 (`engine/fj_wager.py`) needs no assumptions about opponents beyond
the legal wager rules -- it computes a worst-case guarantee. Tier 2
(`engine/fj_bestresponse.py`) and the Daily Double engine
(`engine/dd_wager.py`, `engine/simulate.py`) need actual probabilities: how
likely is an opponent to wager a given amount, how likely are they to
answer correctly, how likely is any given remaining clue to be answered
correctly by someone.

ADR-0001 already rules out shipping the jwolle1 historical dataset, and
this project has not yet done the deeper calibration work of mining the
Tesauro et al. (2013) paper's full tables and figures (Figure 3's opponent
wagering scatter plots, the six-regime empirical model for B, the
round/row-by-row DD accuracy breakdown). Building Tier 2 and the DD engine
now, ahead of that calibration work, means picking some numbers.

## Decision

Ship illustrative, clearly-labeled placeholder parameters rather than wait:

- Opponent Final Jeopardy wagers: uniform distribution over that opponent's
  own Tier 1 breakpoints (bet nothing, their cover wager if one exists,
  their lock-tie wager if one exists, bet everything). This anchors the
  guesses on state-appropriate dollar amounts instead of arbitrary numbers,
  while being explicit that the *weights* (currently uniform) are not
  fitted to anything.
- Opponent Final Jeopardy correctness: 50%, flat, for every opponent and
  every category.
- Regular-clue success rate: 60% probability that some player answers a
  given remaining clue correctly, split evenly among players if so.
- Future (not-yet-found) Daily Doubles: a random player finds it and wagers
  50% of their score at 60% accuracy.

Every one of these constants is named `DEFAULT_...` in code and called out
in module docstrings as a placeholder, not a fitted value. Callers can
override every one of them.

## Consequences

- Recommendations from Tier 2 and the DD engine are directionally useful
  (they correctly capture *shape* -- e.g., don't overbet past the point
  where extra money stops helping -- see the "overbetting" test in
  `tests/test_fj_bestresponse.py`) but the exact recommended dollar amounts
  and win probabilities should not be quoted as validated numbers in the
  white paper or deck without a follow-up calibration pass.
- Any shipped claim of the form "this wager wins X% of the time" must cite
  which opponent-model assumptions produced it, since changing the defaults
  changes the number.
- Follow-up work (tracked in RISK_REGISTER.md, risk #5): mine Tesauro et
  al.'s published tables more thoroughly, and/or use the jwolle1 dataset
  internally (per ADR-0001, not for shipping) to fit real distributions,
  then update these defaults and re-run the test suite, which should still
  pass since the hand-derived tests use explicit fixed models, not the
  defaults.
