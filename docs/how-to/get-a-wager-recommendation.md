# How To: Get a Wager Recommendation for Your Own Game

Use this guide when you know the app and want to enter the numbers of
your own game. If this is your first time, read
`docs/tutorial/getting-started.md` first.

## How to get a Daily Double recommendation

1. Open the app (<https://willhoop.github.io/jeopardy-wagering/app/> or
   `app/index.html`). Click the **Daily Double** tab.
2. Set the round: **Single Jeopardy** or **Double Jeopardy**.
3. Set the number of rivals: **Solo practice**, **1 rival**, or
   **2 rivals**.
4. Enter your score and each rival's score.
5. Set "Money still in play on the board." Pick a value from the list.
   If your amount is not on the list, choose **Exact amount…** and type
   the number.
6. Set "Daily Doubles still hidden after this one":
   - In Single Jeopardy, this is always **None**. There is only one Daily
     Double in that round.
   - In Double Jeopardy, choose **None** if this is the second Daily
     Double, or **One more out there** if it is the first.
7. Move the confidence slider to match how sure you are about the
   category. Read the label under the slider for a plain-language check.
8. Click **Crunch the numbers**.

The app shows your recommended wager, the estimated win rate at that
wager, and a curve chart. If the chart shows a shaded band, the
simulation cannot separate the wagers in that band. This is expected.
The recommendation is the smallest wager in the band. Exception: wagers
that give exactly the same result in every simulated game (for example,
in **Solo practice**) are chosen by money. If your confidence is above
50%, the app recommends the largest of them.

## How to get a Final Jeopardy recommendation

1. Open the app and click the **Final Jeopardy** tab.
2. Set the number of players: **Just you**, **2 players**, or
   **3 players**.
3. Enter your score and each opponent's score.
4. Move the confidence slider to match your confidence in the category.
5. Click **Get my wagers**.

The app shows two cards side by side:

- **Safe Bet (Tier 1)** — the wager that guarantees a win if you answer
  correctly. It does not use your confidence. Use it when you want the
  guaranteed-safe answer, or when you have no read on the category.
- **Smart Bet (Tier 2)** — the wager with the best win chance, given your
  confidence and simulated contestants as opponents. With low confidence
  it can recommend less money than Safe Bet. A tie for first counts as
  half a win, because a tiebreaker clue decides it (rule since November
  2014). When several wagers give the same win chance, Smart Bet picks
  the one with the most expected money. For example, with **Just you** and
  high confidence, it recommends that you bet everything.

## How to read the curve chart

Every result screen shows one curve: win probability against wager size.

- The gold dot marks the recommended wager.
- A shaded band, when present, marks the Daily Double engine's plateau —
  wagers that are statistically too close to call apart.
- The caption under the chart states what the shape means for your
  numbers.

## Related pages

- `docs/tutorial/getting-started.md` — a full walkthrough with the
  wagers that the app shows.
- `docs/explanation/tiers-explained.md` — why two different tiers exist.
- `docs/reference/engine-api.md` — the functions behind these numbers.
- `docs/white-paper.md` — the math and the results.
