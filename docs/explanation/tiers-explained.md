# Explanation: Why Two Wager Tiers Exist

This page explains the idea behind Safe Bet and Smart Bet, in plain
language. For the full math, worked proofs, and citations, read
`docs/white-paper.md`.

## Two different questions

A wager decision can answer two different questions. This project treats
them as separate tools, not one blended answer.

**Question 1: "What wager can't hurt me if I'm right?"**

This question ignores confidence entirely. It asks: assuming every
opponent plays their single most threatening legal move — betting
everything and answering correctly — what wager still keeps me safe? This
project calls the answer **Tier 1**, shown in the app as **Safe Bet**.

**Question 2: "Given how sure I actually am, what wager gives me the best
real chance to win?"**

This question needs two more pieces of information: your own confidence
in the category, and some sense of how opponents tend to wager and
answer. This project calls the answer **Tier 2** for Final Jeopardy, and
the **Daily Double engine** for a mid-game Daily Double. The app shows
this as **Smart Bet**.

## Why Safe Bet can recommend more money than Smart Bet

Safe Bet has to plan for the worst realistic case, every time. Smart Bet
gets to use your actual confidence, and it counts a tie for first as a
win — matching the real show rule that co-champions both advance to the
next game. A wager that only ties an opponent's worst case can be exactly
as good, in real win probability, as a much larger wager that beats it
outright.

## Why the Daily Double engine gives a range, not one number

A Final Jeopardy wager only affects the next thirty seconds. A Daily
Double wager affects the rest of the game — more clues, maybe another
Daily Double, then Final Jeopardy after all of that. There is no clean,
exact formula for that. Instead, the engine simulates the rest of the
game forward, thousands of times, for each candidate wager, and counts
how often each one wins.

Every simulated result carries some uncertainty, the same way a poll of
1,000 people carries a margin of error. When several wagers are close
enough that the simulation cannot tell them apart, the app shows this
honestly as a shaded **plateau** on the chart, instead of picking one
number that looks precise but is not. The app always recommends the
smallest wager in that plateau — there's no reason to risk more money
than the evidence supports.

## What is proven, and what is a placeholder

The Safe Bet math is fully determined. It needs no assumption about
anyone's odds of being correct, so there is nothing to calibrate.

Smart Bet and the Daily Double engine both need a guess at how opponents
behave — how often they get a clue right, and how they tend to size their
own wagers. This project uses clearly labeled placeholder numbers for
that guess, not numbers fitted to real historical games. The *shape* of
the advice (do not overbet past the point of no added benefit; prefer
smaller wagers among ties) holds regardless. The *exact* win-probability
numbers should not be quoted as validated statistics yet. See
`docs/adr/0002-opponent-model-assumptions.md` and `RISK_REGISTER.md`.

## Related pages

- `docs/white-paper.md` — full math, proofs, and citations.
- `docs/tutorial/getting-started.md` — see both tiers in action with known
  numbers.
- `docs/reference/engine-api.md` — the exact functions behind these ideas.
