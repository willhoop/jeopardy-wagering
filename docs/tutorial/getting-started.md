# Tutorial: Get Your First Wager Recommendations

This tutorial shows you how to use the Jeopardy! Wager Trainer for the
first time. You enter one Final Jeopardy scenario and one Daily Double
scenario. Each step gives the wager that the app shows, so you can check
your screen against this page.

## What you need

- A web browser.
- The live app at <https://willhoop.github.io/jeopardy-wagering/app/>, or
  the file `app/index.html` from this project.

The local file needs no internet access and no installation.

## Step 1: Open the app

Open the live app. Or double-click `app/index.html`, or drag it into a
browser window.

You see four tabs at the top: **Daily Double**, **Final Jeopardy**,
**Quiz Me**, and **How This Works**.

## Step 2: Enter a Final Jeopardy scenario

1. Click the **Final Jeopardy** tab.
2. Under "How many players?", click **3 players**.
3. Enter these scores:
   - Your score: **12000**
   - Opponent A score: **8000**
   - Opponent B score: **6000**
4. Set the confidence slider to **50%**.
5. Click **Get my wagers**.

## Step 3: Read the results

The app shows two cards.

**Safe Bet (Tier 1)** shows **$4,001**. This is the smallest wager that
beats each opponent outright if you answer correctly. Opponent A can
reach $16,000 ($8,000 doubled). $12,000 + $4,001 = $16,001, one dollar
more than that worst case.

**Smart Bet (Tier 2)** also shows **$4,001**. Smart Bet uses your
confidence and plays you against simulated contestants. A wager of
$4,000 only ties Opponent A if they double up. A tie goes to a tiebreaker clue,
so it is worth about half a win. The extra dollar turns that tie into a
win, so Smart Bet takes it.

The Smart Bet card also shows a win chance. The chart under the cards
shows the win chance for each wager. For the meaning of these
percentages, read the Tier 2 section of `docs/white-paper.md`.

Move the confidence slider to **90%**. Click **Get my wagers** again.
Smart Bet still shows **$4,001**, but the win chance goes up. Here, higher
confidence does not change the wager. It changes how good that wager is.

## Step 4: Enter a Daily Double scenario

1. Click the **Daily Double** tab.
2. Under "Round", click **Double Jeopardy**.
3. Under "How many rivals are in the game?", click **2 rivals**.
4. Enter these scores:
   - Your score: **4000**
   - Rival 1 score: **6000**
   - Rival 2 score: **3000**
5. Set "Daily Doubles still hidden after this one" to **None — this is
   the last one**.
6. Set "Money still in play on the board" to **Exact amount…** and type
   **0**.
7. Set the confidence slider to **70%**.
8. Click **Crunch the numbers**.

## Step 5: Read the Daily Double result

The app recommends **$4,000**. This is your full score and the legal
maximum here. Below the recommendation, you see a curve of win chance
against wager.

In this scenario, no other wager is close to the best one, so the chart
shows no shaded band. In other scenarios, the chart shows a gold shaded
band. This band is the **plateau**: the simulation cannot separate the
wagers inside it. The app then recommends the smallest wager in the band,
because a larger wager in the band buys nothing that the simulation can
detect. A wide band is expected behavior, not an error.

## What you learned

- Safe Bet (Tier 1) needs no confidence number. It guarantees a win if
  you answer correctly, against the worst case of each rival.
- Smart Bet (Tier 2) and the Daily Double engine use your confidence and
  simulated contestants to find the wager with the best win chance.
- A tie for first is worth about half a win, because a tiebreaker clue
  decides it.
- The Daily Double engine runs a simulation. When several wagers are too
  close to separate, it shows a plateau and recommends the smallest one.

## Next steps

- Try the **Quiz Me** tab: see `docs/how-to/practice-with-quiz-mode.md`.
- Enter your own game's scores: see
  `docs/how-to/get-a-wager-recommendation.md`.
- Read the math and the results: `docs/white-paper.md`.
