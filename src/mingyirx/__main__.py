from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ConfigError
from .io import InputError
from .pipeline import run_pipeline, validate_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mingyirx",
        description="Privacy-first longitudinal prescription analytics",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate input and cohort construction")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument(
        "--input", type=Path, action="append", required=True, help="Repeat for each source CSV"
    )

    run = subparsers.add_parser("run", help="Validate and generate aggregate outputs")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument(
        "--input", type=Path, action="append", required=True, help="Repeat for each source CSV"
    )
    run.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "validate":
            context = validate_pipeline(args.config, args.input)
            summary = {
                "gate": context.gate,
                "source_files": len(context.read_result.source_files),
                "source_rows": context.read_result.row_count,
                "analysis_rows": context.read_result.analysis_row_count,
                "cross_file_overlap_rows_removed": (
                    context.read_result.cross_file_overlap_rows_removed
                ),
                "source_patients": context.cohort_result.total_patients,
                "assigned_patients": len(context.cohort_result.patient_groups),
                "group_counts": context.cohort_result.group_counts,
                "warnings": list(context.warnings),
            }
        else:
            summary = run_pipeline(args.config, args.input, args.output)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (ConfigError, InputError, json.JSONDecodeError) as error:
        print(json.dumps({"gate": "BLOCK", "error": str(error)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
