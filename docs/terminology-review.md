# Terminology review contract

Status: implementation scope frozen on 2026-09-09.

## Objective and sequence

Implement the first literature-review priority without making unreviewed semantic
changes. Reuse the existing exact, one-step, hash-pinned dictionary loader. Follow
this milestone with a separately specified visit-gap sensitivity analysis, network
background validation, combination compression, and dose trajectories, in that order.

## Commands and boundary

`dictionary-prepare --input-dir DIR --output DIR` verifies the existing public
first-prescription tables and normalization audit against their run manifest. It
requires identity normalization and emits a sorted public-vocabulary review ledger.
Only disclosed rows meeting the recorded minimum patient count contribute names.
The ledger is incomplete by design: suppressed and non-first-prescription vocabulary
is not reconstructed. It contains no counts, diagnoses, dates, or patient records.

`dictionary-compile --review CSV --version VERSION --output DIR` validates the
review ledger and emits an ordinary two-column dictionary plus the reviewed metadata
and a hash manifest. Neither command overwrites a directory or changes configuration.
The review ledger deliberately uses `proposed_item_name`, not the loader's
`canonical_item_name`, so a draft cannot accidentally activate as a dictionary.

## Review schema

Fields: source_item_name, proposed_item_name, canonical_item_id, item_type,
preparation, dosage_form, unit, review_status, reviewer_id, evidence_reference.
Initial status is pending, descriptive fields are unknown, and proposed names,
identifiers and review attribution are empty. No inferred synonyms are approved.

Status is pending, approved, or rejected. Only approved rows enter the mapping.
Approval requires all fields and an item type of herb, formula, other_medicine, or
other. Preparation, dosage form and unit must be explicitly reviewed; use
not_applicable only when justified. These are vocabulary descriptors, not automatic
unit conversions or prescription eligibility rules. Reviewer IDs and terminology
references must not contain clinical notes or patient identifiers.

Canonical IDs and names must agree one-to-one. Rows merged to the same name must
have identical type/preparation/form/unit metadata. A target that is itself present
in the ledger must be an approved identity row. Chains and cycles are refused. This
does not prove pharmacological equivalence or detect collisions with undisclosed
vocabulary. Existing visit-item collision and dose-conflict audits remain mandatory.

## Acceptance and risks

- Synthetic tests cover deterministic preparation, privacy thresholds, source hash
  mismatch, draft isolation, approval requirements, incompatible merges, chains,
  accidental overwrite, and loader compatibility.
- Run the complete existing synthetic test suite and CLI smoke checks.
- Generate the real draft using public aggregates only; confirm zero activated
  mappings and unchanged input hashes. Do not declare semantic review complete.
- Before applying a reviewed dictionary to real data, create a new configuration
  version with the generated SHA-256 and compare mapping coverage, collisions,
  dose conflicts, frequencies, networks and combinations against identity mode.
  Record any resulting cohort or estimand changes explicitly. No real dictionary
  is activated by this milestone.
- No dashboard markup changes are planned; UI rendering is not an acceptance test
  for this command-line workflow.
