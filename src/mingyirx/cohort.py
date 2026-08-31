from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from .config import AnalysisConfig, GroupRule
from .io import LineRecord


@dataclass(frozen=True)
class CohortResult:
    patient_groups: dict[str, str]
    total_patients: int
    unmatched_patients: int
    overlap_patients: int
    group_counts: dict[str, int]
    warnings: tuple[str, ...]


def matches_group(text: str, rule: GroupRule) -> bool:
    included = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in rule.include_patterns)
    excluded = any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in rule.exclude_patterns)
    return included and not excluded


def assign_patient_groups(records: tuple[LineRecord, ...], config: AnalysisConfig) -> CohortResult:
    diagnosis_by_patient: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if record.diagnosis_text:
            diagnosis_by_patient[record.patient_id].add(record.diagnosis_text)
        else:
            diagnosis_by_patient.setdefault(record.patient_id, set())

    patient_groups: dict[str, str] = {}
    overlap_patients = 0
    unmatched_patients = 0
    group_counts = {group.name: 0 for group in config.groups}

    for patient_id, diagnosis_values in diagnosis_by_patient.items():
        full_history = " | ".join(sorted(diagnosis_values))
        matches = [group.name for group in config.groups if matches_group(full_history, group)]
        if len(matches) == 1:
            patient_groups[patient_id] = matches[0]
            group_counts[matches[0]] += 1
        elif len(matches) > 1:
            overlap_patients += 1
        else:
            unmatched_patients += 1

    warnings: list[str] = []
    if overlap_patients:
        warnings.append(f"{overlap_patients} patients matched multiple configured groups and were excluded")
    if unmatched_patients:
        warnings.append(f"{unmatched_patients} patients matched no configured group and were excluded")
    for group_name, count in group_counts.items():
        if count < config.min_public_n:
            warnings.append(
                f"Group {group_name} has {count} assigned patients, below min_public_n={config.min_public_n}"
            )

    return CohortResult(
        patient_groups=patient_groups,
        total_patients=len(diagnosis_by_patient),
        unmatched_patients=unmatched_patients,
        overlap_patients=overlap_patients,
        group_counts=group_counts,
        warnings=tuple(warnings),
    )
