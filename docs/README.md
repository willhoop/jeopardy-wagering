# Documentation index

This project's documentation follows the [Diátaxis](https://diataxis.fr/)
framework: four kinds of document, each with a different job. Technical docs
are written in ASD-STE100 Simplified Technical English (short sentences,
active voice, one meaning per word).

## Start here

- **New to the tool?** Read the tutorial:
  [`tutorial/getting-started.md`](tutorial/getting-started.md).
- **Want the math and the "why"?** Read the white paper:
  [`white-paper.md`](white-paper.md).

## Tutorial — learning-oriented

- [`tutorial/getting-started.md`](tutorial/getting-started.md) — a first
  session with known, reproducible expected numbers you can check against.

## How-to guides — task-oriented

- [`how-to/get-a-wager-recommendation.md`](how-to/get-a-wager-recommendation.md)
- [`how-to/practice-with-quiz-mode.md`](how-to/practice-with-quiz-mode.md)
- [`how-to/maintain-the-project.md`](how-to/maintain-the-project.md)

## Reference — information-oriented

- [`reference/engine-api.md`](reference/engine-api.md) — every public
  function and dataclass in `engine/`, with parameter and return-value tables.

## Explanation — understanding-oriented

- [`white-paper.md`](white-paper.md) — the full research, math, and
  methodology.
- [`explanation/tiers-explained.md`](explanation/tiers-explained.md) — a
  plain-language companion to the white paper's Tier 1 / Tier 2 discussion.
- [`explanation/wagering-theory-research.md`](explanation/wagering-theory-research.md)
  — the original research memo the white paper consolidates.

## Decision records and reviews

- [`adr/0001-data-source-strategy.md`](adr/0001-data-source-strategy.md)
- [`adr/0002-opponent-model-assumptions.md`](adr/0002-opponent-model-assumptions.md)
- [`reviews/statistical-review-2026-07-23.md`](reviews/statistical-review-2026-07-23.md)
  — first statistical review (Daily Double selection + strict-win tiebreak).
- [`reviews/statistical-review-2026-07-23-v2.md`](reviews/statistical-review-2026-07-23-v2.md)
  — referee-style second review (CRN-aware comparison variance + multiplicity).

## Presentation

- [`deck.pptx`](deck.pptx) — a 12-slide plain-English overview; links the
  white paper on the last slide.

## Generated PDFs

Every Markdown document here has a PDF companion in
[`../build/`](../build/). The Markdown is the source of truth; regenerate the
PDF in the same pass when the source changes (see
[`how-to/maintain-the-project.md`](how-to/maintain-the-project.md)).
