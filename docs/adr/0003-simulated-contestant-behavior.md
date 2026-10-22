# ADR-0003: Simulated contestant behavior and the tiebreaker rule

Status: accepted. Supersedes ADR-0002. Its accuracy, correlation, leader-cover
and Daily Double values are superseded by ADR-0004 (modern-era calibration).
Date: 2026-10-13

## Context

Two defects in the Tier 2 and Daily Double engines surfaced on 2026-10-13.

1. **Wrong tie rule.** The engines counted a tie for first as a full win,
   on the grounds that co-champions both return. That rule ended with the
   24 November 2014 episode. Since then, a tie for first after Final
   Jeopardy is settled by a tiebreaker clue, and only one player returns
   ([Wikipedia, "Jeopardy!"](https://en.wikipedia.org/wiki/Jeopardy!), rules section;
   date from the [Jeopardy! History Wiki, Season 31](https://jeopardyhistory.fandom.com/wiki/Jeopardy!_Timeline_(syndicated_version)/Season_31),
   show #6946). The change followed the October 2014 co-champion ties; it
   was formally announced in 2016, and the first regular-play tiebreaker
   came in 2018 ([McNear, The Ringer, 2021](https://www.theringer.com/2021/01/23/tv/jeopardy-tiebreaker-scenario-rules-changes)).
   The visible symptom: for a leader whose cover bet was $6,001, Smart Bet
   recommended $6,000 — a bet that only ties second place if they double
   up. Under the real rule that tie is worth about half a win.
2. **Placeholder opponents.** ADR-0002 shipped a uniform split over each
   opponent's own Tier 1 breakpoints, at 50% accuracy, independent across
   players. It was labeled as a placeholder. Tesauro et al. (2013, JAIR
   47:205-251) publish enough about real contestant behavior to do better.

## Decision

All values live in one configuration block in `engine/behavior.py`,
mirrored in the `BEHAVIOR` object in `app/index.html`.

**Scoring.** A player's result is a *win share*: 1 for an outright win,
1/k for a k-way tie for first (equal tiebreaker odds, assumed), 0
otherwise. Nobody wins if the top score is $0 or less.

**Opponent wagers.** Each opponent is assigned a role by score: leader (A),
second (B), third (C).

| Role | Bet types and weights | Source |
|---|---|---|
| B | all-in 26%, keep C out (bet < B-2C, or cover 2C-B+1) 27%, overtake A (A-B+1) 15%, two-thirds (3B-2A-1) 8%, random 24% | PUBLISHED for the regime B ≥ ¾A and B ≥ 2C (T13 §2.3). The "cover 2C-B+1" branch is an ASSUMED extension (it applies only when B < 2C, outside the published regime). ASSUMED for the other five regimes. |
| A, not locked | cover 2B-A+1 75%, tie-cover 2B-A 10%, all-in 5%, random 10% | ASSUMED. T13 §1.1 says A "usually" covers, "frequently" 2B-A+1, with no split. |
| A, lockout (A > 2B) | $0 50%, largest safe bet A-2B-1 50% | ASSUMED. |
| C | even spread over the random grid | PUBLISHED that T13 found no evidence that C's bets track the game state (T13 §2.3 note 5). The even spread is ASSUMED. |

"Random" is an equal spread over 0, ¼, ½, ¾ and all of the score. When a
bet type does not exist in a state (for example, no third player to keep
out), its weight is shared out in proportion among the others.

**Accuracy.** Opponents answer Final Jeopardy right 50% of the time
(PUBLISHED, average contestants, T13 §2.3; champions 60%). Right/wrong
outcomes are correlated across all players at 0.3 (PUBLISHED, T13 §2.3),
modeled as a one-factor Gaussian copula. We read 0.3 as the binary
correlation at 50% accuracy and convert it with Sheppard's formula to a
latent correlation r = sin(0.3π/2) ≈ 0.454. The user is inside the same
copula: a hard clue is hard for everyone.

**Daily Double.** Future Daily Doubles are answered right 64% of the time
(PUBLISHED, average contestants, T13 §2.2). Inside a rollout, opponents'
Final Jeopardy wagers are drawn from the model above.

**Computation.** Tier 2 is exact: it integrates over the shared factor
(trapezoid rule, step 0.25 on [-6, 6]) and enumerates every wager and
right/wrong branch. The DD engine samples the same model.

## Consequences

Positive:

- Smart Bet no longer recommends a tie-only bet when one more dollar wins.
- Every opponent number is either cited or labeled as an assumption, in
  one place.
- Correlated outcomes capture a real effect: when you miss, a rival is
  more likely to have missed too.

Negative:

- Five of the six B regimes, all of A's split and C's shape are our
  assumptions, not fitted. The published B weights came from groups of
  "only a few hundred samples" each (T13 §2.3), so even those carry wide
  error bars.
- The data are from the mid-1990s to 2012 at the latest. Contestant behavior has
  likely changed since; non-stationarity is not modeled.
- Equal tiebreaker odds is an assumption; buzzer skill decides the clue.
- The paper defines rho on the binary outcomes (T13 §1.1 Glossary:
  rho = P(RR) + P(WW) - P(RW) - P(WR)) and generates it by thresholding
  correlated normals (§2.3). This equals the phi correlation at 50%
  accuracy; at other accuracies the Sheppard conversion is approximate.
- Win percentages from any earlier version are not comparable: they scored
  ties as wins against a different opponent model.
- The app's Daily Double calculation takes about twice as long, because
  each rollout now simulates opponent wagers.
