# User-finalized terminology and visit-gap sensitivity

Frozen before execution on 2026-09-09.

The user explicitly selects all column B names in the returned workbook as final
analysis labels and requests recoding and continuation. This supersedes the earlier
pending candidate-name decision for this run. It does not assert pharmacist approval
or resolve unknown preparation, dosage form or unit metadata. Retain the original
workbook and unchanged clinical review statuses. Use authorization provenance
`user_finalized_column_b`, not `pharmacist_reviewed`.

## Mapping and run

- All 138 source names must match the original public ledger. B must be nonblank.
- Assign one deterministic RX code per distinct B value in Unicode sorted order.
  Retain old codes in a separate crosswalk. Detect chains before applying mappings.
- Emit the existing exact two-column dictionary with SHA-256. Do not weaken the
  pharmacist-review compiler or fill unknown metadata to satisfy it.
- Run in a new output directory with dictionary version `user-final-b-20260909-v1`
  and cohort version `v3.1.0-user-final-b-normalization`. All other analysis parameters,
  source hashes, eligibility and thresholds remain fixed. Unlisted names pass through.
- Verify original artifacts remain unchanged, compare cohorts, normalization,
  dose conflicts, longitudinal metrics, networks and combinations, and rebuild the
  local aggregate-only dashboard. No external deployment is part of this change.

## Secondary visit-gap analysis

Use original adjacent eligible visits within each patient, never bridge across removed
transitions. Restrict to the strict single-disease cohorts. Descriptive sensitivity
windows are all positive gaps, 1-30 days, 1-90 days and 1-180 days (inclusive).
These are exploratory analyst-selected windows, not clinical guidelines. Same-day
transitions remain in the existing primary analysis and are omitted from this
secondary analysis. Report this difference explicitly.

Compute each patient's median Jaccard in a window, then the group median. Reuse the
existing transition metric. Bootstrap whole patient summaries for a percentile 95%
interval, 1000 replicates, seed 20260909. Report patient-median follow-up duration,
visit count and positive adjacent-gap median. No tests or efficacy interpretation.

Privacy: require the existing min_public_n for every window's patients. Suppress the
entire group's window family if a positive-gap window has fewer patients than the
threshold, or if a nonzero difference between any two nested window patient totals
is below it. Do not publish excluded small counts. No identifiers or exact dates leave
memory. This conservative additional rule guards nested-denominator subtraction.

Acceptance: source/worksheet preservation, exact name-ID consistency, synthetic
window boundaries and patient weighting tests, deterministic bootstrap tests,
suppression tests, full regression suite, public-output privacy scan, unchanged
baseline hashes, new run source/artifact hashes, local dashboard generation.
