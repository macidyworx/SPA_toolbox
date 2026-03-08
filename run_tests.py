#!/usr/bin/env python
"""
Test runner wrapper for SPA_toolbox.

Runs pytest and filters JSON report to show only failed tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py -t tests/test_dog_box/  # Run specific path
    python run_tests.py -t tests/test_dog_box/test_ssotsif.py::test_valid_sif  # Run specific test
    python run_tests.py -t tests/test_clean_fields.py tests/test_last_row.py  # Run multiple
"""

import subprocess
import json
import sys
from pathlib import Path
import argparse


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SPA_toolbox tests with failure-only JSON report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                              # All tests
  python run_tests.py -t tests/test_dog_box/       # By path
  python run_tests.py -t tests/test_dog_box/test_ssotsif.py::test_valid_sif
  python run_tests.py -t tests/test_clean_fields.py tests/test_last_row.py
  python run_tests.py -m file_sorter               # By marker
        """
    )

    parser.add_argument(
        '-t', '--tests',
        nargs='*',
        help='Specific test paths or test functions to run (space-separated)'
    )

    parser.add_argument(
        '-m', '--marker',
        help='Run tests by marker (e.g., clean_fields, dog_box, file_sorter)'
    )

    parser.add_argument(
        '-k', '--keyword',
        help='Run tests by keyword pattern (e.g., "sif or work_files")'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all tests (including passed tests) in output'
    )

    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Do not generate JSON report'
    )

    return parser.parse_args()


def build_pytest_command(args):
    """Build the pytest command based on arguments."""
    # Use .venv/bin/pytest if it exists, otherwise just pytest
    pytest_exe = ".venv/bin/pytest" if Path(".venv/bin/pytest").exists() else "pytest"
    cmd = [pytest_exe]

    # Add verbosity
    cmd.append("-v")

    # Add JSON report unless disabled
    if not args.no_json:
        cmd.extend(["--json-report", "--json-report-file=.report.json"])

    # Add specific test selection
    if args.tests and args.tests:  # -t with specific tests
        cmd.extend(args.tests)
    elif args.marker:  # -m by marker
        cmd.extend(["-m", args.marker])
    elif args.keyword:  # -k by keyword
        cmd.extend(["-k", args.keyword])
    else:  # No args = run all tests
        cmd.append("tests")

    return cmd


def filter_json_report():
    """Filter JSON report to show only failed tests."""
    report_path = Path(".report.json")

    if not report_path.exists():
        return None

    try:
        with open(report_path) as f:
            data = json.load(f)

        # Extract test results
        all_tests = data.get('tests', [])
        failed_tests = [t for t in all_tests if t.get('outcome') == 'failed']
        passed_tests = [t for t in all_tests if t.get('outcome') == 'passed']
        skipped_tests = [t for t in all_tests if t.get('outcome') == 'skipped']

        # Update data with only failures
        data['tests'] = failed_tests

        # Write filtered report
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)

        return {
            'total': len(all_tests),
            'passed': len(passed_tests),
            'failed': len(failed_tests),
            'skipped': len(skipped_tests),
        }

    except Exception as e:
        print(f"⚠️  Error processing JSON report: {e}")
        return None


def print_summary(stats):
    """Print test summary."""
    if not stats:
        return

    total = stats['total']
    passed = stats['passed']
    failed = stats['failed']
    skipped = stats['skipped']

    # Build summary line
    parts = []
    if passed:
        parts.append(f"✅ {passed} passed")
    if failed:
        parts.append(f"❌ {failed} failed")
    if skipped:
        parts.append(f"⏭️  {skipped} skipped")

    summary = " | ".join(parts)
    print(f"\n{summary}\n")

    if failed > 0:
        print(f"📋 Failure details written to: .report.json")
    elif total > 0:
        print("🎉 All tests passed!")


def main():
    """Main entry point."""
    args = parse_args()

    # Build pytest command
    cmd = build_pytest_command(args)

    # Run pytest
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    # Post-process JSON report if it exists
    if not args.no_json and not args.verbose:
        stats = filter_json_report()
        print_summary(stats)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
