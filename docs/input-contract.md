# Input Contract

## Source boundary

Real clinical exports remain outside the repository and are opened read-only. The repository may contain non-sensitive configuration templates and synthetic fixtures, but never direct identifiers, patient-level derivatives, pseudonymization keys, or exact clinical dates.

## Row grain

Each input row is one recorded medication item line within one visit. Required canonical fields are `patient_id`, `visit_id`, `visit_date`, `diagnosis_text`, and `item_name`. `dose`, `unit`, and `physician_id` are optional.

`patient_id` and `visit_id` are local linkage keys. They are held only in memory and never written to aggregate outputs. A timestamp column may be selected for both `visit_id` and `visit_date` when `(patient_id, timestamp)` uniquely represents a visit.

## Column selectors

Configuration values under `columns` are either:

- a unique source header string; or
- a zero-based integer column position.

If a selected string appears more than once in the header, validation blocks and requires a positional selector. All required positions must exist in every row.

## Multiple files

Supply each source using a repeated `--input`. All inputs in one run must have the same ordered header schema and encoding.

Choose `cross_file_overlap_policy` from:

- `append` for verified non-overlapping partitions;
- `max_multiplicity` for overlapping export snapshots. For each canonical line, this retains the greatest occurrence count observed in any one file and removes only excess copies contributed by overlap between files.

The selected policy is a data provenance decision, not a statistical option. It must be fixed before analysis.

## Validation and provenance

Each run records file SHA-256, byte size, raw row count, column count, and header-schema hash. Optional `expected_input_sha256` entries are keyed by source basename and block unexpected source drift.

The following reconciliation must hold:

`raw_rows - cross_file_overlap_rows_removed = analysis_rows`

Validation reports only aggregate counts. Source values are not echoed in errors or public artifacts.

## Analysis eligibility

All canonical rows contribute to complete diagnosis-history cohort assignment. `require_visit_group_match` can then restrict analysis to visits whose aggregated recorded diagnosis matches the assigned group. `item_eligibility` can restrict prescription items by exact normalized units and exclude exact names or name patterns. These filters are recorded in configuration and never inferred from the drugs themselves.

## Versioned item dictionary

An optional dictionary is configured under `item_normalization` with `version`, `dictionary_path`, and `expected_sha256`. The CSV must be UTF-8 and contain `source_item_name,canonical_item_name`. Relative paths are resolved from the configuration file. A dictionary used with real clinical data is invalid without a matching expected SHA-256.

Mappings are exact, direct, and one-step after Unicode/whitespace normalization. Unlisted source names pass through unchanged. Dictionary files must not contain patient data, doses, dates, diagnoses, or free-text clinical notes. A source-string-only run uses a null dictionary path and explicitly versioned identity mode.
