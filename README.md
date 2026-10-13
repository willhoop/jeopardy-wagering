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
| `app/index.html` | Interactive browser trainer: calculators + a graded quiz mode. Live at <https://willhoop.github.io/jeopardy-wagering/app/>, or open the file directly in any browser, no server needed. |
| `engine/` | The Python engine the trainer's logic is based on: `fj_wager.py` (Tier 1, guarantee-based), `fj_bestresponse.py` (Tier 2, confidence-weighted), `simulate.py` + `dd_wager.py` (Daily Double, Monte Carlo). |
| `engine/behavior.py` | Simulated contestant behavior and the tie rule, in one configuration block: role-based Final Jeopardy wager mixes, published accuracy rates, correlated right/wrong outcomes. Each value is marked PUBLISHED or ASSUMED. |
| `tests/` | 43 Python tests, plus `js_parity.js`, which checks the app's JavaScript engine against the same hand-derived values. Hand-derived expected values where possible; invariant checks where Monte Carlo output can't be hand-derived. CI (`.github/workflows/ci.yml`) runs both on every push and pull request. |
| `docs/white-paper.md` | The full research, math, and methodology writeup. Start here to understand *why*, not just *what*. |
| `docs/deck.pptx` | A plain-English overview, no math required. Links `white-paper.md` on the last slide. |
| `docs/tutorial/`, `docs/how-to/`, `docs/reference/`, `docs/explanation/` | Task-oriented documentation ([Diátaxis](https://diataxis.fr/) structure), written in ASD-STE100. |
| `docs/adr/` | Architecture decision records — the reasoning behind data-sourcing and opponent-model choices. |
| `docs/adr/0003-simulated-contestant-behavior.md` | The current opponent model and tie rule: sources, decision, and negative consequences. Supersedes ADR-0002. |
| `RISK_REGISTER.md` | Open risks and known limitations, tracked live. |
| `CHANGELOG.md` | Every change, in [Keep a Changelog](https://keepachangelog.com/) format. |
| `build/` | Generated PDF copies of every doc, and `md_to_pdf.py`, the script that builds them. Markdown is the source of truth; regenerate the PDF if the source changes. |
| `llms.txt` | A short summary and links for AI agents ([llmstxt.org](https://llmstxt.org/) format). |

## Quick start

Open the trainer at <https://willhoop.github.io/jeopardy-wagering/app/>,
or open `app/index.html` locally.

Run the tests:

```bash
cd tests
python -m pytest
cd ..
node tests/js_parity.js
```

Read the theory first if you want to understand the math before using the
tool: `docs/white-paper.md` (or its PDF twin in `build/`).

## Two ways every wager is calculated

1. **Safe Bet (Tier 1)** — the wager that can't hurt you if you're right,
   assuming every opponent plays the worst realistic case against you. No
   confidence estimate needed.
2. **Smart Bet (Tier 2 / Daily Double engine)** — factors in your actual
   confidence and plays you against simulated contestants to maximize your
   real win chance. A tie for first goes to a tiebreaker clue (the rule
   since November 2014), so it counts as half a win. The opponent model
   draws on a published study of real games (Tesauro et al., 2013) for
   accuracy, the correlation of right/wrong answers, and second place's
   wager mix in one score regime; the rest are labeled assumptions — see
   `docs/adr/0003-simulated-contestant-behavior.md`.

## Status

Engine and tests: validated by hand-derived cases, with CI on every push.
Tier 2 opponent model: partly calibrated to published data, partly
assumed. See `RISK_REGISTER.md` for what is proven versus assumed, and
`CHANGELOG.md` for what shipped when.

## License

MIT — see `LICENSE`.
