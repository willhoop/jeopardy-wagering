# ADR-0001: Data source strategy for calibration and validation

Status: accepted
Date: 2026-07-23 (accepted 2026-07-23 — Will had no strong preference and
deferred to this recommendation)

## Context

The model needs two things from historical Jeopardy! data: (1) aggregate
statistics to calibrate the win-probability engine (DD accuracy by round and
row, human FJ wagering distributions by rank), and (2) a way to validate that
the engine's predictions match real outcomes.

J-Archive's site terms forbid scraping, republishing, or monetizing its
content. The most complete derived dataset available, jwolle1's
`jeopardy_clue_dataset` on GitHub (538,845 clues, with Daily Double wager
amounts and round-end scores), carries its own restriction: its README says
not to use the data "to make a public-facing web site, app, or any other
product," and the source prefers not to be credited.

Tesauro et al. (2013), published in the Journal of Artificial Intelligence
Research, mined roughly 3,000 J-Archive episodes and published the resulting
aggregate statistics (DD accuracy by row, human wager distributions, etc.) as
part of a peer-reviewed paper. These are citable published findings, not raw
scraped data, and carry no reuse restriction.

## Decision

- Do not scrape J-Archive directly.
- Use the Tesauro et al. published statistics as the calibration source for
  anything that ships: the white paper, the deck, the technical docs, and any
  numbers quoted in the tool's output.
- Use the jwolle1 dataset only inside the internal validation harness (tests,
  simulator calibration checks) and never surface raw rows, aggregate tables
  derived directly from it, or the dataset itself in a shipped artifact.
- If a shipped artifact needs a statistic the paper does not cover, generate
  it from our own simulation rather than from the restricted dataset, and
  label it clearly as simulated, not historical.

## Consequences

- The white paper's data appendix will cite one peer-reviewed source instead
  of a larger raw dataset, which narrows what we can claim with historical
  backing. Flag any claim that isn't in the paper as "simulated" rather than
  "observed."
- Internal validation can still be strong, since the jwolle1 dataset remains
  usable for testing and calibration — it just cannot appear in outputs.
- If Will wants richer historical detail in the shipped product later, this
  ADR should be revisited — for example, by seeking direct permission from a
  data holder, or by running our own compliant, permitted data collection.
