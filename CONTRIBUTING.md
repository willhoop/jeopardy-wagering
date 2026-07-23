# Contributing

This is currently a solo personal project, but the guidelines below keep it
consistent if that changes.

## Before making a change

Read `docs/white-paper.md` first. It explains the math this project is
built on and which parts are validated versus placeholders. Changes to the
engine should either preserve the existing guarantees (Tier 1) or be
explicit about which assumptions they're changing (Tier 2 / Daily Double).

## Making a change

1. Change the code.
2. Update the relevant docs in the same pass: the white paper if the math
   changed, the ADRs if an assumption changed, the Diátaxis docs
   (`docs/tutorial/`, `docs/how-to/`, `docs/reference/`) if usage changed.
3. Add or update tests. Prefer hand-derived expected values (worked out on
   paper, not copied from the code's own output) wherever the math allows
   it. Where that's not possible (the Monte Carlo Daily Double engine), add
   invariant checks instead -- see `tests/test_dd_wager.py` for examples.
4. If `app/index.html`'s JavaScript logic is touched, re-run the parity
   check against the Python test suite's hand-derived values before
   shipping (there's no automated check for this yet -- see risk #8 in
   `RISK_REGISTER.md`).
5. Add a `CHANGELOG.md` entry: what changed, and why, following [Keep a
   Changelog](https://keepachangelog.com/) format. Bump the version.
6. Regenerate any PDF in `build/` whose Markdown source changed.
7. Run the test suite:

   ```bash
   cd tests
   python3 -m pytest -v
   ```

## Never do this

- Never embed raw rows from a scraped or restricted historical dataset in
  a shipped file -- see `docs/adr/0001-data-source-strategy.md`.
- Never silently rewrite a prior conclusion in the white paper or an ADR.
  Add new information and state what changed and why, so the history stays
  legible.
- Never present a Tier 2 / Daily Double win-probability number as a
  validated statistic without noting the placeholder opponent-model
  assumptions behind it.
