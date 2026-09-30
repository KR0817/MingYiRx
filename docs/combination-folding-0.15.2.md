# Combination folding, dashboard 0.15.2

Frozen 2026-09-09. Presentation-only optimization using existing disclosed stable
pairs and triplets. No raw-data mining, new support estimates, or closed-itemset
claims. Preserve the original CSVs, source hashes, and primary statistical outputs.

Fold a pair under one triplet only when the pair is a strict item subset and both
rows have equal integer support_patients, equal positive integer patients, group,
stratum_type and stratum. Both must be stable, public rows in the current candidate
filter. Other pairs stay independent. Missing denominators or malformed combination
sizes cannot establish redundancy. The combination patients column is now explicitly
included in the existing public projection.

Choose one parent deterministically by Unicode lexical combination name when more
than one triplet qualifies. Each child appears once. Filter by context/search/size
before grouping; apply the display limit to root cards after grouping. Pair-only
mode remains a flat pair list. A root excluded by filtering cannot hide its child.
Native details/summary exposes every folded row with its own original statistics.
Provide an explicit checkbox to restore the flat list and a grouping count label.
Single-item dose chips remain marginal cohort summaries, not combination doses.

Acceptance: tests for same-support folding, unequal support, wrong denominator or
stratum, malformed names/sizes, ambiguous parents, input preservation, filtering,
limits and the toggle. Run existing Python/JavaScript checks. Build from the
user-finalized-B aggregate baseline, preserve all payload data except added public
denominators and dashboard version, compare source hashes, and render desktop/mobile
states with folding, expansion and flat-list restoration. No external deployment.
