"""Validate generated Wanderly dashboard JSON before backend integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_dashboard_json(payload: Any) -> list[str]:
    issues: list[str] = []

    if not isinstance(payload, dict):
        return ["root must be a JSON object"]

    if not isinstance(payload.get("assistant_message"), str) or not payload.get("assistant_message"):
        issues.append("assistant_message must be a non-empty string")

    dashboard_payload = payload.get("dashboard_payload")
    if not isinstance(dashboard_payload, dict):
        issues.append("dashboard_payload must be an object")
        return issues

    if dashboard_payload.get("schema_version") != "travel_dashboard_v1":
        issues.append("dashboard_payload.schema_version must equal travel_dashboard_v1")

    api_grounding = dashboard_payload.get("api_grounding")
    if not isinstance(api_grounding, dict):
        issues.append("dashboard_payload.api_grounding must be an object")
        return issues

    for key in ("used_api", "missing_api", "warnings"):
        if not isinstance(api_grounding.get(key), list):
            issues.append(f"dashboard_payload.api_grounding.{key} must be a list")

    return issues


def load_text(path: Path | None) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    return input("Paste generated JSON: ").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated dashboard JSON.")
    parser.add_argument("--input", type=Path, help="Path to a file containing one generated JSON object.")
    parser.add_argument("--output", type=Path, help="Optional path to write validation results as JSON.")
    args = parser.parse_args()

    result: dict[str, Any] = {"valid_json": False, "schema_valid": False, "issues": []}
    try:
        payload = json.loads(load_text(args.input))
        result["valid_json"] = True
        result["issues"] = validate_dashboard_json(payload)
        result["schema_valid"] = not result["issues"]
    except json.JSONDecodeError as exc:
        result["issues"] = [f"invalid JSON: {exc}"]

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["schema_valid"] else 1)


if __name__ == "__main__":
    main()
