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
const OPP = [[0, 0.5], [5000, 0.5]];
check('FJ no-wager win prob 0.75',
  approx(outcomeProbabilities(9000, 0, 0.5, [{ score: 5000, dist: OPP, pCorrect: 0.5 }])[0], 0.75));
check('FJ cover-bet win prob 0.875',
  approx(outcomeProbabilities(9000, 1001, 0.5, [{ score: 5000, dist: OPP, pCorrect: 0.5 }])[0], 0.875));
{
  const orig = defaultOpponentDist;
  defaultOpponentDist = () => OPP;
  check('FJ strict-win tiebreak recommends 1001', fjTier2([9000, 5000], 0, 0.5, 0.5).recommendedWager === 1001);
  defaultOpponentDist = orig;
}
{
  const rec = fjTier2([4000, 9000, 10000], 0, 1.0, 0.5);
  check('3-way both-leaders-bust win prob 1/12', approx(rec.winProbability, 1 / 12));
  check('3-way recommends 0', rec.recommendedWager === 0);
}

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
