# How To: Get a Wager Recommendation for Your Own Game

Use this guide when you already know the app and want to enter your own
game's numbers. If this is your first time, read
`docs/tutorial/getting-started.md` first.

## How to get a Daily Double recommendation

1. Open `app/index.html` and click the **Daily Double** tab.
2. Set the round: **Single Jeopardy** or **Double Jeopardy**.
3. Set the number of rivals: **0**, **1**, or **2**.
4. Enter your score and each rival's score.
5. Set "Money still in play." Pick a value from the dropdown, in
   thousands. If your exact amount is not on the list, choose **Exact
   amount** and type the precise number.
6. Set "Daily Doubles still hidden after this one":
   - In Single Jeopardy, this is always **None**. There is only one Daily
     Double in that round.
   - In Double Jeopardy, choose **None** if this is the second Daily
     Double, or **One more out there** if it is the first.
7. Move the confidence slider to match how sure you are about the
   category. Read the label under the slider for a plain-language check.
8. Click **Crunch the Numbers**.

The app shows your recommended wager, the estimated win rate at that
wager, and a curve chart. If the chart shows a shaded band, every wager in
that band is close enough that the simulation cannot tell them apart —
this is expected. Bet the smallest wager in the band.

## How to get a Final Jeopardy recommendation

1. Open `app/index.html` and click the **Final Jeopardy** tab.
2. Set the number of players: **1**, **2**, or **3**.
3. Enter your score and each opponent's score.
4. Move the confidence slider to match your confidence in the category.
5. Click **Crunch the Numbers**.

The app shows two cards side by side:

- **Safe Bet (Tier 1)** — the wager that guarantees a win if you answer
  correctly, no matter how confident you are. Use this when you want the
  guaranteed-safe answer, or when you have no real read on the category.
- **Smart Bet (Tier 2)** — the wager that gives the best real win chance,
  given your stated confidence. This can recommend less money than Safe
  Bet, because it also counts a tie for first as a win, matching the
  actual show rule.

## How to read the curve chart

Every result screen shows one curve: win probability against wager size.

- The gold dot marks the recommended wager.
- A shaded band, when present, marks the Daily Double engine's plateau —
  wagers that are statistically too close to call apart.
- The caption under the chart states, in one line, what the shape means
  for your specific numbers.

## Related pages

- `docs/tutorial/getting-started.md` — a full worked walkthrough with
  known expected numbers.
- `docs/explanation/tiers-explained.md` — why two different tiers exist.
- `docs/reference/engine-api.md` — the exact functions behind these
  numbers, for anyone reading or changing the code.
