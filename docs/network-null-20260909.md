# Fixed-margin network background analysis

Frozen before execution: 2026-09-09. Secondary exploratory analysis only.

Use the user-finalized-B configuration and strict cohorts. Each patient contributes
the first eligible prescription. Randomize the complete binary prescription-item
matrix, including low-frequency items, while preserving every row and column sum.
No rare item labels or patient matrices are emitted.

Use Curveball row trades: choose two distinct rows uniformly, retain shared items,
uniformly redistribute their symmetric difference while retaining row sizes. Include
identity trades. Reference: Strona et al., Nature Communications 5:4114 (2014),
https://www.nature.com/articles/ncomms5114 (publisher lists corrections). The
finite-chain mixing diagnostics below are our implementation choices, not guarantees
that draws are independent or perfectly uniform.

## Family, sampling and disclosure

- Node eligibility exactly reuses primary prevalence and bootstrap-selection rules.
  These depend on column marginals, which remain fixed under the null.
- Test all unordered pairs of eligible nodes, including unplotted and zero-count
  pairs. Apply BH within the full group family before any output suppression.
- Two chains, 500 retained matrices each. Each starts at the observed matrix, with
  20*N attempted row trades for burn-in and 2*N attempted trades between samples.
  Seed 20260909 plus 100*group index plus chain index; groups sort by code.
- Empirical upper-tail probability: (1 + retained counts >= observed)/(1001).
  Compute BH-adjusted values as exploratory Monte Carlo quantities. Correlated
  sampling, finite resolution and dependent edge tests limit formal FDR claims.
- Export only pairs with at least min_public_n observed coexposed patients, without
  selecting by p/q. Include whether the pair belongs to the existing primary graph.
- Every retained matrix must match original row/column sums. Record changed trade
  fraction, maximum edge R-hat, maximum absolute lag-1 correlation, and maximum
  between-chain mean difference. Flag R-hat >1.05 or abs(lag-1)>0.2 for review.
  These diagnostics do not establish global mixing; unresolved flags are reported.
- No efficacy, pharmacological interaction, validated clinical prediction or
  externally replicated association claim is allowed.

## Acceptance

Test row/column invariants, deterministic output, a tiny enumerated state space,
degenerate matrices, privacy suppression, and the complete pre-disclosure family.
Run full synthetic regression tests. Real run must verify source and configuration
hashes against the normalized baseline, preserve all baseline outputs, scan public
outputs, and record software/configuration/seed and artifact provenance. Keep this
analysis in a separate output directory; do not alter the primary dashboard.

## Sampling amendment after first diagnostic run

The first real run preserved margins but all three groups exceeded the predeclared
maximum absolute lag-1 threshold (approximately 0.25-0.26). Before inspecting edge
p/q results, increase thinning from 2*N to 10*N attempted trades; retain burn-in,
seeds, family, draw count, p/q formulas and primary data. Preserve the first run.
The second run is a sampling-quality refinement, not a search for more discoveries.
