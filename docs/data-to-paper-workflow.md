# Data-to-paper workflow

## Purpose

This document maps public aggregate MingYiRx outputs and restricted local provenance to manuscript sections and their code-level evidence. It is a handoff contract, not an automatic manuscript generator. Investigators remain responsible for clinical interpretation, ethics and author facts, citation verification, and final wording.

## Evidence layers

| Manuscript purpose | Aggregate evidence | Implementation source | Supported statement |
|---|---|---|---|
| Cohort flow | `cohort_summary.csv`, `run_manifest.json` | `config.py`, `cohort.py`, `pipeline.py` | Counts of source, excluded, assigned, first-prescription, and repeat patients under the frozen recorded-label rules |
| Source and terminology quality | `item_normalization_audit.csv`, `dose_conflict_audit.csv` | `io.py`, `analysis.py` | Dictionary coverage and unresolved recorded dose conflicts |
| First-prescription structure | `first_prescription_item_prevalence.csv` | `analysis.py` | Patient-level exposure prevalence in each recorded-label group |
| Stable combinations | `frequent_item_combinations.csv` | `analysis.py` | Privacy-screened patient-level pairs and triplets retained under the prespecified support and reselection rules |
| Patient-linked modification | `longitudinal_summary.csv`, `transition_mode_summary.csv` | `analysis.py` | Patient-equal adjacent-prescription continuity, addition, removal, dose-change, and modification burden |
| Item-level modification direction | `longitudinal_item_change_tendency.csv` | `analysis.py` | Privacy-screened patient prevalence and patient-equal transition fraction for each recorded item added or removed during follow-up |
| Clinical phenotype and demographics | `clinical_phenotype_summary.csv`, `clinical_first_prescription_item_prevalence.csv` | `cohort.py`, `analysis.py` | Descriptive exact target-disease signatures and separately disclosed sex or first-prescription age strata |
| Combination-versus-single modification | `clinical_item_change_comparison.csv` | `analysis.py` | Unadjusted difference in patient prevalence and patient-equal transition frequency when both item-direction cells pass disclosure |
| Patient-year evolution | `clinical_year_summary.csv`, `clinical_year_item_prevalence.csv`, `clinical_year_item_change_tendency.csv` | `analysis.py` | Annual index-prescription prevalence and later-visit-year change frequency after patient-year aggregation |
| Constrained prescribing background | `matched_reference_summary.csv`, `matched_reference_sensitivity.csv` | `analysis.py` | Difference between patient-linked continuity and matched different-patient continuity under the fixed hierarchy |
| Calendar-period stress test | `temporal_stability.csv`, `temporal_cutpoint_sensitivity.csv` | `analysis.py` | Internal stability across patient-disjoint periods and prespecified cut points |
| Distributional cross-group comparison | `cross_group_similarity.csv` | `analysis.py` | Prevalence-weighted overlap and Jensen-Shannon distance over one public item universe |
| Recurrent-item networks | `network_nodes.csv`, `network_edges.csv`, `network_threshold_sensitivity.csv` | `analysis.py`, `scripts/plot_networks.py` | Public primary-network composition and threshold dependence |
| Cross-group network membership | `network_group_overlap.csv`, `network_membership.csv` | `analysis.py`, `scripts/plot_networks.py` | Shared and non-shared primary-network members and pairwise membership Jaccard |
| Run provenance | Restricted local `run_manifest.json`; public `report.md` | `pipeline.py`, `privacy.py` | Dataset/configuration identity, input hashes, software version, reconciliation, warnings, privacy scan, and aggregate report |

## Recommended manuscript order

1. Report source reconciliation, recorded-label cohort construction, exclusions, and eligible visits.
2. Report terminology normalization coverage and dose-conflict limitations before dose-aware results.
3. Describe first-prescription item prevalence and stable combinations as the prescribing backbone.
4. Present patient-linked adjacent-prescription change as the primary longitudinal contribution, followed by privacy-screened item-level addition and removal directions.
5. Compare it with the matched different-patient background and both matching restrictions.
6. Report patient-disjoint temporal stability and the prespecified cut-point stress test.
7. Present network and cross-group membership results last as exploratory structural analyses.
8. Keep the optional clinical phenotype, demographic, and annual views in a secondary descriptive section unless they are prespecified as a separate manuscript aim.

The manuscript should keep this order so that visual network findings cannot overshadow cohort validity, longitudinal estimands, or robustness checks.

## Claim rules

| Result pattern | Permitted wording | Prohibited escalation |
|---|---|---|
| High recurrent-item prevalence | Frequently recorded or recurrent in the supplied cohort | Essential treatment, optimal therapy, or effective ingredient |
| Stable pair/triplet | Reselected under patient bootstrap from the same cohort | Synergy, compatibility mechanism, or required prescription |
| Frequently added or removed item | Frequently recorded follow-up modification among repeat patients in the supplied cohort | Instruction to add or remove the item, treatment response, indication, contraindication, or individualized suitability |
| Positive within-minus-between continuity | Patient-linked continuity exceeded the constrained different-patient background | Individualized treatment benefit or causal personalization |
| Similar direction across matching restrictions | Descriptive contrast was not created solely by the tested matching restrictions | Control of all confounding |
| Similarity across time cut points | Internal calendar-period finding was directionally stable | External validation or unchanged clinical efficacy |
| Combination-minus-single change difference | Higher recorded patient-equal change frequency in the disclosed combination phenotype | Comorbidity effect, interaction, indication, or treatment rule |
| Annual item movement | Recorded annual composition or change frequency under the patient-year estimand | Effectiveness, quality improvement, disease progression, causal trend, or forecast |
| Shared network member | Entered each thresholded public network | Universal core treatment or cross-disease mechanism |
| Single-group network member | Entered only that group's primary public network at the configured thresholds | Disease specificity, contraindication elsewhere, or non-use elsewhere |
| Network component or degree | Descriptive co-prescription structure or prominence | Syndrome, pharmacologic module, scale-free structure, or recommendation |

## Figure and table provenance

- Every reported number should be copied from a public CSV or `report.md`, never retyped from a figure.
- Figure scripts must read public aggregate files only. The current optional network figures record input and artifact hashes in `network_figure_manifest.json`.
- The optional clinical review dashboard reads five core and, when enabled, nine clinical public aggregate tables only; its controls change presentation or retrieve an existing one-dimensional stratum, not the estimand or privacy threshold.
- A manuscript table should state the relevant denominator and whether patients, visits, or transitions are the analysis unit.
- Threshold-dependent findings must report the primary threshold and the prespecified sensitivity range.
- `NA` or suppressed cells must remain unavailable; they must not be reconstructed from other totals.

## Pre-publication gate

Before a manuscript version is treated as data-locked, verify all of the following:

- The run gate is not `BLOCK`, and every warning has an explicit disposition.
- Input, configuration, cohort, dictionary, and software versions in the restricted local manifest match the manuscript record; local absolute paths are not copied into submission files.
- Row reconciliation and cohort flow match the reported Methods and Results.
- Real source files and patient-level intermediates remain outside Git.
- The public privacy scan has zero issues.
- Tables and figures were generated from the same run manifest.
- The manuscript describes diagnosis-text cohorts as recorded-label phenotypes unless independently adjudicated.
- Ethics, secondary-use authorization, pharmacist review, authorship, funding, conflicts, and journal declarations are confirmed by the responsible authors rather than inferred from code.
- No efficacy, safety, mechanism, diagnostic-validity, scale-free, or transportability claim exceeds the analysis contract.

## Reproducibility boundary

The committed repository reproduces the workflow with synthetic data. Real analyses require local read-only inputs, locked hashes, and a non-synthetic configuration. A real-data manifest may contain local absolute paths and therefore remains ignored and restricted even when its scientific tables pass privacy scanning. GitHub Actions runs only the synthetic fixture; it must never receive clinical files, private paths, credentials, or unpublished patient-level outputs.
