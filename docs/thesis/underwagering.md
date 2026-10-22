# The House Is You: Why Strong Players Underwager on Jeopardy!

Version 2.2 — 2026-10-13. A thesis: an argument with its evidence, its
counter-evidence and the tests it still needs. Model figures come from this
project's engine at version 2.2.0; the white paper documents that engine.

## Abstract

The claim: careful, intelligent people learn early that gambling is a losing
game, because the house always wins. On Jeopardy! they are no longer the
customer. When they know a category, a Daily Double is a bet with the odds in
their favor, so they are the house. Many strong players still bet as if they
were the customer. They make small, "safe" wagers when the game rewards large
ones.

The evidence partly supports this and partly does not. Published data shows
that human Daily Double wagers fall well below the win-maximizing amount.
This project's model shows the cost is large for a trailing player and small
for a leader. But the premise that intelligent people avoid risk in general
is contradicted by the best-known study of the question. A narrower claim
survives: a heuristic that is correct in a casino gets applied to a game where
it is wrong. Tournament formats such as Jeopardy! Masters change the
incentives, and some caution there is rational.

## 1. The claim, stated so it can be wrong

Three parts:

1. **Heuristic.** People who avoid gambling hold a correct rule for
   negative-expectation games: "the more you bet, the more you lose."
2. **Transfer.** On Jeopardy! they apply the same rule to bets with positive
   expectation, and wager less than they should.
3. **Cost.** The underwager costs real win probability, most of all when the
   player is behind.

Each part can fail on its own. Section 3 tests part 1, section 4 part 2,
and section 5 part 3.

## 2. Why "the house always wins" stops being true

A casino bet has negative expectation for the player. In American roulette,
a single-number bet pays 35 to 1 on a 1-in-38 chance. The expected return per
dollar is (35 - 37)/38 = -2/38, a 5.26% house edge. Every dollar wagered loses
5.26 cents on average, so the rational amount to bet is zero.

A Daily Double reverses the sign. With wager w and probability p of a correct
response, the expected change in score is

    E[gain] = p·w - (1 - p)·w = (2p - 1)·w

When p > 0.5, every extra dollar wagered *adds* (2p - 1) dollars in
expectation. At 70% confidence that is +40 cents per dollar: a 40% edge, in
the player's favor, nearly eight times the roulette house edge. The player
holds the edge the casino normally holds. On this measure alone, "bet less"
is backwards.

Two cautions keep this honest:

- Jeopardy! does not reward expected dollars. In regular play it rewards
  *winning the game* (the winner keeps their total and returns). The right
  target is win probability, which is what this project's engine maximizes.
  Win probability and expected dollars usually point the same way when you
  are behind, and can point opposite ways when you lead.
- p is the player's own estimate. An underconfident player bets less for a
  reason that is not risk aversion at all.

## 3. Do intelligent people avoid risk? The counter-evidence

The premise in part 1 is that intelligent people are risk-averse. The
best-known direct test finds the opposite. Dohmen, Falk, Huffman and Sunde
(2010) ran incentivized risk-choice experiments with about 1,000 adults in a
representative German sample. They found that **lower** cognitive ability goes
with **more** risk aversion, after controls for education, income and credit
constraints. The result is correlational.

So "smart people avoid risk" is not supported as a general trait. The claim
must be narrower to survive:

- **Domain-specific rule, not a trait.** People can be willing to take
  positive-expectation risks in a lab and still hold a firm rule about
  *gambling*, a domain they have learned is a losing one. Jeopardy! wagering
  looks and feels like gambling: a dollar amount, a stake, a reveal.
- **Loss aversion.** Losses weigh more than equal gains (Kahneman and
  Tversky, 1979). On television, a loss is also public and permanent.
- **Regret.** A big wager that misses is remembered as a mistake. A small
  wager that hits is not remembered as money left on the table.

None of these three is measured in this document. They are candidate
mechanisms, not findings.

## 4. Evidence that players underwager

Tesauro, Gondek, Lenchner, Fan and Prager (2013) studied real games from
the mid-1990s to 2012 at the latest. In more than 2,200 regular episodes in
which both second-round Daily Doubles were played, they compare the human
wager on the last Daily Double with the average bet that their Average
Contestant simulator recommends at row-based default confidence (T13
section 3.1.4, Table 3):

| Situation | Average human wager | Average simulator-recommended wager (row-based default confidence) |
|---|---|---|
| Player leading | $2,590 | $5,380 |
| Player trailing | $3,120 | $6,970 |

Humans bet about half of the recommended amount, in both positions. This is
the most direct published evidence for part 2 of the claim. It describes play
before the Daily Double hunting era. Since then, players have bet Daily
Doubles much harder (see ADR-0004), so the gap has likely narrowed. This
document does not measure by how much: the modern statistics come from a
source whose terms forbid republishing them.

**Jeopardy! Masters.** The claim that elite players underwager on the Masters
specials is an observation, not a measurement here. Testing it needs Masters
wager data, which this project does not publish (see section 7).

## 5. Measured: what underwagering costs

Method: this project's Daily Double engine (`engine/dd_wager.py`, version
2.1.0) simulates the rest of the game against simulated modern-era rivals,
then Final Jeopardy, and scores a tie for first as a share of a win. The
state below is a Double Jeopardy! Daily Double with about $8,000 left on the
board and no Daily Doubles after it. Each row: 2,000 simulated games per
wager, wagers on a $200 grid, two seeds (7 and 8); the figure is the range
across the two seeds. "Human average" uses Tesauro's published averages from
section 4 as the reference wager.

**Trailing player** (scores $6,000 vs $12,000 vs $8,000, you have $6,000):

| Confidence | Bet $2,000 | Human average ($3,120) | Bet everything ($6,000) |
|---|---|---|---|
| 70% | 15% | 16-17% | **26%** |
| 60% | 14% | 14-15% | **22%** |

Betting everything is the engine's recommendation in every run, and the only
wager on its plateau. The typical human bet gives up about 9 to 10 points of
win probability at 70% confidence: nearly 40% of the player's chances.

**Leading player** (scores $12,000 vs $8,000 vs $6,000, you lead):

| Confidence | Bet $2,000 | Human average ($2,590) | Recommended-size ($5,380) | Best estimate |
|---|---|---|---|---|
| 70% | 67% | 69% | 70-72% | 72-73% (at $7,400-$7,800) |
| 60% | 64% | 65% | 63-65% | 65-66% (flat; $0 to ~$10,000 not distinguishable) |

For the leader the cost is a few points at 70%, and at 60% a small bet is as
good as anything. The engine's statistical plateau is wide here: many wagers
cannot be told apart at this sample size.

**Final Jeopardy!, for contrast** (Tier 2 engine, exact; you lead $12,000 vs
$8,000 vs $6,000):

| Confidence | Bet $0 | Cover bet ($4,001) |
|---|---|---|
| 90% | 58.0% | **95.9%** |
| 70% | 58.0% | **85.8%** |

A leader who "plays it safe" by betting nothing gives up 28 to 38 points of
win probability. The cover bet is the safe bet. The engine itself now
recommends $4,499 at both confidence levels: the same win probability as
$4,001, with more money when right, because a miss still leaves $7,501.

Commands: see section 9.

## 6. When betting less is right

The thesis does not say "always bet more." The same engine says caution is
correct in several places:

- **Leading with modest confidence.** At 60% confidence the leader's curve
  is flat (section 5): extra wager buys little.
- **Second place in Final Jeopardy!.** With $8,000 behind a $12,000 leader
  (third place $6,000) at 70% confidence, the engine recommends $0 (36.9%
  win share). Betting small and hoping the leader misses is a real strategy.
- **Tournament incentives.** Jeopardy! Masters awards match points per game
  in the preliminary rounds: 3 for first, 1 for second, 0 for third. The
  two-game final is decided by combined score (Masters games are scored in
  points, not dollars). The format varies by season (the 2025 edition added
  a nine-player knockout round); check the official rules for a given year.
  Second place is worth something, so a bet that
  risks dropping from second to third has a real cost that regular play does
  not have. Some Masters caution is rational play under those rules, not
  timidity. This weakens Masters as evidence for the thesis: an underwager
  there must be judged against a match-points objective, which this
  project's engine does not model.

## 7. Data used, and what was not used

- **Published:** Tesauro et al. (2013), regular episodes, mid-1990s to 2012
  at the latest.
- **Model calibration:** the engine's simulated rivals are calibrated
  privately to J! Archive season statistics for Seasons 38-41 (ADR-0004).
  Those season pages include the in-season tournaments (for example, the
  Tournament of Champions) as well as regular play, so a minority of the
  calibrating games had tournament incentives. Jeopardy! Masters is archived
  separately and was **not** used. No J! Archive figure appears here; its
  terms forbid republication.
- **Not used:** any per-player, per-game wager record, and any data on
  contestants' education, intelligence or attitude to gambling.

## 8. What this does not prove

- It does not show that *intelligent* players underwager more than others.
  There is no measure of intelligence here, and the best evidence (section 3)
  says ability goes with less risk aversion, not more.
- It does not show *why* players underwager. Heuristic transfer, loss
  aversion, regret and underconfidence all predict small bets; nothing here
  separates them.
- The cost figures in section 5 are model outputs, not observed outcomes.
  They depend on the engine's assumptions (simplified regular-clue play,
  simulated rivals, the tiebreaker scoring). They have not been checked
  against real games.
- The human-average wagers are from before 2013. Modern players bet
  harder; the size of today's gap is unmeasured here.
- The Masters observation is not tested at all.

## 9. How to test it properly

1. **Gap, modern era.** For each real Daily Double, compare the actual wager
   with the engine's recommendation for that state, split by position
   (leading or trailing). Needs per-game data with a license that permits
   publication.
2. **Who underwagers.** Link wager gaps to a proxy for ability (for example,
   regular-clue accuracy in the same game) to test the "smart players"
   part directly, controlling for score position.
3. **Mechanism.** Underconfidence predicts a gap that shrinks in categories
   the player answers well; loss aversion predicts a gap that grows with the
   stake. The two can be separated by category and score.
4. **Masters.** Rebuild the objective as expected match points, then judge
   Masters wagers against that objective, not against win probability.

Reproduce section 5 (from `engine/`, version 2.2.0):

```python
import dd_wager, fj_bestresponse as br
from simulate import RolloutConfig
cfg = RolloutConfig(remaining_clue_values=[1100] * 7, remaining_dd_count=0)
r = dd_wager.analyze([6000, 12000, 8000], 0, 2, 0.7, config=cfg,
                     wager_step=200, trials_per_wager=2000, seed=7)
print(r.recommended_wager, dict(r.wager_win_probabilities)[6000])
r = br.analyze([12000, 8000, 6000], 0, 0.9)
print(r.recommended_wager, r.win_probability, dict(r.wager_win_probabilities)[0])
print(br.analyze([12000, 8000, 6000], 1, 0.7).recommended_wager)
```

## References

- Dohmen, T., Falk, A., Huffman, D., & Sunde, U. (2010). Are risk aversion
  and impatience related to cognitive ability? *American Economic Review*,
  100(3), 1238-1260.
- Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of
  decision under risk. *Econometrica*, 47(2), 263-291.
- Tesauro, G., Gondek, D., Lenchner, J., Fan, J., & Prager, J. M. (2013).
  Analysis of Watson's strategies for playing Jeopardy!. *Journal of
  Artificial Intelligence Research*, 47, 205-251.
  https://doi.org/10.1613/jair.3834 (preprint: https://arxiv.org/pdf/1402.0571)
- Jeopardy! Masters format (match points 3/1/0): Wikipedia, "Jeopardy!
  Masters." https://en.wikipedia.org/wiki/Jeopardy!_Masters
- This project: `docs/white-paper.md` (the engine and its figures),
  `docs/adr/0004-modern-era-calibration.md` (the calibration).
