# Tao Qingwen analysis migration map

The original study is a reference case, not a dependency of this repository.

| Original responsibility | Generalized module | Migration decision |
|---|---|---|
| Source hashes and GB18030 parsing | `io.py` and run manifest | Implement in core |
| Diagnosis regex functions | JSON group rules plus `cohort.py` | Implement in core |
| First-prescription prevalence | `analysis.py` | Implement in core |
| Patient-adjacent Jaccard | `analysis.py` | Implement in core |
| Dose-aware modification burden | `analysis.py` | Implement in core |
| Patient-disjoint time comparison | `analysis.py` | Implement in core |
| Prespecified temporal cut-point sensitivity | `analysis.py` | Implemented in v0.5 |
| Versioned item dictionary and dose-conflict audit | `config.py`, `analysis.py` | Implemented in v0.6 infrastructure; real mapping awaits authoritative file |
| Stable first-prescription pairs/triplets | `analysis.py` | Implemented in v0.7 without network claims |
| Matched different-patient reference | `analysis.py` | Implemented in v0.3 |
| Patient bootstrap, empirical null, BH-FDR | `analysis.py` | Implemented in v0.3 |
| Exact-match and minimum-five-control sensitivity | `analysis.py` | Implemented in v0.4 |
| Adjusted GLM | Future `inference.py` | Requires a covariate contract |
| Threshold-sensitive network | `analysis.py` | Implemented in v0.8 without scale-free claims |
| CNSPlots network and threshold figures | Optional `scripts/plot_networks.py` | Implemented in v0.8 from public aggregates only |
| Cross-disease node/edge membership overlap | `analysis.py` and optional `scripts/plot_networks.py` | Implemented in v0.9 at the prespecified primary thresholds |
| Data-to-paper evidence handoff | `docs/data-to-paper-workflow.md` and synthetic-data CI | Implemented in v0.10 without automatic claim generation |
| Patient-equal item-level addition/removal tendency | `analysis.py` | Implemented in v0.11 with direction-specific public-patient suppression |
| Local clinical review dashboard | `dashboard.py` | Implemented in v0.11 from public aggregate tables only; no raw upload or patient-specific recommendation |
| Comorbidity, demographic, and patient-year clinical views | `cohort.py`, `analysis.py`, `dashboard.py` | Implemented in v0.12 as suppressed descriptive aggregates; v0.14.1 renders annual item metrics as gap-aware line charts; local input retrieves history rather than predicting a prescription |
| Privacy-gated item gram-dose summaries | `analysis.py`, `pipeline.py`, `dashboard.py` | Added as medians/IQRs in v0.13 and replaced in v0.14 by patient-equal most frequently recorded exact gram dose(s), including explicit group ties and an exact-category privacy gate; no unit conversion or recommendation |
| Manuscript and journal packaging | Separate downstream project | Do not couple to core |

This split prevents physician-specific diagnosis strings, file paths, journal formatting, and publication decisions from contaminating the reusable analysis engine.
