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
goes to a tiebreaker clue (sources: Wikipedia, "Jeopardy!", rules section;
Jeopardy! History Wiki, Season 31 timeline). Only the winner of that clue returns. Smart Bet
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
- Often a range of wagers gives the same win chance. Then Smart Bet uses
  a second rule: it picks the wager in the range that wins the most money
  on average. The winner keeps their final total, so money is the fair
  tiebreak. Example: you have $12,000, and your rivals have $8,000 and
  $6,000. Safe Bet is $4,001. At 50%, 70% or 90% confidence, every
  wager from $4,001 to $4,499 gives the same win chance, so Smart Bet
  recommends $4,499.

## Why Smart Bet uses money to break ties

Before version 2.2, Smart Bet took the smallest of the tied wagers. A
user found the problem: in a solo game at 100% confidence, Smart Bet
said $0. A solo player always wins, so every wager tied, and the
smallest was $0. But the player keeps the money. So Smart Bet now ranks
wagers by win chance first and money second. The same rule makes a
leader who is locked out and sure of the answer bet big.

## How Smart Bet models opponents

Smart Bet plays you against **simulated contestants**. The model gives
each opponent a role by score: leader, second place, or third place.
Each role has a mix of bet types, for example "cover the doubled score of
second place" or "bet everything".

The simulated contestants play like contestants from recent seasons
(Seasons 38-41, 2021-2025). Play changed in the 2010s: players now jump
to high-value clues to hunt Daily Doubles, and they bet them hard. A
model of older games does not show this. So the model is calibrated to
the modern era:

- The leader almost always bets to cover second place.
- Players who are in front answer Final Jeopardy correctly more often
  than players behind them.
- Future Daily Doubles can fall at any point in the rest of the round.
  Leaders find them more often, and finders bet a large part of their
  score.

Second place's wager mix has no modern source. It still comes from a
published study of pre-2013 games (Tesauro et al., 2013). That study
found no evidence that third place's bets track the scores, so the model
spreads them evenly (an assumption).
`engine/behavior.py` marks each value as CALIBRATED, PUBLISHED or
ASSUMED.

The calibration used season statistics from J! Archive. Its terms of use
forbid republishing data from it. So no document in this project gives
the source statistics or the calibrated values. The values are in
`engine/behavior.py` only.

Right and wrong answers are correlated across players. A hard clue is
hard for everyone. So when you miss, a rival is more likely to miss too.
The model includes you in this correlation.

`docs/adr/0003-simulated-contestant-behavior.md` and
`docs/adr/0004-modern-era-calibration.md` give the sources, the decisions
and their negative consequences.

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

One case is different. Some wagers give exactly the same result in every
simulated game, for example in a solo game. More simulation cannot
separate them. For these exact ties, the engine picks by money: if you
are more likely right than wrong, it recommends the largest of them.

## What is proven, and what is assumed

The Safe Bet math is fully determined. It needs no assumption about the
accuracy of any player.

Smart Bet and the Daily Double engine need a model of opponents. Part of
that model is calibrated to modern-era play: Final Jeopardy accuracy by
score rank, the outcome correlation, the leader's cover share, Daily
Double accuracy, the Daily Double wager size and who finds a Daily
Double. Part is published from older games (pre-2013): the
second-place wager mix in one score regime. The other parts are
assumptions: the split of the leader's bets, the second-place mix in the
other five regimes, the third-place shape, equal tiebreaker odds, and
the regular-clue model. A reader cannot check the calibrated values
against their source, because the source data is not published. Treat
each Smart Bet percentage as a model output, not as a validated
statistic. See `RISK_REGISTER.md` (risks #5, #7, #14 and #15).

## Related pages

- `docs/white-paper.md` — the math, the results and the citations.
- `docs/tutorial/getting-started.md` — see both tiers in the app.
- `docs/reference/engine-api.md` — the functions behind these ideas.
- `docs/adr/0003-simulated-contestant-behavior.md` — the opponent model.
- `docs/adr/0004-modern-era-calibration.md` — the modern-era calibration.
