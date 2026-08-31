# Analysis Contract

## Supported claim

The pipeline describes recorded prescription structure and longitudinal modification within the supplied clinical record system.

## Unsupported claims

The pipeline does not estimate treatment effectiveness, safety, comparative benefit, prescribing appropriateness, pharmacologic synergy, mechanism, diagnostic performance, or transportability.

## Required investigator decisions

Before analyzing real data, freeze and document:

1. the patient and visit identity keys;
2. the diagnosis-text phenotype expressions and exclusions;
3. eligible medication forms, units, and pharmacist dictionary version;
4. first eligible visit definition;
5. temporal period boundary;
6. public minimum cell count;
7. project, dataset, and cohort version identifiers;
8. ethics and secondary-use authorization.

Any change to patients, exclusions, group rules, primary estimand, or source hash creates a new `cohort_version`.

## Interpretation sequence

1. Start with cohort flow and missingness.
2. Describe first-prescription item prevalence.
3. Quantify within-patient adjacent change.
4. Compare the observed change with an appropriate background only in a prespecified advanced module.
5. Test time-period stability before claiming that a pattern is reusable.
6. Treat networks and clusters as visualization or hypothesis-generation tools, not clinical mechanisms.

## Matched-reference interpretation

The different-patient reference asks whether ordered prescriptions from one patient are more similar than prescriptions selected from other patients under the same configured clinician, recorded-label group, year, follow-up stage, and prescription-size hierarchy. A positive within-minus-between value supports patient-linked prescription continuity beyond that constrained background. It does not identify why prescriptions differ, whether changes were clinically appropriate, or whether patients benefited.

The exact-match-only and minimum-five-control restrictions are robustness checks on match quality and control-pool sparsity. Agreement in direction strengthens confidence that the descriptive contrast is not created solely by fallback matching or very small control pools; it does not convert the contrast into a causal effect.

## Item-level change interpretation

An addition or removal row means that at least the configured public minimum number of repeat patients experienced that recorded change. The patient-level transition fraction is calculated before group averaging so patients with many visits do not dominate. The two directions are disclosed independently; a missing direction is below the reporting rule or absent and must not be treated as zero. These historical tendencies do not determine whether an item should be added, removed, continued, or dosed for a current patient.

## Clinical review interface

The interactive dashboard is a local cohort-review surface over public aggregate results. It does not accept an individual patient's symptoms, examination, laboratory data, comorbidities, allergies, current medicines, pregnancy status, or treatment response. Therefore it cannot generate a clinically complete or patient-specific prescription. Users must be able to inspect the cohort denominator, calculation basis, threshold, and uncertainty boundary without relying primarily on the visual ranking.

## Temporal-cutpoint interpretation

Agreement across prespecified cut points supports the direction of an internal calendar-period stability finding without treating one arbitrary year as decisive. It remains an internal data-drift stress test within the supplied record system, not external validation. Differences may reflect case mix, documentation, item availability, nomenclature, or practice changes and must not be labelled clinical deterioration or improvement.

## Item and dose audit interpretation

Dictionary coverage measures how much of the eligible source vocabulary was explicitly reviewed or mapped; it is not evidence that the canonical names are pharmacologically interchangeable. Dose-conflict counts identify visit-item cells with multiple distinct positive recorded dose-unit pairs after mapping. They describe unresolved source data and exclusion from dose-resolved estimands, not medication errors, unsafe prescribing, or inappropriate changes.

## Combination interpretation

Frequent pairs and triplets are patient-level first-prescription co-occurrences. Bootstrap stability means that a prevalence threshold is likely to be reselected under resampling of the same source cohort. Lift above one means co-occurrence exceeds the product of recorded marginal frequencies; it does not establish pharmacologic interaction, traditional compatibility, therapeutic necessity, mechanism, or effectiveness. Combination rows are descriptive candidates for replication and human review.

## Network interpretation

Network nodes are internally stable recurrent items and edges are privacy-screened first-prescription co-occurrences passing a prespecified cosine threshold. Threshold-grid membership Jaccard describes how much the published node or edge set changes when analysis thresholds change. It is not external validation. Degree and weighted degree are descriptive prominence measures only; components are not automatically syndromes or therapeutic modules. No scale-free, pharmacologic, causal, efficacy, or prescription-recommendation conclusion is permitted.

Cross-group overlap compares membership in the prespecified primary networks, not raw exposure. A shared node or edge is a reproducible descriptive candidate for clinician review; a single-group member is threshold-specific and must not be called disease-specific without external validation. Absence from another published network means only that the member did not pass all configured publication thresholds there. Node and edge Jaccard values should be interpreted together because shared ingredients can be recombined into different co-prescription structures.
