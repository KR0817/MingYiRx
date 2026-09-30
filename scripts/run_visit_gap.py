"""Run the frozen secondary visit-gap analysis without replacing primary outputs."""
import argparse
import json
from pathlib import Path

from mingyirx.followup import visit_gap_sensitivity
from mingyirx.io import file_sha256
from mingyirx.pipeline import _write_csv, validate_pipeline
from mingyirx.privacy import scan_public_outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists')
    context = validate_pipeline(args.config, args.input)
    rows = visit_gap_sensitivity(context.visit_result.visits_by_patient, context.config.min_public_n)
    args.output.mkdir(parents=True)
    table = args.output / 'visit_gap_sensitivity.csv'
    _write_csv(table, list(rows[0]), rows)
    manifest = {
        'analysis': 'visit-gap-v1', 'cohort_version': context.config.cohort_version,
        'dataset_id': context.config.dataset_id, 'decision_basis': 'user_finalized_column_b',
        'min_public_n': context.config.min_public_n, 'bootstrap_replicates': 1000, 'seed': 20260909,
        'windows_days': ['positive', [1,30], [1,90], [1,180]],
        'same_day': 'excluded_from_secondary_only', 'scope': 'strict_recorded_label_cohorts',
        'config_sha256': file_sha256(args.config),
        'input_sha256': [item.sha256 for item in context.read_result.source_files],
        'dictionary_sha256': context.config.item_normalization.dictionary_sha256,
        'module_sha256': file_sha256(Path(__file__).resolve().parents[1] / 'src/mingyirx/followup.py'),
        'table_sha256': file_sha256(table),
    }
    (args.output / 'analysis_provenance.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    scan = scan_public_outputs(args.output)
    if scan.issues:
        raise ValueError('Public output privacy validation failed')
    print(json.dumps({'gate':'PASS_WITH_WARNINGS', 'rows':len(rows), 'privacy_issues':0,
                      'interpretation':'descriptive_exploratory_sensitivity'}))


if __name__ == '__main__':
    main()
