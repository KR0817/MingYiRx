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
| Manuscript and journal packaging | Separate downstream project | Do not couple to core |

This split prevents physician-specific diagnosis strings, file paths, journal formatting, and publication decisions from contaminating the reusable analysis engine.
