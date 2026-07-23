# Statistical Review v2 — 2026-07-23 (Referee Report)

Status: the headline finding is fixed in code; the remaining findings are
documented as known limitations. This report is written in the register of a
thesis committee referee. It supersedes nothing in the v1 review
(`statistical-review-2026-07-23.md`); it corrects one thing the v1 review got
wrong and records issues v1 did not examine.

## Summary judgment

The project is methodologically serious for its scope: it separates a
distribution-free guarantee (Tier 1) from a probability-weighted
best-response (Tier 2 / Daily Double), it tests exact math by hand, and it
labels its placeholders. That is above the bar for what it is. However, the
Daily Double engine — the one genuinely statistical component — contained a
second, subtler error beneath the one v1 fixed, and several modeling
assumptions are stated too weakly. One of these (Finding 1) is a real defect
that changed recommendations; it is now fixed. The rest are correctly scoped
as limitations but must be stated plainly, which they now are.

## Finding 1 (defect, FIXED): the comparison variance contradicted the
## simulation design

**Context.** The Daily Double engine estimates each candidate wager's win
probability by Monte Carlo rollout, using **common random numbers** (CRN):
within a trial, every candidate wager is scored against the *same* replayed
rest-of-game randomness. CRN is a standard variance-reduction technique whose
entire purpose is to make *comparisons between wagers* more precise by
inducing positive correlation between their estimates.

**The error.** The v1 fix selected the recommended wager using a "plateau" of
statistically-indistinguishable wagers, but computed the comparison standard
error with the **independent** two-sample formula
`sqrt(se_w^2 + se_best^2)`. That formula assumes the two estimates are
independent. Under CRN they are not — they are strongly positively
correlated. The correct variance of the difference is

    Var(p_w - p_best) = Var(p_w) + Var(p_best) - 2*Cov(p_w, p_best),

and the `-2*Cov` term is exactly the variance reduction CRN was introduced to
buy. By using the independent formula, the engine discarded that reduction
and systematically *overstated* the comparison uncertainty.

**Evidence.** Instrumenting the engine's own CRN loop to record per-trial
paired win indicators, for the exact reported scenario
`scores = [4200, 6000, 3400]`, `p_correct = 0.42`, 3000 trials, seed 42:

| quantity | value |
|---|---|
| independent comparison SE (used by v1) | ~0.0114, roughly constant across wagers |
| true paired comparison SE | falls from 0.0095 to 0.000 as wagers approach the best |
| win-indicator correlation with the best wager | rises from ~0.30 to 1.00 |

The decision consequence was not cosmetic. Under the independent SE the
plateau spanned **\$100–\$4,200 and the engine recommended \$100**; under the
correct paired SE the plateau was **{\$4,200}**. The engine's stability across
confidence levels — the property v1 was proud of — turned out to be an
artifact of an over-wide (wrong) interval, and it caused systematic
*under-betting*.

**The fix.** Two coupled changes:

1. *Paired comparison variance.* The engine now records the per-trial win
   indicator for every candidate wager and estimates the SE of the difference
   (candidate vs. empirical best) directly from the per-trial paired
   differences. This respects the CRN design.

2. *Multiplicity control.* Roughly `k` candidate wagers are each compared
   against the single empirical best wager. This is a
   multiple-comparisons-with-the-best problem (Hsu, 1996). A per-comparison
   `z = 1` re-introduces instability, because the empirical best is itself the
   maximum of `k` noisy estimates. The engine now uses a Bonferroni band
   `z* = Phi^{-1}(1 - alpha/k)` (default `alpha = 0.05`), which adapts to the
   number of candidate wagers (`z* ~ 2.7–3.05` for the grids used here).

**Why the fix is correct on both ends (verified).**

- *Flat scenario* (`[4200, 6000, 3400]`, `p ~ 0.43`), where all wagers are
  genuinely about equal: recommends **\$0, stable across every seed** — the
  right call, made for the right reason (a wide plateau because the surface is
  truly flat, not because the interval is mis-computed).
- *Clear-signal scenario* (`[3000, 4000, 2000]`, guaranteed correct), where
  betting genuinely helps: recommends **\$1,200, stable across every seed**,
  and does **not** collapse to \$0 — the paired SE detects that wagers below
  \$1,200 are significantly worse, and the "smallest wager on the plateau"
  rule then picks \$1,200 rather than the full \$3,000.

This is the difference between a rule that is stable because it is right and a
rule that is stable because it is blunt.

## Finding 2 (limitation, DOCUMENTED): the reported win probability is
## selection-biased

`win_probability` is the in-sample maximum over ~`k` candidate wagers. The
maximum of `k` noisy estimates is an upward-biased estimate of the true best
value (the "winner's curse"). The *recommended wager* is well insulated —
it is the smallest wager on a multiplicity-controlled plateau, not the raw
argmax — but the reported *percentage* should be read as a mild optimistic
upper bound, not an unbiased point estimate. This is now stated in the engine
docstring, the notes returned to the caller, and the risk register. A future
version could report a debiased estimate (e.g., data-splitting: choose the
wager on one half, estimate its win probability on the other) or the
recommended wager's own out-of-selection estimate.

## Finding 3 (limitation, DOCUMENTED): "monotonicity" was overstated

The prior docstring implied CRN delivered monotonicity guarantees. It does
not. Because opponents' modeled Final Jeopardy wagers depend on the player's
own score, raising the Daily Double wager can change opponents' downstream
behavior and move the win probability non-monotonically. CRN provides a fair
*paired comparison*, not monotonicity. Wording corrected in the engine and
the white paper.

## Finding 4 (limitation, DOCUMENTED): Tier 2 opponent-correctness
## independence

The exact Final Jeopardy enumeration treats each opponent's correctness as
independent. Real Final Jeopardy correctness is positively correlated across
players (shared clue, shared difficulty). Positive correlation would, for
example, raise the probability that *both* leaders miss — so the "third place
can win when both leaders bust" figure (1/12 in the shipped example) is, if
anything, a conservative floor under a more realistic positively-correlated
model. This is a modeling choice, not an arithmetic error, and is now flagged
against ADR-0002 and in the risk register.

## Finding 5 (limitation, DOCUMENTED): "exact" means double precision, not
## exact rational arithmetic

The Tier 2 enumeration is called "exact" to contrast it with Monte Carlo. It
is exact in the sense of *no sampling error*, but it is computed in IEEE-754
double precision, not exact rational arithmetic. The accumulated floating
error (~1e-16) is far below the 1e-9 comparison tolerance, so no result is
affected, but the white paper wording is tightened to "exact enumeration in
double precision (no sampling error)".

## Finding 6 (limitation, DOCUMENTED): the app and the reference engine use
## different PRNGs

The Python engine uses the Mersenne Twister; the JavaScript app uses
`mulberry32`. Given the "same" seed they produce *different* random streams,
so the app's Daily Double numbers will not match the Python engine's
trial-for-trial. The exact (Final Jeopardy) functions and the deterministic
bound functions do match, and were re-verified under Node against the Python
hand-derived values, along with the inverse-normal and Bonferroni-band values
and the paired-SE <= independent-SE invariant. But the Monte Carlo Daily
Double outputs are only distributionally comparable, not identical. Extends
risk #8.

## Finding 7 (limitation, DOCUMENTED): the board abstraction is coarse

`approximateClueList` reconstructs the remaining board from a single number
(total dollars left) by assuming a fixed average clue value. Two very
different board states (many small clues vs. a few large ones) map to the same
rollout. Already labeled a placeholder; reinforced here because it materially
affects Daily Double rollouts far from Final Jeopardy.

## What would move this from "good project" to "defensible thesis chapter"

1. Calibrate the opponent model against real data (the single largest source
   of unquantified error; ADR-0002, risk #5).
2. Replace the Bonferroni band with the exact MCB constant (Hsu) or a
   bootstrap over the joint rollout, and report a proper simultaneous
   confidence set for the win-probability curve.
3. Debias the reported win probability (data-splitting), and show the
   coverage of the plateau empirically.
4. Model opponent-correctness correlation and report sensitivity of the
   headline numbers to it.
5. Unify the two engines behind one PRNG (or generate the JS from the Python)
   so parity is exact and CI-checkable.

None of these are required for the tool to be useful. All of them are the
difference between "the numbers are directionally sound and honestly labeled"
and "the numbers are defended".

## Validation performed for this review

- Instrumented CRN experiment demonstrating the independent-vs-paired SE gap
  and the resulting opposite recommendations.
- Cross-seed stability of the corrected (paired SE + Bonferroni) rule on both
  a flat scenario and a clear-signal scenario.
- Full test suite: 33 passing (4 new/updated tests for the paired SE, the
  Bonferroni band, and clear-signal behavior).
- JS/Python re-verification under Node: exact FJ values, inverse-normal and
  Bonferroni-band reference values, and the paired-SE <= independent-SE
  invariant all match.
