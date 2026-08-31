# Project Instructions

## Project

- Name: MingYiRx longitudinal prescription analytics
- Started: 2026-08-31
- Workspace: `C:\Users\glah1\Documents\Codex\2026-08-31\git`
- Reference implementation: `F:\Codex\2026-08-21\f-baidusyncdisk`

## Objective

Build a reusable, local-first Git project for studying senior TCM physicians' medication structure and follow-up prescription modifications from longitudinal outpatient records.

## Privacy and evidence boundaries

- Never commit raw clinical data, identifiers, pseudonymization keys, patient-level derived tables, or exact dates.
- Raw inputs remain read-only and outside the repository.
- Store restricted intermediates only under ignored `work/` paths.
- Public outputs must be aggregate and apply configurable minimum-cell suppression; default minimum count is 10.
- Diagnosis-text cohorts are recorded-label phenotypes unless independently adjudicated.
- Do not infer effectiveness, safety, prescribing appropriateness, mechanism, syndrome differentiation, or diagnostic validity from uncontrolled prescribing records.
- External models and web services must never receive identifiable or patient-level unpublished clinical material.

## Engineering conventions

- Use English for code, variables, filenames, tests, and technical contracts.
- Use Python standard library first; add dependencies only when analysis requires them.
- Prefer small functions and explicit data contracts over physician-specific hard-coded scripts.
- Configuration defines source column mapping, disease rules, item eligibility, privacy thresholds, and analysis periods.
- Every run records project/dataset/cohort identity, input hashes, configuration hash, software versions, row-count reconciliation, and validation status.
- Report gates as `PASS`, `PASS_WITH_WARNINGS`, or `BLOCK`.

## Repository layout

- `src/mingyirx/`: reusable analysis code.
- `configs/`: non-sensitive example configuration.
- `data/synthetic/`: synthetic demonstration data only.
- `tests/`: deterministic synthetic-data tests.
- `work/`: ignored restricted intermediates and private run state.
- `outputs/`: ignored generated results except documented examples when explicitly reviewed.
- `docs/`: analysis contracts and interpretation guidance.

## Verification

- Validate schema, identifiers, visit ordering, duplicate rows, missingness, date parsing, medication normalization, dose conflicts, cohort exclusivity, and source hashes.
- Verify patient-level summaries precede group-level summaries for longitudinal analyses.
- Test privacy suppression and scan generated public outputs for direct-identifier columns and common identifier patterns.
- Use synthetic data for all committed examples and tests.

## Commands

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m mingyirx validate --config configs\example.json --input data\synthetic\prescriptions.csv
python -m mingyirx run --config configs\example.json --input data\synthetic\prescriptions.csv --output outputs\demo
```
