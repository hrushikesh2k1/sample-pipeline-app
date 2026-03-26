import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import add, subtract


def build_snapshot():
    return {
        "app_name": "sample-pipeline-app",
        "version": 1,
        "operations": [
            {"name": "add_2_3", "result": add(2, 3)},
            {"name": "subtract_5_3", "result": subtract(5, 3)},
            {"name": "subtract_10_4", "result": subtract(10, 4)},
        ],
    }


def compare_snapshots(expected, actual):
    differences = []
    expected_ops = {item["name"]: item["result"] for item in expected.get("operations", [])}
    actual_ops = {item["name"]: item["result"] for item in actual.get("operations", [])}
    operation_names = sorted(set(expected_ops) | set(actual_ops))

    for name in operation_names:
        if expected_ops.get(name) != actual_ops.get(name):
            differences.append(
                {
                    "field": name,
                    "expected": expected_ops.get(name),
                    "actual": actual_ops.get(name),
                }
            )

    return differences


def main():
    parser = argparse.ArgumentParser(description="Compare app output with the approved regression baseline.")
    parser.add_argument("--baseline", default="baseline/expected_snapshot.json")
    parser.add_argument("--report", default="artifacts/regression-report.json")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    current_snapshot = build_snapshot()

    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(current_snapshot, indent=2) + "\n", encoding="utf-8")

    approved_snapshot = json.loads(baseline_path.read_text(encoding="utf-8"))
    differences = compare_snapshots(approved_snapshot, current_snapshot)

    report = {
        "status": "pass" if not differences else "fail",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "baseline_file": str(baseline_path),
        "difference_count": len(differences),
        "differences": differences,
        "current_snapshot": current_snapshot,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if differences:
        print("Regression check failed.")
        print(json.dumps(differences, indent=2))
        raise SystemExit(1)

    print(f"Regression check passed. Report written to {report_path}")


if __name__ == "__main__":
    main()
