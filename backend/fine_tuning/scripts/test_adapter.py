"""Smoke-test the base model plus LoRA adapter before merging."""

from __future__ import annotations

import json

from adapter_loader import AdapterConfig, generate_text, load_base_model_and_adapter, print_config
from test_json_schema import validate_dashboard_json


PROMPT = (
    "Plan a 2 day budget trip to Berlin for one traveler. "
    "Return only JSON using the travel_dashboard_v1 schema."
)


def main() -> None:
    config = AdapterConfig.from_env()
    print_config(config)

    tokenizer, model = load_base_model_and_adapter(config)
    text = generate_text(tokenizer, model, PROMPT, config)

    print("\nGenerated output:\n")
    print(text)

    try:
        payload = json.loads(text)
        print("\nJSON check: valid")
        issues = validate_dashboard_json(payload)
        if issues:
            print("Schema check: invalid")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("Schema check: valid")
    except json.JSONDecodeError as exc:
        print(f"\nJSON check: invalid ({exc})")


if __name__ == "__main__":
    main()
