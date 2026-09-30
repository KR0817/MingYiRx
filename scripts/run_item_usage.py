"""Create a separate dashboard aggregate bundle with audited usage totals."""
import argparse
import json
import shutil
from pathlib import Path

from mingyirx.io import file_sha256
from mingyirx.pipeline import validate_pipeline, _write_csv
from mingyirx.privacy import scan_public_outputs
from mingyirx.usage import item_usage_totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists')
    baseline = json.loads((args.baseline / 'run_manifest.json').read_text(encoding='utf-8'))
    if baseline['configuration']['sha256'] != file_sha256(args.config):
        raise ValueError('Baseline configuration mismatch')
    for name, digest in baseline['artifacts'].items():
        if file_sha256(args.baseline / name) != digest:
            raise ValueError('Baseline artifact mismatch')
    context = validate_pipeline(args.config, args.input)
    if context.gate == 'BLOCK':
        raise ValueError('Input validation blocked')
    if context.config.clinical_phenotype_analysis.enabled and context.clinical_visit_result is None:
        raise ValueError('Clinical visits unavailable')
    visits = context.clinical_visit_result or context.visit_result
    rows = item_usage_totals(visits.visits_by_patient, context.config.min_public_n)
    args.output.mkdir(parents=True)
    for name in baseline['artifacts']:
        shutil.copy2(args.baseline / name, args.output / name)
    table = args.output / 'item_usage_totals.csv'
    _write_csv(table, ['item_name', 'total_usage_visits'], rows)
    provenance = {
        'analysis': 'all-visit-usage-v1',
        'scope': 'clinical_population' if context.clinical_visit_result else 'strict_population',
        'count_unit': 'normalized_item_per_eligible_visit',
        'min_public_n': context.config.min_public_n,
        'config_sha256': file_sha256(args.config),
        'input_sha256': [source.sha256 for source in context.read_result.source_files],
        'dictionary_sha256': context.config.item_normalization.dictionary_sha256,
        'module_sha256': file_sha256(Path(__file__).resolve().parents[1] / 'src/mingyirx/usage.py'),
        'table_sha256': file_sha256(table),
    }
    (args.output / 'usage_provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    baseline['artifacts'][table.name] = file_sha256(table)
    (args.output / 'run_manifest.json').write_text(json.dumps(baseline, ensure_ascii=True, indent=2), encoding='utf-8')
    scan = scan_public_outputs(args.output)
    if scan.issues:
        raise ValueError('Public output privacy validation failed')
    print(json.dumps({'usage_rows': len(rows), 'privacy_issues': 0}))


if __name__ == '__main__':
    main()
