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

## Historical recorded gram doses

A published gram value is a distribution summary of an explicitly recorded `g` value, not a treatment recommendation. First-prescription summaries use one observation per exposed patient. Addition doses come from the prescription where the item appears; removal doses come from the preceding prescription where it was still present. Repeated changes are summarized within patient before the group median and inclusive IQR; annual changes are additionally summarized within patient-year. Other units, unresolved conflicts, and missing doses are not converted or imputed.

Dose disclosure has its own `min_public_n` gate. A prevalence or change row can remain public while its dose fields are blank because fewer than the required number of patients had a resolved gram value. Blank dose fields mean unavailable under the recording and privacy rules, not zero grams. Constituent doses shown beside a stable pair or triplet are the matching stratum's single-item first-prescription summaries, not a combination-specific regimen.

## Clinical review interface

The interactive dashboard is a local cohort-review surface over public aggregate results. It does not accept an individual patient's symptoms, examination, laboratory data, comorbidities, allergies, current medicines, pregnancy status, or treatment response. Therefore it cannot generate a clinically complete or patient-specific prescription. Users must be able to inspect the cohort denominator, calculation basis, threshold, and uncertainty boundary without relying primarily on the visual ranking.

## Comorbidity and demographic interpretation

The clinical phenotype view uses exact combinations of the configured target disease labels over a patient's complete recorded diagnosis history. It is deliberately separate from the strict single-disease manuscript cohorts. A label such as RA plus Sjögren disease means both target strings were recorded and no configured other connective-tissue-disease exclusion was recorded; it does not establish classification-criteria validity, disease chronology, primary versus secondary Sjögren disease, or a biological overlap syndrome.

Sex is the consistent mapped source value. Age is completed years at the first eligible prescription and is used only through prespecified bands. Missing or inconsistent demographics are not imputed. Public sex and age strata are one-dimensional descriptive views; comparing them does not adjust for case mix, calendar time, disease severity, visit frequency, indication, or other confounding.

The combination-minus-single item-change comparison uses mutually exclusive recorded-label phenotypes. It reports both the fraction of repeat patients ever experiencing the direction and the mean patient-level transition fraction. The latter is the primary ordering because it reduces unequal follow-up opportunity, but it does not eliminate informative visit frequency or other confounding. A positive value means only that the recorded change was more frequent in the disclosed combination phenotype under that estimand. It cannot be described as a comorbidity effect, interaction, indication, contraindication, response marker, or recommendation. Rows absent because either side did not meet the direction-specific disclosure threshold must remain unavailable.

## Patient-year evolution interpretation

Annual composition counts each patient once per calendar year using that patient's first eligible prescription in the year. Annual addition/removal assigns an adjacent transition to the year of its later visit, calculates an item-specific fraction within each patient-year, and then averages those fractions across disclosed repeat patients. These definitions reduce domination by frequent attenders but do not make calendar-year cohorts exchangeable.

Each year, item, direction, phenotype, and displayed demographic stratum remains subject to the public minimum. A missing point is suppressed or absent and must be rendered as unavailable rather than zero or interpolated. Annual movement may reflect changing case mix, record completeness, nomenclature, access, prescribing supply, or follow-up patterns; it is not evidence of effectiveness, quality improvement, disease evolution, or a causal prescribing trend.

## Local cohort-reference input

Diagnosis, sex, and age entered in the dashboard are local, transient lookup controls over already disclosed aggregate tables. They are not clinical features in a fitted prediction model. The sex and age views remain separate one-dimensional descriptions, so their results cannot be intersected, added, or interpreted as a personalized posterior probability. Returned frequent items and combinations are historical cohort summaries, not a generated formula, clinical recommendation, dose, contraindication check, or treatment plan.

## Temporal-cutpoint interpretation

Agreement across prespecified cut points supports the direction of an internal calendar-period stability finding without treating one arbitrary year as decisive. It remains an internal data-drift stress test within the supplied record system, not external validation. Differences may reflect case mix, documentation, item availability, nomenclature, or practice changes and must not be labelled clinical deterioration or improvement.

## Item and dose audit interpretation

Dictionary coverage measures how much of the eligible source vocabulary was explicitly reviewed or mapped; it is not evidence that the canonical names are pharmacologically interchangeable. Dose-conflict counts identify visit-item cells with multiple distinct positive recorded dose-unit pairs after mapping. They describe unresolved source data and exclusion from dose-resolved estimands, not medication errors, unsafe prescribing, or inappropriate changes.

## Combination interpretation

Frequent pairs and triplets are patient-level first-prescription co-occurrences. Bootstrap stability means that a prevalence threshold is likely to be reselected under resampling of the same source cohort. Lift above one means co-occurrence exceeds the product of recorded marginal frequencies; it does not establish pharmacologic interaction, traditional compatibility, therapeutic necessity, mechanism, or effectiveness. Combination rows are descriptive candidates for replication and human review.

## Network interpretation

Network nodes are internally stable recurrent items and edges are privacy-screened first-prescription co-occurrences passing a prespecified cosine threshold. Threshold-grid membership Jaccard describes how much the published node or edge set changes when analysis thresholds change. It is not external validation. Degree and weighted degree are descriptive prominence measures only; components are not automatically syndromes or therapeutic modules. No scale-free, pharmacologic, causal, efficacy, or prescription-recommendation conclusion is permitted.

Cross-group overlap compares membership in the prespecified primary networks, not raw exposure. A shared node or edge is a reproducible descriptive candidate for clinician review; a single-group member is threshold-specific and must not be called disease-specific without external validation. Absence from another published network means only that the member did not pass all configured publication thresholds there. Node and edge Jaccard values should be interpreted together because shared ingredients can be recombined into different co-prescription structures.
