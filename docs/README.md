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
  session, with the wagers that the app shows at each step.

## How-to guides — task-oriented

- [`how-to/get-a-wager-recommendation.md`](how-to/get-a-wager-recommendation.md)
- [`how-to/practice-with-quiz-mode.md`](how-to/practice-with-quiz-mode.md)
- [`how-to/maintain-the-project.md`](how-to/maintain-the-project.md)

## Reference — information-oriented

- [`reference/engine-api.md`](reference/engine-api.md) — each public
  function, constant and dataclass in `engine/` (including the simulated
  contestant behavior in `behavior.py`), with parameter and return-value
  tables.

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
  — superseded by ADR-0003; kept as the historical record.
- [`adr/0003-simulated-contestant-behavior.md`](adr/0003-simulated-contestant-behavior.md)
  — the tiebreaker rule and the simulated opponents of Tier 2 and the
  Daily Double engine.
- [`reviews/statistical-review-2026-07-23.md`](reviews/statistical-review-2026-07-23.md)
  — first statistical review (Daily Double wager selection, and the
  strict-win tiebreak that 2.0.0 removed).
- [`reviews/statistical-review-2026-07-23-v2.md`](reviews/statistical-review-2026-07-23-v2.md)
  — referee-style second review (CRN-aware comparison variance + multiplicity).

## Presentation

- [`deck.pptx`](deck.pptx) — a plain-English overview. The last slide
  links the white paper.

## Generated PDFs

Each Markdown document here has a PDF companion in
[`../build/`](../build/). The Markdown is the source of truth. When the
source changes, regenerate the PDF in the same pass with
`python build/md_to_pdf.py <source.md> build/<name>.pdf` (see
[`how-to/maintain-the-project.md`](how-to/maintain-the-project.md)).
