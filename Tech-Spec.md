# Technical Specification: MingYiRx

## Architecture

MingYiRx is a local Python CLI with a small functional core:

1. `config.py` validates a JSON analysis contract.
2. `io.py` streams and canonicalizes prescription-line CSV records.
3. `cohort.py` assigns patient-level recorded-label phenotypes from full diagnosis history.
4. `analysis.py` builds visit prescriptions and computes aggregate estimands.
5. `privacy.py` suppresses low-count cells and scans public artifacts.
6. `pipeline.py` orchestrates a deterministic run and writes a manifest.

The core analysis uses only the Python standard library. Optional plotting runs in a separate CNSPlots environment and reads public aggregates only; adjusted inference remains a future module.

## Canonical input

Each source row represents one recorded item line within one visit. Required canonical fields are:

`patient_id, visit_id, visit_date, diagnosis_text, item_name`

Optional fields are:

`dose, unit, physician_id`

Source columns are mapped to canonical fields in JSON configuration. A selector is either a unique header string or a zero-based integer position. Positional selectors are required when an export contains duplicate header names. Direct identifiers may exist in the local input but must not be mapped except for the local patient key and must never be written to output.

The CLI accepts one or more repeated `--input` arguments. Every file in one run must have the same header schema and encoding. `expected_input_sha256`, when configured by basename, blocks a run if a locked source changes.

`cross_file_overlap_policy` is explicit:

- `append` preserves every row and is appropriate for known-disjoint partitions.
- `max_multiplicity` removes exact cross-file overlap while retaining the largest within-file multiplicity for each canonical line. It is appropriate for overlapping export snapshots.

The reconciliation invariant is `raw_rows - cross_file_overlap_rows_removed = analysis_rows`. The manifest records per-file absolute path, SHA-256, bytes, raw rows, column count, schema hash, read-only access, sensitivity status, and unknown receipt date as null. Validation errors identify the file and row but do not echo source values.

Diagnosis history for patient-level cohort assignment uses all canonical rows. Analysis visits may additionally require their aggregated diagnosis text to match the assigned group when `require_visit_group_match=true`. Medication-line eligibility is applied only after cohort construction using configured exact units, excluded exact names, and excluded name patterns. This keeps non-eligible item lines available for diagnosis-history ascertainment without admitting them into prescription sets.

## Item normalization contract

`item_normalization` records a nonblank version and optionally references a UTF-8 CSV with exactly one direct mapping per source name. Required columns are `source_item_name` and `canonical_item_name`. Paths resolve relative to the JSON configuration. Real-data dictionaries require an expected SHA-256 that must match before source data are analyzed.

Both dictionary fields undergo the same Unicode NFKC and whitespace normalization as source item strings. Eligibility filters apply to source strings first; eligible names are then mapped once. Unmapped names are preserved unchanged. Duplicate source entries, blank values, conflicting mappings, and chained non-identity mappings block the run. Processing variants, synonyms, plant parts, or botanical identities remain distinct unless the supplied human-reviewed dictionary explicitly maps them.

When multiple source strings map to one canonical name within a visit, their recorded doses are pooled under that canonical item. More than one distinct positive dose-unit pair then creates an unresolved visit-item conflict. This prevents normalization from silently hiding dose disagreement.

## Cohort contract

- Normalize Unicode width and whitespace without semantic synonym merging.
- Evaluate all configured regular expressions over each patient's complete diagnosis history.
- With `exclusive_groups=true`, include a patient only when exactly one configured group matches.
- Record overlap and unmatched counts in the aggregate flow report.
- Group names are stable codes; labels are presentation metadata.

## Visit contract

- A visit is keyed by `(patient_id, visit_id)`.
- When `require_visit_group_match=true`, only visits whose aggregated diagnosis text matches the assigned patient group are eligible.
- A configured item filter is applied within eligible visits; visits with no eligible medication items do not enter prescription analysis.
- All rows within a visit must resolve to one date; conflicting dates block the run.
- Visits are ordered by date and then visit ID for deterministic same-day ordering.
- A visit prescription is a set of normalized item strings plus an optional dose map.
- Repeated identical item-dose lines collapse within a visit.
- Multiple distinct positive doses for the same item in one visit mark that item dose unresolved.
- Dose-conflict audit rows report affected patients, visits, and visit-item cells by group and overall. If affected patients are below `min_public_n`, all conflict numerators and rates in that row are suppressed. When a group is suppressed, the overall numerators and one additional positive group are also suppressed so subtraction cannot recover the protected cell.
- Dose modification burden and the four dose-resolved transition modes are computed only when every item in both adjacent visits has one positive dose and retained items use the same unit. Binary composition metrics remain available for all eligible transitions.

## Estimands

### First-prescription prevalence

Use one earliest eligible visit per patient. For item `i` in group `g`:

`prevalence(i,g) = exposed patients / first-prescription patients`

### Adjacent-prescription change

For consecutive prescriptions `A` and `B`:

- Jaccard: `|A ∩ B| / |A ∪ B|`
- Retention: `|A ∩ B| / |A|`
- Addition: `|B - A| / |B|`
- Modification burden: `(added + removed + retained-dose-changed) / |A ∪ B|`

Compute transition metrics, then patient medians/proportions, then group medians/means so patients with many visits do not dominate.

### Matched different-patient reference

For every adjacent eligible transition, compare the previous prescription with candidate current prescriptions from other patients. Control visits must be second or later eligible visits and share clinician, recorded-label group, and calendar year. Matching proceeds through a fixed hierarchy:

1. same visit stage and exact prescription size;
2. same visit stage and nearest prescription size;
3. nearest prescription size within the same year.

Visit stages are second, third-to-fifth, and sixth-or-later. Self-matches are prohibited. When several candidate visits belong to one control patient, take that control patient's median Jaccard first; then take the median across control patients. Summarize transitions within each index patient before group aggregation.

Patient bootstrap confidence intervals resample index-patient summaries. The empirical one-sided null independently samples one eligible control patient and one of that patient's candidate visits for each matched transition, then repeats the same transition-to-patient-to-group aggregation. BH adjustment is applied across configured groups. Random seed and replicate counts are configuration and manifest facts.

Two fixed sensitivity restrictions reuse the already-constructed primary matching sets:

- exact year-stage-prescription-size matches only;
- transitions with at least five eligible control patients.

Each restriction redoes transition-to-patient-to-group aggregation and patient bootstrap intervals. It does not rematch excluded transitions, add arbitrary calipers, or run a second empirical null. The sensitivity seed is the configured primary seed plus two.

If physician identifiers are unavailable, matching is allowed only when configuration explicitly asserts a single-physician dataset. This analysis estimates excess longitudinal continuity relative to a constrained prescribing background; it is not a treatment effect, diagnostic test, or proof of individualized clinical benefit.

### Cross-group structure

Use prevalence-weighted Jaccard and base-2 Jensen-Shannon distance over one shared item universe meeting the public count rule in every configured group. Fixing one universe prevents each pairwise comparison from silently answering a different question. These are descriptive distributional metrics.

### Temporal stress test

Assign each patient to a period by first eligible visit. Compare group-specific first-prescription prevalence vectors over the union of items observed in either period; unobserved items receive zero prevalence. Period samples are patient-disjoint by construction. Item names and low-frequency item counts are not emitted by this scalar stress test.

The primary split uses `early_end_year`. A configured non-empty `temporal_cutpoints` list must include that primary year and repeats the same patient-disjoint estimands at each prespecified cut point. Every cut point reports prevalence-weighted Jaccard, base-2 Jensen-Shannon distance, and early-core retention. It does not search for an optimal cut point or test a temporal trend. If either period has fewer patients than `min_public_n`, both period counts and all derived metrics are suppressed and the warning does not disclose the small count.

### Stable first-prescription combinations

For each configured group, count each unordered two- or three-item combination at most once in each patient's first eligible prescription. A public candidate must have at least `min_public_n` exposed patients and support at least `core_prevalence`. Candidate generation first removes individual items below `min_public_n`.

`support = exposed patients / first-prescription patients`

`lift = observed support / product of constituent item prevalences`

Lift is a descriptive marginal-frequency calibration, not synergy, compatibility, mechanism, or benefit. Stability is the exact probability that a same-size nonparametric patient bootstrap sample reaches `core_prevalence`. For a candidate observed in `k` of `n` patients, this is the binomial survival probability with `X ~ Binomial(n, k/n)` and threshold `ceil(n × core_prevalence)`. `combination_analysis.stability_probability` classifies stable combinations without finite-replicate Monte Carlo noise.

### Privacy-safe recurrent-item networks

For each group, nodes are items from one first eligible prescription per patient. At a node-prevalence threshold `t`, a node must have at least `min_public_n` exposed patients, prevalence at least `t`, and exact bootstrap selection probability at least `network_analysis.stability_probability`. The primary node threshold is `core_prevalence`.

For every unordered eligible node pair, the edge support is the number of first-prescription patients exposed to both items. Public edges require at least `min_public_n` patients and cosine similarity at least `network_analysis.primary_cosine`, where `cosine = coexposed / sqrt(item_1_exposed × item_2_exposed)`. Edge lift is descriptive only.

The prespecified sensitivity grid crosses `network_analysis.node_prevalence_thresholds` with `network_analysis.edge_cosine_thresholds`. Every row reports node and edge counts, density, connected components, largest-component fraction, and node/edge membership retention and Jaccard relative to the primary setting. This directly audits threshold dependence rather than inferring robustness from similar-looking layouts.

Cross-group network comparison uses only the primary threshold setting. For every group pair and separately for nodes and edges, it reports intersection counts and membership Jaccard:

`J(A, B) = |A ∩ B| / |A ∪ B|`

Every public node or edge also receives an exact configured-group membership pattern. `all_groups`, `multi_group`, and `single_group` describe only membership in the thresholded public networks. They do not encode zero use, exclusivity, contraindication, clinical response, or a traditional compatibility interpretation. When both compared sets are empty, Jaccard is null because there is no observed membership universe to compare.

The core package does not estimate communities or fit degree-distribution models. Optional figures use the public aggregate node/edge tables, a fixed random seed for deterministic group-specific layouts, and editable SVG output. Cross-group comparison uses the same node/edge encodings and quantitative membership summaries, not node position. Neither layout, centrality, connectedness, nor lift establishes a traditional compatibility rule, syndrome, mechanism, efficacy, or scale-free structure.

## Privacy

- Default `min_public_n=10`; configuration below 10 is rejected unless `synthetic_mode=true`.
- Patient identifiers, visit identifiers, exact dates, free-text diagnosis strings, and patient-level metrics are never written to public outputs.
- `work/` and `outputs/` are ignored by Git.
- Manifest paths are absolute local paths; manifests must not be committed when they refer to real clinical inputs.
- Public files are scanned for forbidden headers and common phone/identity-number patterns.

## CLI

```text
python -m mingyirx validate --config CONFIG --input CSV [--input CSV ...]
python -m mingyirx run --config CONFIG --input CSV [--input CSV ...] --output DIRECTORY
```

`validate` is read-only and emits a console gate. `run` first performs the same validation and stops on `BLOCK`.

## Output contract

- `cohort_summary.csv`
- `first_prescription_item_prevalence.csv`
- `longitudinal_summary.csv`
- `transition_mode_summary.csv`
- `cross_group_similarity.csv`
- `temporal_stability.csv`
- `temporal_cutpoint_sensitivity.csv`
- `matched_reference_summary.csv`
- `matched_reference_sensitivity.csv`
- `item_normalization_audit.csv`
- `dose_conflict_audit.csv`
- `frequent_item_combinations.csv`
- `network_nodes.csv`
- `network_edges.csv`
- `network_threshold_sensitivity.csv`
- `network_group_overlap.csv`
- `network_membership.csv`
- `report.md`
- `run_manifest.json`

All outputs are aggregate. Empty analyses still emit headers and an explanatory warning.

## Verification

- Unit tests use committed synthetic data only.
- Tests assert deterministic row counts and exact metric values for a small fixture.
- A privacy test scans every generated artifact.
- A CLI smoke test runs from configuration to outputs.
- `python -m unittest discover -s tests -v` is the baseline check.
