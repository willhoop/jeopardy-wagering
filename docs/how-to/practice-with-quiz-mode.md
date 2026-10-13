# How To: Practice with Quiz Mode

Use Quiz Mode to drill wager decisions against randomly generated
scenarios, and get graded against the optimal play.

## Steps

1. Open the app (<https://willhoop.github.io/jeopardy-wagering/app/> or
   `app/index.html`). Click the **Quiz Me** tab.
2. Click **New Scenario**. The app shows a random Daily Double or Final
   Jeopardy setup, with scores for you and each rival.
3. Read the scenario text. It states the round, the confidence you should
   assume, and any Daily Double or board-money details that apply.
4. Type your wager in the input box.
5. Click **Lock it in!**.

## How grading works

The app compares your wager's win probability against the optimal
wager's win probability, as a percentage. It converts that percentage
into a letter grade:

| Grade | What it means |
|---|---|
| A+ | Your wager matched the optimal win probability almost exactly. |
| A | Your wager was close to optimal. |
| B | Your wager was solid, but left some win probability on the table. |
| C | Your wager was too cautious for the situation. |
| D | Your wager left a large amount of win probability on the table. |

The reveal screen also shows the curve chart for that scenario, with the
optimal wager marked, so you can see how far your wager sat from the
peak.

## Streaks and scoring

The app tracks a running score, your current streak of A-grade answers
(85% or higher), and your best streak. Reach a 3-answer streak for a
confetti celebration. Your stats are saved in your browser between
visits — they are not sent anywhere.

## Related pages

- `docs/tutorial/getting-started.md` — learn the app's core recommendation
  screens first, if you have not already.
- `docs/how-to/get-a-wager-recommendation.md` — use your own game's real
  numbers instead of a random scenario.
