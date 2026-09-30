# Dashboard research workbench 0.15.0

## Scope and acceptance

Continue the approved local dashboard design using existing disclosed aggregates.
No raw-data rerun, clinical recommendation, deployment, or third-party dependency.

1. Clearing medication search preserves the selected combination-size filter.
2. A provenance panel separates analysis and dashboard versions, publishes only
   allowlisted run identity, and checks loaded artifact hashes when a manifest exists.
   Missing identity is unknown; a hash mismatch blocks generation.
3. A single-item workspace compares the same one-dimensional stratum across
   disclosed phenotypes. Show numerator, denominator, missingness, and recorded dose.
4. Strict-cohort research has its own selector, independent of clinical strata.
   Show existing matched estimates, confidence intervals, FDR, sensitivity analyses,
   transition modes, and primary-network neighborhoods without re-estimation.
5. Quality panels distinguish present, absent, and checked evidence. Suppressed
   cells remain missing. No raw exclusion counts or manifest warning text are exposed.
6. Export the selected item view as formula-safe CSV and a JSON provenance record.
   Network threshold sensitivity is a table, since alternative edge sets are absent.

## Contract and verification

- Extend the embedded payload with `research` and `provenance`; additional aggregate
  tables are optional for backward compatibility, but malformed present tables fail.
- Projection occurs before serialization. Never serialize the restricted manifest.
- Preserve original CSV files and prior review HTML. Store a new versioned HTML.
- Test real event-listener accumulation, cohort isolation, missing values, export
  formula protection, whitelist behavior, and artifact mismatch rejection.
- Run the full synthetic suite, build twice for deterministic output, verify source
  hashes, and inspect desktop/mobile behavior through the local browser.
- Terminology normalization review and multi-visit sequence estimation remain
  separate analysis-contract work; no automatic drug merging or invented trajectories.
