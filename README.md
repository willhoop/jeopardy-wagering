# Jeopardy! Wagering Strategy

A wagering-strategy model and practice tool for Jeopardy!'s two decisions
that carry real stakes: the **Daily Double** and **Final Jeopardy**. Built
for 3-player games, with 2-player and 1-player (solo practice) as reduced
cases of the same model.

Not affiliated with Jeopardy! or Sony Pictures Television. A study and
post-game analysis tool only — not for use during an actual taping.

## What's here

| Path | What it is |
|---|---|
| `app/index.html` | Interactive browser trainer: calculators + a graded quiz mode. Open it directly in any browser, no server needed. |
| `engine/` | The Python engine the trainer's logic is based on: `fj_wager.py` (Tier 1, guarantee-based), `fj_bestresponse.py` (Tier 2, confidence-weighted), `simulate.py` + `dd_wager.py` (Daily Double, Monte Carlo). |
| `tests/` | 30 automated tests. Hand-derived expected values where possible; invariant checks where Monte Carlo output can't be hand-derived. |
| `docs/white-paper.md` | The full research, math, and methodology writeup. Start here to understand *why*, not just *what*. |
| `docs/deck.pptx` | A 12-slide plain-English overview, no math required. Links `white-paper.md` on the last slide. |
| `docs/tutorial/`, `docs/how-to/`, `docs/reference/`, `docs/explanation/` | Task-oriented documentation ([Diátaxis](https://diataxis.fr/) structure), written in ASD-STE100. |
| `docs/adr/` | Architecture decision records — the reasoning behind data-sourcing and opponent-model choices. |
| `RISK_REGISTER.md` | Open risks and known limitations, tracked live. |
| `CHANGELOG.md` | Every change, in [Keep a Changelog](https://keepachangelog.com/) format. |
| `build/` | Generated PDF copies of every doc. Markdown is the source of truth; regenerate the PDF if the source changes. |

## Quick start

Open the trainer:

```
app/index.html
```

Run the tests:

```bash
cd tests
python3 -m pytest
```

Read the theory first if you want to understand the math before using the
tool: `docs/white-paper.md` (or its PDF twin in `build/`).

## Two ways every wager is calculated

1. **Safe Bet (Tier 1)** — the wager that can't hurt you if you're right,
   assuming every opponent plays the worst realistic case against you. No
   confidence estimate needed.
2. **Smart Bet (Tier 2 / Daily Double engine)** — factors in your actual
   confidence and a model of opponent behavior to maximize real win
   probability. The opponent-behavior numbers are labeled placeholders, not
   fitted to real historical data yet — see `docs/adr/0002-opponent-model-assumptions.md`.

## Status

Engine and tests: solid, validated by hand-derived cases. Project scaffold
and Tier 2 calibration: in progress. See `RISK_REGISTER.md` for the current,
honest list of what's proven versus what's still a placeholder, and
`CHANGELOG.md` for what shipped when.

## License

MIT — see `LICENSE`.
