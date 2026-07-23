# Security Policy

## Scope

This is a personal research and practice-tool project. It has no server,
no database, no user accounts, and no network calls of its own — the
`app/index.html` trainer runs entirely client-side in a browser, and the
`engine/` Python code runs locally. The realistic attack surface is small:
mainly the risk of a dependency or a copy-pasted code snippet introducing a
problem.

## Reporting a vulnerability

If you find a security issue (for example, something that could execute
unexpected code when `app/index.html` is opened, or an unsafe dependency in
the Python engine), email **willjhooper@msn.com** with a description and
steps to reproduce. This is a solo personal project, so please allow a
reasonable amount of time for a response -- there's no dedicated security
team behind it.

## Data handling

- The trainer's Quiz Mode stores a score/streak counter in the browser's
  `localStorage`. That's the only persisted data in this project, and it
  never leaves the browser.
- No scores, wagers, or personal information are transmitted anywhere.
- No historical Jeopardy! data is scraped, stored, or shipped by this
  project -- see `docs/adr/0001-data-source-strategy.md` for why.
