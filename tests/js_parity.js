/* JS/Python parity harness — committed so CI can run it on every push.
 *
 * Extracts the engine functions from app/index.html (the hand-written
 * JavaScript port) and checks them against the same hand-derived values used
 * by the Python test suite, plus the statistical invariants introduced in the
 * 2026-07-23 reviews. Exits non-zero on any mismatch.
 *
 * Only the EXACT and DETERMINISTIC functions are checked for equality with
 * Python; the Monte Carlo Daily Double outputs use a different PRNG
 * (mulberry32 vs. Mersenne Twister) and so are only checked for invariants,
 * never for trial-for-trial equality. See RISK_REGISTER.md risk #8.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
const start = html.indexOf('<script>') + '<script>'.length;
const end = html.indexOf('</script>');
let js = html.slice(start, end);
// Keep only the engine section (everything before the UI plumbing), so no
// document/DOM references are evaluated under Node.
const cut = js.indexOf('/* =========================================================\n   UI PLUMBING');
js = js.slice(0, cut);
// Evaluate the engine in this scope so its top-level function declarations
// become accessible on globalThis for the checks below.
(0, eval)(js);

let failures = 0;
function check(name, cond, extra) {
  if (!cond) { console.error('FAIL:', name, extra !== undefined ? extra : ''); failures++; }
  else console.log('ok:', name);
}
const approx = (a, b, eps = 1e-9) => Math.abs(a - b) < eps;

// --- Exact Tier 2 Final Jeopardy values (hand-derived, must match Python) ---
// Tie rule: a tie for first goes to a tiebreaker (half a win); nobody wins at $0.
const OPP = [[0, 0.5], [5000, 0.5]];
const opp1 = [{ score: 5000, dist: OPP, pCorrect: 0.5 }];
check('FJ no-wager win prob 0.75', approx(expectedWinProbability(9000, 0, 0.5, opp1), 0.75));
check('FJ cover-bet win prob 0.875', approx(expectedWinProbability(9000, 1001, 0.5, opp1), 0.875));
check('FJ tie bet worth 0.8125 (tiebreaker)', approx(expectedWinProbability(9000, 1000, 0.5, opp1), 0.8125));
check('FJ all-in worth 0.5 (no win at $0)', approx(expectedWinProbability(9000, 9000, 0.5, opp1), 0.5));
check('FJ ceiling tie 0.95', approx(expectedWinProbability(10000, 0, 0.5,
  [{ score: 5000, dist: [[0, 0.5], [2500, 0.3], [5000, 0.2]], pCorrect: 0.5 }]), 0.95));
check('FJ correlated cover 0.825', approx(expectedWinProbability(9000, 1001, 0.5,
  [{ score: 5000, dist: [[5000, 1]], pCorrect: 0.5 }], 0.3), 0.825, 1e-4));
{
  const orig = defaultOpponentDist;
  defaultOpponentDist = () => OPP;
  check('FJ recommends 3999: top of the tied range, by money', fjTier2([9000, 5000], 0, 0.5, 0.5, 0).recommendedWager === 3999);
  const dists = { 1: [[0, 0.5], [9000, 0.5]], 2: [[0, 1 / 3], [8001, 1 / 3], [10000, 1 / 3]] };
  defaultOpponentDist = (s, i) => dists[i];
  const rec = fjTier2([4000, 9000, 10000], 0, 1.0, 0.5, 0);
  check('3-way both-leaders-bust win prob 1/12', approx(rec.winProbability, 1 / 12));
  check('3-way recommends 4000 (tied win share, most money)', rec.recommendedWager === 4000);
  defaultOpponentDist = orig;
}

// --- Simulated behavior (hand-derived, see tests/test_behavior.py) ---
check('winShare two-way tie 0.5', winShare([100, 100], 0) === 0.5);
check('winShare three-way tie 1/3', approx(winShare([100, 100, 100], 2), 1 / 3));
check('winShare nobody wins at $0', winShare([0, 0, 0], 0) === 0);
{
  const d = Object.fromEntries(wagerDistribution([10000, 8000, 3000], 1));
  const exp = { 8000: 0.308, 1999: 0.27, 2001: 0.15, 3999: 0.08, 0: 0.048, 2000: 0.048, 4000: 0.048, 6000: 0.048 };
  check('B published regime weights', Object.keys(exp).length === Object.keys(d).length &&
    Object.entries(exp).every(([w, p]) => approx(d[w], p, 1e-12)), JSON.stringify(d));
  const a = Object.fromEntries(wagerDistribution([10000, 8000, 3000], 0));
  check('A cover weights', approx(a[6001], 0.80, 1e-12) && approx(a[6000], 0.04, 1e-12) && approx(a[10000], 0.064, 1e-12));
  check('FJ accuracy follows score rank', fjAccuracy([3400, 10000, 8000], 1) === 0.51 && fjAccuracy([3400, 10000, 8000], 2) === 0.46 && fjAccuracy([3400, 10000, 8000], 0) === 0.40);
  const lock = Object.fromEntries(wagerDistribution([20000, 8000], 0));
  check('A lockout weights', lock[0] === 0.5 && lock[3999] === 0.5);
}
{
  const r = latentCorrelation(0.3);
  const both = quadratureNodes().reduce((acc, [f, w]) => acc + w * conditionalAccuracy(0.5, f, r) ** 2, 0);
  check('quadrature reproduces binary correlation 0.3', approx(both, 0.325, 1e-4));
}
check('solo at 100% bets everything', fjTier2([12000], 0, 1.0).recommendedWager === 12000);
check('solo DD at 70% bets the max', ddAnalyze([5000], 0, 2, 0.7, [], 0, 50).recommendedWager === 5000);
check('shipped defaults: leader at 89% does not bet the tie', fjTier2([10000, 8000, 3400], 0, 0.89).recommendedWager !== 6000);

// --- Inverse-normal / Bonferroni band reference values (must match Python) ---
check('inverseNormalCdf(0.95) ~ 1.6449', approx(inverseNormalCdf(0.95), 1.6449, 1e-3));
check('bonferroniZ(1, 0.05) ~ 1.6449', approx(bonferroniZ(1, 0.05), 1.6449, 1e-3));
check('bonferroniZ(10, 0.05) ~ 2.5758', approx(bonferroniZ(10, 0.05), 2.5758, 1e-3));
check('bonferroniZ(40, 0.05) ~ 3.0233', approx(bonferroniZ(40, 0.05), 3.0233, 1e-3));

// --- Daily Double statistical invariants (CRN pairing + behavior) ---
{
  const rec = ddAnalyze([4200, 6000, 3400], 0, 2, 0.5, [200, 400], 0, 400);
  const marg = Object.fromEntries(rec.standardErrors);
  const bestWager = rec.results.reduce((b, r) => (r[1] > b[1] || (r[1] === b[1] && r[0] < b[0])) ? r : b, rec.results[0])[0];
  const seBest = marg[bestWager];
  let allLe = true, worst = 0;
  for (const [w, pse] of rec.comparisonStandardErrors) {
    const ind = Math.sqrt(marg[w] ** 2 + seBest ** 2);
    if (pse > ind + 1e-12) { allLe = false; worst = Math.max(worst, pse - ind); }
  }
  check('DD paired SE <= independent SE for every wager (CRN is used)', allLe, 'worst excess=' + worst);
}
check('DD guaranteed-wrong recommends 0',
  ddAnalyze([5000, 8000, 3000], 0, 2, 0.0, [], 0, 400).recommendedWager === 0);
check('DD clear-signal recommends a positive wager',
  ddAnalyze([3000, 4000, 2000], 0, 2, 1.0, [], 0, 600).recommendedWager > 0);

if (failures === 0) {
  console.log('\nAll JS parity checks passed.');
  process.exit(0);
} else {
  console.error('\n' + failures + ' JS parity check(s) FAILED.');
  process.exit(1);
}
