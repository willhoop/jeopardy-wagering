# Explanation: Why Two Wager Tiers Exist

This page explains the idea behind Safe Bet and Smart Bet. For the full
math, the results and the citations, read `docs/white-paper.md`.

## Two different questions

A wager decision can answer two different questions. This project treats
them as two tools, not one blended answer.

**Question 1: "What wager can't hurt me if I'm right?"**

This question ignores confidence. It assumes that each opponent makes
their most dangerous legal move: they bet everything and answer
correctly. It asks which wager still wins outright. This project calls
the answer **Tier 1**. The app shows it as **Safe Bet**.

**Question 2: "Given how sure I am, what wager gives me the best real
chance to win?"**

This question needs two more inputs: your confidence in the category, and
a model of how opponents wager and answer. This project calls the answer
**Tier 2** for Final Jeopardy and the **Daily Double engine** for a
mid-game Daily Double. The app shows both as **Smart Bet**.

## How ties are scored

Since the 24 November 2014 episode, a tie for first after Final Jeopardy
goes to a tiebreaker clue. Only the winner of that clue returns. Smart Bet
gives each tied player an equal chance in the tiebreaker. A two-way tie
is half a win. A three-way tie is one third of a win. If every player
ends at $0 or less, nobody wins.

Tier 1 does not need this rule. It asks for an outright win.

## Why Safe Bet and Smart Bet can differ

Safe Bet plans for the worst case every time. Smart Bet uses your
confidence and the likely moves of real contestants.

- With low confidence, Smart Bet can recommend less than Safe Bet. A
  large wager loses more when you miss, and most opponents do not bet
  the worst case against you.
- A wager that only ties a rival is worth about half a win. One more
  dollar turns that tie into a win. For this reason, Smart Bet usually
  takes the extra dollar when a tie is in play.

## How Smart Bet models opponents

Smart Bet plays you against **simulated contestants**. The model gives
each opponent a role by score: leader, second place, or third place.
Each role has a mix of bet types, for example "cover the doubled score of
second place" or "bet everything". Some weights come from a published
study of real games (Tesauro et al., 2013). Others are our assumptions.
`engine/behavior.py` marks each value as PUBLISHED or ASSUMED.

Right and wrong answers are correlated across players. A hard clue is
hard for everyone. So when you miss, a rival is more likely to miss too.
The model includes you in this correlation.

`docs/adr/0003-simulated-contestant-behavior.md` gives the sources, the
decision and its negative consequences.

## Why the Daily Double engine gives a range, not one number

A Final Jeopardy wager ends the game. A Daily Double wager changes the
rest of the game: more clues, maybe another Daily Double, then Final
Jeopardy. No exact formula covers this. The engine simulates the rest of
the game thousands of times for each candidate wager. It then counts the
win share of each wager.

Each simulated result has some uncertainty, as a poll has a margin of
error. When the simulation cannot separate some wagers, the app shows a
shaded **plateau** on the chart. The app recommends the smallest wager in
the plateau. The evidence does not support a larger risk.

## What is proven, and what is assumed

The Safe Bet math is fully determined. It needs no assumption about the
accuracy of any player.

Smart Bet and the Daily Double engine need a model of opponents. Part of
that model is published: opponent accuracy, the outcome correlation,
Daily Double accuracy, and the second-place wager mix in one score
regime. The other parts are assumptions: the leader's wager mix, the
second-place mix in the other five regimes, the third-place shape, equal
tiebreaker odds, and the regular-clue model. The published data are from
games played between the mid-1990s and 2012. Treat each Smart Bet
percentage as a model output, not as a validated statistic. See
`RISK_REGISTER.md` (risks #5, #7 and #14).

## Related pages

- `docs/white-paper.md` — the math, the results and the citations.
- `docs/tutorial/getting-started.md` — see both tiers in the app.
- `docs/reference/engine-api.md` — the functions behind these ideas.
- `docs/adr/0003-simulated-contestant-behavior.md` — the opponent model.
