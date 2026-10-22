# ADR-0004: Private calibration to modern-era play

Status: accepted. Amends ADR-0001. Supersedes the accuracy, correlation,
leader-cover and Daily Double values of ADR-0003.
Date: 2026-10-13

## Context

ADR-0003 calibrated the simulated contestants to Tesauro et al. (2013),
whose data covers the mid-1990s to 2012 at the latest. Will pointed out that
wagering strategy and board play changed radically in the 2010s: players
now jump to high-value clues to hunt Daily Doubles, and they bet them far
harder. Behavior from before that shift is out of date.

No peer-reviewed or freely reusable source publishes modern-era
statistics. J! Archive publishes per-season Daily Double and Final
Jeopardy! statistics, but its terms of use forbid scraping and forbid
republishing "data provided by J! Archive and collected or derived from
J! Archive". Published articles that quote modern figures (for example,
FiveThirtyEight, 2019) also took them from J! Archive.

## Decision

Will's decision: use J! Archive's data to calibrate the model, but publish
none of it.

- Read J! Archive's per-season statistics pages by hand, one page per
  season, for Seasons 38-41 (2021-2025). No scraping and no bulk download.
- Keep the source statistics in `data/private/`, which `.gitignore`
  excludes. They are never committed, quoted or tabulated in any document.
- Use them to set these model values in `engine/behavior.py`, marked
  CALIBRATED:
  - Final Jeopardy accuracy by score rank, and overall.
  - The correlation of right/wrong outcomes across players.
  - The leader's share of bets that cover second place.
  - Daily Double accuracy, wager fraction by round, and who finds a future
    Daily Double, by score rank.
- Keep Tesauro et al. (PUBLISHED) only where no modern statistic exists:
  second place's wager mix, and the shape of third place's bets.
- Documents describe what was calibrated and why, never the source figures.
- Future Daily Doubles now fall at a random point among the remaining clues
  instead of after all of them, because modern players find them early.

## Consequences

Positive:

- The simulated rivals now reflect how the game has been played since the
  Daily Double hunting era began, not how it was played before it.
- Each calibrated value is backed by hundreds of games per season, across
  four seasons.

Negative:

- **Terms-of-use risk, accepted.** The app runs in the browser, so the
  calibrated values are visible in its public source and in
  `engine/behavior.py`. A strict reading of J! Archive's terms could treat
  rounded model settings as "data derived from J! Archive". We publish no
  statistics, tables or quotes, and we would remove the values on a
  takedown request (the terms require a response to such requests). The
  terms also bar "otherwise systematically collect[ing]" data, not only
  automated scraping. We accept, as part of this risk, the interpretation
  that reading four season pages by hand for private calibration is
  allowed.
- **Not reproducible by readers.** A reader cannot check a calibrated value
  against its source in this repository. The method is described; the data
  is not shipped.
- **Second place is still pre-2013.** The biggest behavioral component in
  Final Jeopardy, second place's bet mix, has no modern source.
- **Score rank by proxy.** "Who finds a Daily Double" is reported by
  lectern, not score rank. The returning champion's lectern stands in for
  the leader.
- **Some tournament games are mixed in.** Each season page covers every game
  that season, including in-season tournaments such as the Tournament of
  Champions. Only the leader-cover share is from regular play alone.
  Tournament players face different incentives and are stronger than average.
  Jeopardy! Masters is archived separately and was not used.
- **Finishing place is not used.** Accuracy by finishing place is biased
  (answering right moves you up), so accuracy comes from response patterns
  by score position entering Final Jeopardy instead.
- The ADR-0003 copula reads the correlation as a binary correlation at 50%
  accuracy. Modern accuracy is below 50%, so the conversion is approximate.
