"""Compare base-model output against base + LoRA adapter output."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapter_loader import (
    AdapterConfig,
    generate_text,
    load_base_model_and_adapter,
    load_base_model_only,
    print_config,
)
from test_json_schema import validate_dashboard_json


DEFAULT_PROMPT = (
    "You are given API_CONTEXT with available travel data. Plan a 2 day budget trip to Berlin "
    "for one traveler. Return only a JSON object with assistant_message and dashboard_payload. "
    "The dashboard_payload.schema_version must be travel_dashboard_v1 and api_grounding must "
    "state which APIs were used or missing.\n\n"
    "API_CONTEXT: {\"flights\": [], \"hotels\": [], \"weather\": [], \"events\": []}"
)


def evaluate_output(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"valid_json": False, "schema_valid": False, "issues": [f"invalid JSON: {exc}"]}

    issues = validate_dashboard_json(payload)
    return {"valid_json": True, "schema_valid": not issues, "issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare base and adapter outputs.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "base_vs_adapter_comparison.json",
    )
    args = parser.parse_args()

    config = AdapterConfig.from_env()
    print_config(config)

    print("\nLoading base model...")
    base_tokenizer, base_model = load_base_model_only(config)
    base_text = generate_text(base_tokenizer, base_model, args.prompt, config)
    del base_model

    print("Loading adapter model...")
    adapter_tokenizer, adapter_model = load_base_model_and_adapter(config)
    adapter_text = generate_text(adapter_tokenizer, adapter_model, args.prompt, config)

    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_model_id": config.base_model_id,
        "adapter_repo_id": config.adapter_repo_id,
        "adapter_subfolder": config.adapter_subfolder,
        "local_adapter_path": config.local_adapter_path,
        "prompt": args.prompt,
        "base": {
            "output": base_text,
            "evaluation": evaluate_output(base_text),
        },
        "adapter": {
            "output": adapter_text,
            "evaluation": evaluate_output(adapter_text),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\nSaved comparison to: {args.output}")
    print("\nBase evaluation:")
    print(json.dumps(result["base"]["evaluation"], indent=2))
    print("\nAdapter evaluation:")
    print(json.dumps(result["adapter"]["evaluation"], indent=2))


if __name__ == "__main__":
    main()
