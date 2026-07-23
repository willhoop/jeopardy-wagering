# Tutorial: Get Your First Wager Recommendations

This tutorial shows you how to use the Jeopardy! Wager Trainer for the first
time. You will enter one Final Jeopardy scenario and one Daily Double
scenario. You will see the exact numbers the tool gives back, so you can
check your results against this page.

## What you need

- A web browser.
- The file `app/index.html` from this project.

You do not need internet access. You do not need to install anything.

## Step 1: Open the app

Open `app/index.html` in your browser. Double-click the file, or drag it
into a browser window.

You see four tabs at the top: **Daily Double**, **Final Jeopardy**,
**Quiz Me**, and **How This Works**.

## Step 2: Enter a Final Jeopardy scenario

1. Click the **Final Jeopardy** tab.
2. Set the number of players to **3**.
3. Enter these scores:
   - Your score: **12000**
   - Rival 1: **8000**
   - Rival 2: **6000**
4. Set the confidence slider to **50%**.
5. Click **Crunch the Numbers**.

## Step 3: Read the results

The app shows two cards.

**Safe Bet (Tier 1)** shows **$4,001**. This is the smallest wager that beats
every rival outright, no matter how confident you are. The app picks $4,001
because Rival 1's worst case is $16,000 (their $8,000 doubled), and $12,000 +
$4,001 = $16,001 — one dollar more than that worst case.

**Smart Bet (Tier 2)** shows **$4,000** at 50% confidence, with a win
probability near **78%**. Smart Bet uses your confidence. It found that
$4,000 already reaches the same win probability as $4,001, so it recommends
the cheaper wager.

Move the confidence slider to **90%** and click **Crunch the Numbers**
again. Smart Bet still recommends $4,000, but the win probability rises to
about **96%**. Higher confidence does not change *how much* to bet here — it
changes how good that bet actually is.

## Step 4: Enter a Daily Double scenario

1. Click the **Daily Double** tab.
2. Set the round to **Double Jeopardy**.
3. Set the number of rivals to **2**.
4. Enter these scores:
   - Your score: **4000**
   - Rival 1: **6000**
   - Rival 2: **3000**
5. Set "Daily Doubles still hidden after this one" to **None — this is the
   last one**.
6. Set "Money still in play" to **$0** (Exact amount).
7. Set the confidence slider to **70%**.
8. Click **Crunch the Numbers**.

## Step 5: Read the plateau

The app recommends a wager near **$2,000**, with a win probability near
**45%**. Below the recommendation, you see a curve and a gold shaded band.

The shaded band is the **plateau**. Every wager inside it gives a
statistically similar win chance. The app recommends the smallest wager in
the band, because betting more inside the band buys you nothing extra that
the simulation can detect.

This is expected behavior, not an error. A wide plateau means the decision
is genuinely close between several wager sizes.

## What you learned

- Safe Bet (Tier 1) never needs a confidence number. It guarantees a win if
  you are correct, against the worst realistic rival outcome.
- Smart Bet (Tier 2) and the Daily Double engine use your confidence to
  find the wager with the best real win chance.
- The Daily Double engine runs a simulation. Its answers come with a
  plateau, not one falsely exact number.

## Next steps

- Try the **Quiz Me** tab: see
  `docs/how-to/practice-with-quiz-mode.md`.
- Enter your own game's scores: see
  `docs/how-to/get-a-wager-recommendation.md`.
- Read the full math behind these numbers: `docs/white-paper.md`.
