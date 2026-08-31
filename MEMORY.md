# Project Memory

## 2026-08-31 — Project initialization

- This repository generalizes the validated Tao Qingwen RA/Sjögren disease/ankylosing spondylitis workflow into a reusable local-first analysis project.
- The scientific center is patient-linked adjacent-prescription change, not static frequency or network visualizations alone.
- Raw clinical data and patient-level intermediates must remain outside Git; committed examples use synthetic records only.
- The first release should stay small: intake validation, canonical visit/item tables, first-prescription prevalence, adjacent-visit Jaccard, additions/removals/dose changes, cross-group overlap, time-period stress testing, privacy suppression, and an auditable run manifest.
- Disease-specific rules, source column names, privacy thresholds, and time periods belong in configuration rather than code.
- The original study's matched same-clinician different-patient reference, adjusted modelling, bootstrap inference, network analysis, and manuscript generation are later modules after the core data contract is stable.

## 2026-08-31 — Version 0.1.0 core implemented

- The repository now contains a standard-library-only Python CLI with JSON configuration, canonical CSV ingestion, full-history exclusive recorded-label cohorts, first-prescription prevalence, adjacent-visit Jaccard/retention/addition, dose-aware modification burden, transition modes, cross-group similarity, patient-disjoint temporal stability, privacy suppression, and run manifests.
- The committed dataset is synthetic: 53 item lines, 14 patients, 12 exclusively assigned patients, one overlap exclusion, and one unmatched exclusion. It contains no real clinical records.
- Four deterministic tests cover cohort assignment, composition and dose transitions, end-to-end aggregate outputs, repeat-run artifact stability, privacy scanning, and rejection of a real-data configuration with `min_public_n < 10`.
- The demo produced seven public artifacts plus a run manifest; the privacy scan reported zero issues. `outputs/`, `work/`, and real/private data paths are Git-ignored.
- Python 3.12 virtual environments may not include `setuptools`; the supported zero-dependency path is `PYTHONPATH=src`. Editable installation remains optional when build tooling is already available.
- The next implementation priority is a source adapter and configuration for the locked Tao Qingwen GB18030 export, followed by the matched different-patient reference and patient-bootstrap uncertainty. Real data must remain outside this repository.

## 2026-08-31 — Version 0.2.0 source adapter verified

- The CLI now accepts repeated inputs, header-name or zero-based positional selectors, GB18030 exports with duplicate headers, optional locked SHA-256 values, explicit `append` or `max_multiplicity` overlap handling, and per-file provenance with row-count reconciliation.
- Cohort assignment uses complete diagnosis history; optional visit-level group matching and configurable item eligibility are applied only when constructing analysis prescriptions.
- The committed Tao Qingwen template contains no source path or patient data. It maps the locked 17-column exports by position and preserves the original decoction-item eligibility rule.
- Read-only real-data validation reproduced 281,287 source and analysis rows, 4,464 source patients, and strict recorded-label groups of RA 771, SjD 669, and AS 540. Eligible prescription cohorts reproduced 677, 652, and 460 patients, with 3,164, 2,535, and 1,580 visits and 2,487, 1,883, and 1,120 adjacent transitions.
- Cross-disease similarity now uses one all-group public item universe and base-2 Jensen-Shannon distance; temporal similarity uses the union of items across patient-disjoint periods. These definitions reproduce the locked cross-disease and temporal aggregate results.
- The first real aggregate run exposed decimal strings as false positive identity numbers. CSV precision is now bounded to nine decimals and privacy patterns exclude decimal substrings; the corrected run passed with zero privacy issues.
- Real aggregate preflight artifacts remain under ignored `outputs/tao_preflight/`. The next implementation priority is the matched same-clinician different-patient reference with patient-level bootstrap uncertainty.

## 2026-08-31 — Version 0.3.0 matched reference verified

- The matched reference uses only second-or-later control visits from another patient under a fixed hierarchy: same physician, recorded-label group, year, stage, and exact size; nearest size within the same stage; then nearest size within the same year.
- Candidate visits are summarized within each control patient before the control-patient median. Matched transitions are summarized within index patients before group medians and patient bootstrap intervals.
- The real-data run matched all 5,490 eligible transitions from 851 repeat patients: RA 336/2,487, SjD 346/1,883, and AS 169/1,120. Point estimates exactly reproduced the locked analysis: observed patient-median Jaccard 0.741, 0.751, and 0.750; matched background 0.242, 0.320, and 0.273; within-minus-between 0.480, 0.411, and 0.458.
- With 2,000 null replicates, all three empirical one-sided p values and BH-FDR values were 0.00049975. The standard-library seeded bootstrap is deterministic and yields substantively equivalent but not byte-identical intervals to the earlier NumPy RNG implementation.
- The aggregate run remained `PASS_WITH_WARNINGS` with zero privacy-scan issues. Synthetic examples now include matchable same-year repeat visits, and tests cover self-match exclusion, nearest-size fallback, control-patient weighting, deterministic repetition, and physician provenance requirements.
- The next scientific priority is a matching-rule sensitivity analysis. Covariate-adjusted modelling should remain separate because the current generic input contract does not require demographic or clinical covariates.

## 2026-08-31 — Version 0.4.0 matching sensitivity verified

- The primary matched sets now feed two prespecified restrictions without rematching: exact year-stage-prescription-size matches only, and transitions with at least five eligible control patients. Each restriction repeats transition-to-patient-to-group aggregation and a patient bootstrap with seed `primary_seed + 2`; it does not rerun the empirical null.
- The real exact-match restriction retained RA 322 patients/2,405 transitions, SjD 328/1,769, and AS 164/1,047. Within-minus-between medians were 0.487, 0.416, and 0.459.
- The minimum-five-control restriction retained RA 272 patients/2,037 transitions, SjD 299/1,531, and AS 100/581. Within-minus-between medians were 0.494, 0.421, and 0.485.
- All six standard-library bootstrap intervals remained above zero. Counts and point estimates exactly reproduced the locked prior analysis; intervals are deterministic but not byte-identical to the earlier NumPy RNG implementation.
- Two consecutive real-data runs produced identical artifact hashes and zero privacy-scan issues. The next priority is a prespecified temporal-cutpoint sensitivity analysis; covariate adjustment remains deferred until a stable covariate contract exists.

## 2026-08-31 — Version 0.5.0 temporal cut-point sensitivity verified

- Configuration now requires a non-empty ascending `temporal_cutpoints` list containing the primary `early_end_year`. The Tao Qingwen template fixes 2018, 2019, 2020, and 2021 as early-period end years.
- Every cut point assigns each patient once by the first eligible prescription, so early and late samples remain patient-disjoint. If either side is below `min_public_n`, both period counts and all derived metrics are suppressed and warnings do not reveal the small count.
- The 12 real group-cutpoint rows exactly reproduced the locked counts and point estimates at nine-decimal output precision. Weighted Jaccard ranges were 0.398-0.423 for RA, 0.329-0.344 for SjD, and 0.375-0.483 for AS; every value remained below 0.5.
- Early-core retention ranged from 0.619-0.667 for RA, 0.464-0.591 for SjD, and 0.600-0.842 for AS. These are internal calendar-period stability summaries, not evidence of clinical change or external validation.
- Eleven synthetic tests, compilation, privacy scanning, and two consecutive real runs passed; the real artifact hashes were identical. A future module should prioritize versioned medication normalization and dose-conflict auditing before adjusted modelling or network expansion.

## 2026-09-01 — Version 0.6.0 item normalization and dose audit verified

- `item_normalization` now accepts a versioned UTF-8 mapping CSV with `source_item_name` and `canonical_item_name`, resolves paths relative to configuration, and requires a matching SHA-256 for real data. Mappings are normalized, direct, one-step, and exact; unmapped names pass through unchanged.
- Eligibility is applied before mapping. When multiple reviewed source strings map to one canonical item within a visit, dose values are pooled and conflicting positive dose-unit pairs remain unresolved instead of being silently hidden.
- The real Tao Qingwen run remained in explicit `source-string-v1` mode because the available supplement is a display-label table whose pharmacopoeial/botanical mapping status says the completed review record still needs transcription. The run contained 125,345 eligible lines and 417 distinct source strings; no semantic renaming was performed.
- Public dose-conflict rows use primary small-cell suppression, complementary suppression of one additional positive group, and suppression of the overall numerators whenever subtraction could recover a protected group. Exact totals remain only in the ignored local manifest.
- All nine pre-v0.6 scientific table hashes were unchanged, twelve tests passed, repeat-run artifacts were identical, and the real privacy scan reported zero issues. The next reusable analysis priority is privacy-aware stable pair/triplet extraction before optional network visualization.

## 2026-09-01 — Version 0.7.0 stable combinations verified

- `combination_analysis` now extracts unordered pairs and triplets from each patient's first eligible prescription. Public candidates must meet both `min_public_n` and the prespecified `core_prevalence`; lift remains a descriptive marginal-frequency calibration.
- Stability is the exact plug-in nonparametric-bootstrap selection probability `P[X >= ceil(n × core_prevalence)]` for `X ~ Binomial(n, k/n)`. The implementation computes tails from the threshold to avoid large-sample underflow and contains no Monte Carlo randomness.
- The real strict three-disease run produced 726 candidates and 622 stable combinations: RA 74 pairs/84 triplets with 65/70 stable, SjD 119/191 with 100/165 stable, and AS 84/174 with 82/140 stable.
- The candidate row set, support counts, support values, lift values, and stability classifications exactly matched all 726 strict-group rows from the locked prior implementation. All eleven pre-v0.7 CSV table hashes were unchanged.
- Fourteen tests and compilation passed. Two consecutive real runs produced identical hashes for all 13 public artifacts, and the privacy scan reported zero issues.
- Network visualization remains deferred. The next step should define privacy-safe edge eligibility and prespecified threshold sensitivity before plotting; no scale-free, synergy, mechanism, or efficacy claim is permitted from co-occurrence data.

## 2026-09-01 — Version 0.8.0 threshold-sensitive networks verified

- Network nodes now require `min_public_n`, the configured prevalence threshold, and an exact bootstrap reselection probability at least `network_analysis.stability_probability`. Edges require `min_public_n` coexposed first-prescription patients and the configured cosine threshold; edge lift remains descriptive.
- The real primary setting used 20% node prevalence, 0.80 node stability probability, and cosine 0.50. RA contained 23 stable nodes/83 edges, SjD 26/121, and AS 21/82. The 286 published edges were a strict subset of the 309 earlier candidate-node edges, and every retained support count, cosine value, and lift matched the locked implementation.
- The prespecified 3×3 grid crossed node prevalence 15%, 20%, and 25% with cosine 0.40, 0.50, and 0.60. Node-set Jaccard minima versus the primary setting were 0.70 for RA, 0.81 for SjD, and 0.78 for AS; edge-set minima were 0.41, 0.54, and 0.55. Absolute edge counts ranged from 34-178, 68-223, and 49-148, so topology is threshold-sensitive.
- The optional CNSPlots script reads only public aggregates and produces deterministic PNG/SVG network panels plus edge-membership sensitivity heatmaps. Group-specific fixed-seed layouts, explicit CJK fonts, and separate placement of small components resolved label loss and component compression; cross-group node position is not interpretable.
- Fifteen tests and compilation passed. Two consecutive real runs produced identical hashes for all 16 top-level public artifacts, the privacy scan reported zero issues, and two complete figure renders produced identical PNG/SVG hashes. All twelve pre-v0.8 CSV hashes were unchanged.
- No community, scale-free, mechanism, syndrome, efficacy, or recommendation claim is implemented. A next optional descriptive module could quantify pairwise node/edge membership overlap across groups before any clustering or community interpretation; adjusted inference still requires a covariate contract.

## 2026-09-01 — Version 0.9.0 cross-group network membership verified

- Primary-network membership is now compared at the same prespecified thresholds. `network_group_overlap.csv` reports pairwise node/edge intersections and Jaccard; `network_membership.csv` records every public node or edge as all-group, multi-group, or single-group membership without treating non-membership as non-use.
- Real node overlap was RA-SjD 13 (Jaccard 0.361), RA-AS 12 (0.375), and SjD-AS 7 (0.175). Real edge overlap was 34 (0.200), 7 (0.044), and 6 (0.030), respectively. The lower edge overlap supports a descriptive formulation of a partly shared recurrent-item backbone with more differentiated co-prescription assembly.
- Seven items entered all three primary networks: 当归、炒枳壳、知母、苏梗、茯苓、麸炒枳壳、麸炒白术. Five edges entered all three: 当归-苏梗、炒枳壳-苏梗、知母-茯苓、知母-麸炒白术、茯苓-麸炒白术.
- The real membership union contained 45 nodes and 244 edges. Existing 15 CSV hashes remained unchanged when the two new tables were added; two consecutive v0.9 real runs produced identical hashes for all 18 public artifacts, and the privacy scan reported zero issues.
- Fifteen synthetic tests and compilation passed. The CNSPlots comparison figure uses an exact-pattern bubble matrix plus node/edge Jaccard dumbbells; two complete renders produced identical hashes for six PNG/SVG artifacts, and all three SVG files parsed successfully. Standard Matplotlib SVG was used because `mutool` is unavailable.
- Cross-group membership remains exploratory and threshold-dependent. Single-group membership is not disease specificity, and edge overlap does not establish a traditional compatibility rule, syndrome, mechanism, effectiveness, or recommendation. Adjusted inference still requires a covariate contract.
