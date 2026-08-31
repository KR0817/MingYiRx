from __future__ import annotations

import csv
import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import __version__
from .analysis import AnalysisResult, VisitBuildResult, analyze, build_visits
from .cohort import CohortResult, assign_patient_groups
from .config import AnalysisConfig, load_config
from .io import InputError, ReadResult, file_sha256, read_sources
from .privacy import PrivacyScan, scan_public_outputs


TABLE_FIELDS = {
    "cohort_summary": [
        "group",
        "patients",
        "first_prescription_patients",
        "repeat_patients",
        "visits",
        "transitions",
    ],
    "first_prescription_item_prevalence": [
        "group",
        "item_name",
        "exposed_patients",
        "group_patients",
        "prevalence",
    ],
    "longitudinal_summary": [
        "group",
        "repeat_patients",
        "transitions",
        "dose_resolved_patients",
        "dose_resolved_transitions",
        "median_patient_jaccard",
        "median_patient_retention",
        "median_patient_addition",
        "median_patient_modification_burden",
    ],
    "transition_mode_summary": [
        "group",
        "mode",
        "dose_resolved_patients",
        "dose_resolved_transitions",
        "mean_patient_proportion",
    ],
    "cross_group_similarity": [
        "group_left",
        "group_right",
        "common_public_items",
        "weighted_jaccard",
        "jensen_shannon_distance",
    ],
    "temporal_stability": [
        "group",
        "early_end_year",
        "early_patients",
        "late_patients",
        "item_universe_items",
        "weighted_jaccard",
        "jensen_shannon_distance",
        "early_core_items",
        "retained_core_items",
        "core_retention_fraction",
    ],
    "temporal_cutpoint_sensitivity": [
        "group",
        "early_end_year",
        "early_patients",
        "late_patients",
        "item_universe_items",
        "weighted_jaccard",
        "jensen_shannon_distance",
        "early_core_items",
        "retained_core_items",
        "core_retention_fraction",
    ],
    "matched_reference_summary": [
        "group",
        "patients",
        "matched_transitions",
        "potential_transitions",
        "unmatched_transitions",
        "matchable_transition_pct",
        "exact_year_stage_size_match_pct",
        "eligible_control_patients_median",
        "observed_patient_median_jaccard",
        "observed_bootstrap_ci95_low",
        "observed_bootstrap_ci95_high",
        "matched_between_patient_median_jaccard",
        "matched_between_bootstrap_ci95_low",
        "matched_between_bootstrap_ci95_high",
        "within_minus_between_median",
        "within_minus_between_bootstrap_ci95_low",
        "within_minus_between_bootstrap_ci95_high",
        "empirical_one_sided_p",
        "empirical_one_sided_bh_fdr",
    ],
    "matched_reference_sensitivity": [
        "analysis",
        "group",
        "patients",
        "transitions",
        "observed_patient_median_jaccard",
        "matched_between_patient_median_jaccard",
        "within_minus_between_median",
        "within_minus_between_bootstrap_ci95_low",
        "within_minus_between_bootstrap_ci95_high",
    ],
    "item_normalization_audit": [
        "dictionary_version",
        "dictionary_sha256",
        "dictionary_entries",
        "eligible_item_lines",
        "distinct_source_items",
        "dictionary_matched_item_lines",
        "dictionary_matched_source_items",
        "unmapped_source_items",
        "changed_item_lines",
        "canonical_items",
        "canonical_collision_visit_items",
    ],
    "dose_conflict_audit": [
        "group",
        "patients",
        "visits",
        "patients_with_conflict",
        "visits_with_conflict",
        "visit_item_conflicts",
        "patients_with_conflict_pct",
        "visits_with_conflict_pct",
    ],
}


@dataclass(frozen=True)
class ValidationContext:
    config_path: Path
    input_paths: tuple[Path, ...]
    config: AnalysisConfig
    read_result: ReadResult
    cohort_result: CohortResult
    visit_result: VisitBuildResult
    gate: str
    warnings: tuple[str, ...]


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _normalize_input_paths(input_paths: Path | Sequence[Path]) -> tuple[Path, ...]:
    if isinstance(input_paths, Path):
        return (input_paths.resolve(),)
    return tuple(Path(path).resolve() for path in input_paths)


def validate_pipeline(
    config_path: Path, input_paths: Path | Sequence[Path]
) -> ValidationContext:
    config_path = config_path.resolve()
    resolved_input_paths = _normalize_input_paths(input_paths)
    config = load_config(config_path)
    repository_root = Path(__file__).resolve().parents[2]
    if not config.synthetic_mode:
        unsafe_paths = [
            path for path in resolved_input_paths if _is_within(path, repository_root)
        ]
        if unsafe_paths:
            raise InputError("Real clinical input must remain outside the Git repository")

    read_result = read_sources(resolved_input_paths, config)
    cohort_result = assign_patient_groups(read_result.records, config)
    if not cohort_result.patient_groups:
        raise InputError("No patients were assigned to exactly one configured group")
    visit_result = build_visits(read_result.records, cohort_result.patient_groups, config)
    if not visit_result.visits_by_patient:
        raise InputError("No analyzable visits remain after cohort assignment")

    warnings = (*read_result.warnings, *cohort_result.warnings, *visit_result.warnings)
    return ValidationContext(
        config_path=config_path,
        input_paths=resolved_input_paths,
        config=config,
        read_result=read_result,
        cohort_result=cohort_result,
        visit_result=visit_result,
        gate="PASS_WITH_WARNINGS" if warnings else "PASS",
        warnings=warnings,
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(
            {
                key: (f"{value:.9f}".rstrip("0").rstrip(".") if isinstance(value, float) else value)
                for key, value in row.items()
            }
            for row in rows
        )


def _format_value(value: object) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    if not rows:
        return "No reportable rows."
    header = "| " + " | ".join(columns) + " |"
    divider = "|" + "|".join("---" for _ in columns) + "|"
    body = [
        "| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def _write_report(
    path: Path,
    context: ValidationContext,
    analysis: AnalysisResult,
) -> None:
    cohort_table = _markdown_table(
        analysis.tables["cohort_summary"], TABLE_FIELDS["cohort_summary"]
    )
    longitudinal_table = _markdown_table(
        analysis.tables["longitudinal_summary"], TABLE_FIELDS["longitudinal_summary"]
    )
    similarity_table = _markdown_table(
        analysis.tables["cross_group_similarity"], TABLE_FIELDS["cross_group_similarity"]
    )
    temporal_table = _markdown_table(
        analysis.tables["temporal_stability"], TABLE_FIELDS["temporal_stability"]
    )
    temporal_cutpoint_table = _markdown_table(
        analysis.tables["temporal_cutpoint_sensitivity"],
        TABLE_FIELDS["temporal_cutpoint_sensitivity"],
    )
    matched_table = _markdown_table(
        analysis.tables["matched_reference_summary"],
        TABLE_FIELDS["matched_reference_summary"],
    )
    matched_sensitivity_table = _markdown_table(
        analysis.tables["matched_reference_sensitivity"],
        TABLE_FIELDS["matched_reference_sensitivity"],
    )
    item_normalization_table = _markdown_table(
        analysis.tables["item_normalization_audit"],
        TABLE_FIELDS["item_normalization_audit"],
    )
    dose_conflict_table = _markdown_table(
        analysis.tables["dose_conflict_audit"],
        TABLE_FIELDS["dose_conflict_audit"],
    )
    warning_lines = "\n".join(f"- {warning}" for warning in (*context.warnings, *analysis.warnings)) or "- None"
    report = f"""# MingYiRx analysis report

**Gate:** `{context.gate if not analysis.warnings else 'PASS_WITH_WARNINGS'}`
**Project:** `{context.config.project_id}`
**Dataset:** `{context.config.dataset_id}`
**Cohort:** `{context.config.cohort_version}`

## Cohort flow

- Source patients: {context.cohort_result.total_patients}
- Assigned exclusive patients: {len(context.cohort_result.patient_groups)}
- Multiple-group patients excluded: {context.cohort_result.overlap_patients}
- Unmatched patients excluded: {context.cohort_result.unmatched_patients}

{cohort_table}

## Item normalization audit

{item_normalization_table}

## Dose conflict audit

{dose_conflict_table}

## Patient-linked adjacent-prescription change

{longitudinal_table}

## Matched same-clinician different-patient reference

{matched_table}

## Matched-reference sensitivity analyses

{matched_sensitivity_table}

## Cross-group first-prescription similarity

{similarity_table}

## Patient-disjoint temporal stress test

{temporal_table}

## Temporal cut-point sensitivity

{temporal_cutpoint_table}

## Warnings

{warning_lines}

## Interpretation boundary

These results describe recorded prescription structure and follow-up modification in the supplied record system. They do not establish effectiveness, safety, prescribing appropriateness, mechanism, syndrome differentiation, diagnostic validity, or external transportability.
"""
    path.write_text(report, encoding="utf-8")


def _config_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_hashes(output_dir: Path, names: list[str]) -> dict[str, str]:
    return {name: file_sha256(output_dir / name) for name in names}


def run_pipeline(
    config_path: Path, input_paths: Path | Sequence[Path], output_dir: Path
) -> dict[str, object]:
    context = validate_pipeline(config_path, input_paths)
    analysis = analyze(context.visit_result, context.config)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files: list[str] = []
    for table_name, rows in analysis.tables.items():
        filename = f"{table_name}.csv"
        _write_csv(output_dir / filename, TABLE_FIELDS[table_name], rows)
        generated_files.append(filename)
    _write_report(output_dir / "report.md", context, analysis)
    generated_files.append("report.md")

    privacy_scan: PrivacyScan = scan_public_outputs(output_dir)
    final_warnings = [*context.warnings, *analysis.warnings]
    if privacy_scan.issues:
        final_warnings.extend(privacy_scan.issues)
    gate = "BLOCK" if privacy_scan.issues else (
        "PASS_WITH_WARNINGS" if final_warnings else "PASS"
    )

    manifest = {
        "gate": gate,
        "project_id": context.config.project_id,
        "dataset_id": context.config.dataset_id,
        "cohort_version": context.config.cohort_version,
        "mingyirx_version": __version__,
        "python_version": platform.python_version(),
        "inputs": [
            {
                "absolute_path": audit.absolute_path,
                "filename": audit.filename,
                "sha256": audit.sha256,
                "bytes": audit.bytes,
                "rows": audit.raw_rows,
                "column_count": audit.column_count,
                "schema_sha256": audit.schema_sha256,
                "duplicate_header_names": list(audit.duplicate_header_names),
                "access_mode": "read_only",
                "contains_sensitive_data": not context.config.synthetic_mode,
                "received_date": None,
                "source_immutability": (
                    "hash_locked"
                    if audit.filename.casefold()
                    in {
                        filename.casefold()
                        for filename in context.config.expected_input_sha256
                    }
                    else "hash_recorded_unlocked"
                ),
            }
            for audit in context.read_result.source_files
        ],
        "input_reconciliation": {
            "cross_file_overlap_policy": context.config.cross_file_overlap_policy,
            "raw_rows": context.read_result.row_count,
            "cross_file_overlap_rows_detected": (
                context.read_result.cross_file_overlap_rows_detected
            ),
            "cross_file_overlap_rows_removed": (
                context.read_result.cross_file_overlap_rows_removed
            ),
            "analysis_rows": context.read_result.analysis_row_count,
        },
        "configuration": {
            "absolute_path": str(context.config_path),
            "sha256": _config_sha256(context.config_path),
            "min_public_n": context.config.min_public_n,
            "synthetic_mode": context.config.synthetic_mode,
            "early_end_year": context.config.early_end_year,
            "temporal_cutpoints": list(context.config.temporal_cutpoints),
            "core_prevalence": context.config.core_prevalence,
            "item_normalization": {
                "version": context.config.item_normalization.version,
                "dictionary_path": (
                    str(context.config.item_normalization.dictionary_path)
                    if context.config.item_normalization.dictionary_path
                    else None
                ),
                "sha256": context.config.item_normalization.dictionary_sha256,
                "entries": len(context.config.item_normalization.mappings),
            },
            "matched_reference": {
                "enabled": context.config.matched_reference.enabled,
                "assume_single_physician": (
                    context.config.matched_reference.assume_single_physician
                ),
                "random_seed": context.config.matched_reference.random_seed,
                "bootstrap_replicates": (
                    context.config.matched_reference.bootstrap_replicates
                ),
                "null_replicates": context.config.matched_reference.null_replicates,
            },
        },
        "cohort_flow": {
            "source_patients": context.cohort_result.total_patients,
            "assigned_patients": len(context.cohort_result.patient_groups),
            "overlap_excluded": context.cohort_result.overlap_patients,
            "unmatched_excluded": context.cohort_result.unmatched_patients,
            "group_counts": context.cohort_result.group_counts,
        },
        "analysis": analysis.metadata,
        "eligibility_flow": {
            "require_visit_group_match": context.config.require_visit_group_match,
            "group_mismatch_visits_excluded": (
                context.visit_result.group_mismatch_visit_count
            ),
            "eligible_item_lines": context.visit_result.eligible_item_line_count,
            "ineligible_item_lines_excluded": (
                context.visit_result.ineligible_item_line_count
            ),
            "visits_without_eligible_items_excluded": (
                context.visit_result.empty_eligible_visit_count
            ),
            "dictionary_matched_item_lines": (
                context.visit_result.dictionary_matched_item_line_count
            ),
            "changed_item_lines": context.visit_result.changed_item_line_count,
            "canonical_collision_visit_items": (
                context.visit_result.canonical_collision_visit_item_count
            ),
            "dose_conflict_visit_items": (
                context.visit_result.dose_conflict_item_count
            ),
        },
        "privacy_scan": {
            "files_scanned": privacy_scan.files_scanned,
            "issues": list(privacy_scan.issues),
        },
        "warnings": final_warnings,
        "artifacts": _artifact_hashes(output_dir, generated_files),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if gate == "BLOCK":
        raise InputError("Generated artifacts failed the privacy scan; see run_manifest.json")
    return manifest
