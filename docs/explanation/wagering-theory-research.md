# Jeopardy! Wagering Strategy — Research Foundations

Status: working notes. Consolidated into the finalized, citable version at
`docs/white-paper.md` on 2026-07-23 — read that one for the polished
version of everything below, including worked examples and the current
validation status. This file stays as the running research log.
Date: 2026-07-23

## 1. Scope

Build a wagering strategy model for two decisions: Daily Double (DD) bets and
Final Jeopardy (FJ) bets. The primary case is a 3-player game. 2-player and
1-player games are reduced cases of the same model.

## 2. Data landscape

J-Archive (j-archive.com) is the community record of historical games. Its own
site terms forbid scraping, republication, and monetization of its content. A
scraper built against J-Archive directly would break those terms.

Three usable alternatives exist:

- **jwolle1/jeopardy_clue_dataset** (GitHub). 538,845 clues as of the Season
  41 release (the README listed 554,131 clues through Season 42 in July
  2026). Each row lists the clue value, the Daily Double wager (zero if not a
  DD), round, and category. A companion file gives contestant scores, Coryat
  scores and right/wrong counts. The README states two restrictions:
  the source "prefers not to be credited," and the data must not be used "to
  make a public-facing web site, app, or any other product." This makes the
  dataset usable for internal calibration and validation only — not for a
  shipped product, white paper appendix, or public dataset release.
- **J-Archive's own Wagering Calculator** (j-archive.com/wageringcalculator.php).
  A reference implementation of community FJ logic. Useful to compare our
  model's output against, not a data source.
- **Tesauro, Gondek, Lenchner, Fan & Prager (2013), "Analysis of Watson's
  Strategies for Playing Jeopardy!," Journal of Artificial Intelligence
  Research 47:205–251** (arXiv:1402.0571). The IBM Watson team mined roughly
  3,000 J-Archive episodes to build empirical models of DD accuracy, FJ
  wagering behavior, and DD placement. The paper publishes the resulting
  aggregate statistics. These numbers are citable research findings, not raw
  scraped rows, so they carry no reuse restriction.

**Working decision:** cite the Tesauro et al. published statistics for
anything that ships (white paper, deck, docs). Use the jwolle1 dataset only
to validate our simulator internally, never to populate a shipped artifact.
See ADR-0001.

## 3. Final Jeopardy wagering

### 3.1 Two-player heuristics (Keith Williams, "The Final Wager")

- **Lockout:** if the leader (A) holds more than double the second-place
  score (B), A cannot lose regardless of the FJ outcome and does not need to
  wager.
- **Cover bet:** if A holds less than double B, A should wager at least
  `2B - A + 1`, so that a correct answer keeps A ahead even if B doubles up.
  (`2B - A` only ties.)
- **Bet-to-tie:** in some score ranges, wagering to land on an exact tie beats
  a full cover bet, because it changes which outcomes A needs to win.
  (Advice from the co-champion era, before November 2014; under the
  tiebreaker rule a tie is worth less than a win.)
- **Two-thirds rule** (Dupée, 1998, as cited by Tesauro et al.): if B holds
  at least two-thirds of A's score and A bets to cover, B should wager no
  more than `3B - 2A`. B then wins whenever A misses, whether or not B is
  right. Betting more makes B also need a correct answer. A can counter
  with an "anti-two-thirds" bet (Tesauro et al., §1.1).

### 3.2 Three-player heuristics

Williams frames the three-player case as three pairwise sub-problems: A vs.
B, B vs. C, and A vs. C. The wager must satisfy all three constraints at
once, which sometimes forces a tie-wager instead of a clean cover.

Tesauro et al. found no evidence that third-place (C) wagers vary with the
strategic situation and used one C model for all groups (§2.3, note 5).
They split A and B behavior into six groups at strategic breakpoints: B/A
below 2/3, 2/3 to 3/4, above 3/4, crossed with whether B is at least 2C.

### 3.3 Game-theoretic layer

The exact optimum requires each player's private confidence in the FJ
category, which opponents cannot observe — formally, a Bayesian game. The
Watson team avoided computing a full Bayes-Nash equilibrium (too costly to
compute, and human opponents do not play equilibrium strategy anyway).
Instead they computed a **Best-Response** strategy against an empirically
fitted model of human wagering, using Monte Carlo simulation.

Implication for this project: build two layers.

1. An interpretable heuristic layer (Williams' addition/subtraction rules,
   the two-thirds rule, lockout/lock-tie detection) for at-a-glance use.
2. A simulation-backed optimizer (Monte Carlo best-response against a fitted
   opponent model) for practice, analysis, and to validate layer 1.

Layer 2 is a study and practice tool, not a live-assist device — live
wagering assistance during an actual taping would break the show's rules.
State this explicitly in the README and white paper.

Notable edge cases the model must handle: lockout, lock-tie (B holds exactly
half of A's score — B should bet everything, since a tie beats needing both a
correct answer and an A miss), and "anti-two-thirds" bets in categories where
confidence is unusually low.

## 4. Daily Double wagering

### 4.1 Empirical baseline

Tesauro et al. report that second-round DD accuracy by row (a proxy for
clue difficulty) is about 72% for the top two rows, falling to about 57%
for the bottom row (§3.1.4). Overall mean DD accuracy is 64% for average
contestants (§2.2).

The paper's central finding on human behavior: contestants underbet DDs
relative to the wager that maximizes win probability. In last-DD situations
(second round, no DDs remaining; the subset of more than 2,200 regular
episodes in which both second-round DDs were played), leading players bet
$2,590 on average against a $5,380 average simulator-recommended bet at
row-based default confidence; trailing players bet $3,120 against $6,970
(§3.1.4, Table 3). Quantifying this conservatism gap — how much win
probability a real bet leaves on the table — is a natural benchmark output
for our tool.

### 4.2 Proposed expected-value model

State: current score, opponent scores, remaining board value, round, and a
confidence estimate `p` for the category (row position is one proxy;
self-reported confidence is another).

```
E(bet) = p · V(score + bet, ...) + (1 - p) · V(score - bet, ...)
```

`V(...)` is the win probability of the resulting state, estimated by
simulating the rest of the game forward (Monte Carlo rollout). Search should
include near-miss bets around "lock-tie" and "lockout" score targets — the
Watson paper shows these off-the-obvious-number bets can carry outsized value
because of discrete tie outcomes.

### 4.3 Generalizing to three (and fewer) players

With three players, `V(...)` must track standing against two opponents at
once — every DD or FJ decision branches into beat-both, beat-one, or
beat-none outcomes. This three-way branching is the central technical
challenge; most public tools, including the pairwise decomposition in
Williams' own three-player tutorial, approximate it rather than solving it
jointly. Two-player and one-player modes are degenerate cases of the same
state representation, so the engine should be built once for N players and
specialized for N = 1, 2, 3.

## 5. Proposed architecture (draft)

- **Language:** Python.
- **Core:** an N-player game-state simulator plus a Monte Carlo win-probability
  estimator, calibrated on per-round/per-row accuracy rates and empirical
  opponent-wagering distributions.
- **Two consumer layers:** the closed-form heuristic module (section 3.1,
  3.2 rules) and the simulation-backed optimizer (section 3.3, 4.2), with the
  optimizer used to validate the heuristics and to produce the white paper's
  quantitative claims.
- **Validation:** reproduce the Tesauro et al. headline numbers (DD accuracy
  by row, human wager conservatism, two-thirds threshold) as a calibration
  check before trusting the model's three-player extensions.

## 6. Open questions and risks

See `RISK_REGISTER.md` at the project root for the tracked version. Draft
entries:

1. Data licensing limits what can appear in shipped artifacts (see section 2).
2. Real confidence is unobservable in historical data; the tool likely needs
   a self-reported confidence input rather than a purely inferred one.
3. Live in-game assistance would break contest rules; scope this as a study
   and post-game analysis tool only.
4. Pairwise heuristic decomposition for three players is an approximation,
   not a proven joint optimum; needs empirical validation against the full
   simulator.

## 7. Status (updated 2026-07-23)

Done:

1. Scope confirmed: FJ first, since its guarantee-based math needs no
   confidence/probability inputs ("more fixed"). Data-source approach
   (ADR-0001) accepted.
2. `engine/fj_wager.py` (Tier 1, guarantee-based FJ) built and tested.
3. `engine/fj_bestresponse.py` (Tier 2, confidence- and opponent-model-based
   FJ) built and tested. See ADR-0002 for the opponent-model assumptions.
4. `engine/simulate.py` and `engine/dd_wager.py` (Daily Double, Monte Carlo)
   built and tested.
5. 26 tests passing across all four modules.

Still open:

1. Full project scaffold (README, LICENSE, SECURITY.md, CONTRIBUTING.md,
   CI) -- not started; CI specifically needs a GitHub remote, which isn't
   connected yet.
2. Calibrate the Tier 2 / DD engines' placeholder constants against
   Tesauro et al.'s full published tables (ADR-0002, risk #5).
3. Write the white paper, deck, and Diátaxis technical docs once the
   engines are calibrated and validated, not just directionally correct.
4. Git: one local commit exists; further commits are blocked by a sandbox
   quirk (see CHANGELOG 0.2.0 notes) until Will clears it on his end.

Future ideas (not built, just logged):

1. Surface "mathematically eliminated" rivals explicitly in the app UI --
   e.g., "Rival 2's score doesn't affect this wager." The underlying math
   in `fj_wager.py` already ignores such rivals correctly (it only ever
   looks at the single highest opponent ceiling, never a sum or average
   across all opponents) -- see white paper section 4.4 for the full
   explanation. This would be a usability enhancement, not a math fix.

## Sources

- Tesauro, G., Gondek, D., Lenchner, J., Fan, J., & Prager, J. M. (2013).
  Analysis of Watson's strategies for playing Jeopardy!. Journal of
  Artificial Intelligence Research, 47, 205–251.
  https://doi.org/10.1613/jair.3834 (preprint: https://arxiv.org/pdf/1402.0571)
- Williams, K. "How to wager in Final Jeopardy!" The Final Wager.
  https://thefinalwager.wordpress.com/tutorial/
- Dupée, M. (1998). How to Get on Jeopardy!—and Win! Citadel Press.
  (Cited from Tesauro et al., 2013; not read directly.)
- jwolle1. jeopardy_clue_dataset. GitHub.
  https://github.com/jwolle1/jeopardy_clue_dataset
- J! Archive Wagering Calculator. https://j-archive.com/wageringcalculator.php
