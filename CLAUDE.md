# CLAUDE.md — working memory for this project

Read this first. It's a fast-orientation file for an AI agent (or Will)
picking this project back up, not a replacement for the real docs.

## What this project is

A wagering-strategy model and practice tool for Jeopardy!'s Daily Double
and Final Jeopardy decisions. 3-player primary case; 2 and 1 players are
reduced cases of the same model. Full explanation: `docs/white-paper.md`.

## Two-tier design (memorize this, it comes up everywhere)

- **Tier 1** (`engine/fj_wager.py`) — worst-case guarantee, no confidence
  input needed. "What wager can't hurt me if I'm right?"
- **Tier 2** (`engine/fj_bestresponse.py` for FJ; `engine/simulate.py` +
  `engine/dd_wager.py` for Daily Double) — confidence-weighted, uses a
  placeholder opponent-behavior model (documented, not fitted to real data
  yet — ADR-0002). "Given my real confidence, what maximizes my win odds?"

Ties for first place count as wins in Tier 2 (matches the actual show
rule); Tier 1 requires an outright beat. This is *why* Tier 2 sometimes
recommends a smaller wager than Tier 1 for the same scoreline — not a bug.

## Known gotchas

- **Git is stuck in this exact folder.** A lock file got wedged during an
  earlier session because sandboxed tools couldn't delete files inside the
  synced Projects folder. One commit exists (`5c83b5b`). To fix: delete the
  `.git` folder here and run `git init` again — this works fine on Will's
  real machine, the restriction was sandbox-specific.
- **No GitHub remote is connected.** The `engineering:github` MCP connector
  needs authorization before any push is possible.
- **`app/index.html` is a hand-written JS port of the Python engine.** It
  is *not* covered by the automated test suite. If you change the Python
  engine, you must manually update the JS and re-verify it (see
  `CONTRIBUTING.md` step 4). This is risk #8 in `RISK_REGISTER.md`.
- **Never use the jwolle1 historical dataset (or anything scraped from
  J-Archive) in a shipped artifact.** Internal validation only, if at all.
  See ADR-0001.
- **Every doc gets a PDF companion in `build/`,** generated with pandoc +
  pdflatex. Regenerate the PDF in the same pass as any Markdown edit — see
  the note in `CHANGELOG.md` 0.4.1 for the exact command pattern and a
  Unicode gotcha (U+2212 minus signs break pdflatex; use plain hyphens).

## Commands

```bash
# Run tests
cd tests && python3 -m pytest -v

# Rebuild a doc's PDF (adjust paths/title)
pandoc docs/white-paper.md -o build/white-paper.pdf \
  --toc --toc-depth=2 -V geometry:margin=1in -V colorlinks=true -V linkcolor=blue \
  --highlight-style=tango --pdf-engine=pdflatex \
  --pdf-engine-opt=-interaction=nonstopmode --pdf-engine-opt=-halt-on-error \
  -V title="Doc Title"
```

## Where things stand (see CHANGELOG.md for the authoritative, dated version)

Done: Tier 1 + Tier 2 FJ engines, Daily Double Monte Carlo engine, 26
tests, the interactive app, the white paper, both ADRs, the risk register,
PDF companions for all docs, README/LICENSE/SECURITY/CONTRIBUTING/this
file.

Not done: the plain-English deck, the Tutorial/How-to/Reference Diátaxis
docs, `check_projects.py`, working git/CI in this folder.
