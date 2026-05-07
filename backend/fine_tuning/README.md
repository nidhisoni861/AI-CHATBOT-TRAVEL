# Fine-Tuning

The model should behave as a travel reasoning and formatting assistant. It should not act as a live travel database. The serving backend/API will provide current flights, hotels, weather, and events.

## Scripts

- `scripts/train_unsloth.py`: train or resume the LoRA adapter.
- `scripts/adapter_loader.py`: load the base model and attach a Hugging Face or local adapter checkpoint.
- `scripts/test_adapter.py`: smoke-test base model plus adapter generation.
- `scripts/test_json_schema.py`: validate generated JSON for frontend safety.
- `scripts/compare_base_vs_adapter.py`: compare the same prompt on base model vs fine-tuned adapter.
- `scripts/merge_and_push.py`: optional later export step for a standalone merged Hugging Face model.

## Expected JSON Checks

`test_json_schema.py` checks:

- valid JSON
- `assistant_message` exists
- `dashboard_payload` exists
- `dashboard_payload.schema_version` is `travel_dashboard_v1`
- `dashboard_payload.api_grounding` exists
- `used_api`, `missing_api`, and `warnings` are lists

Keep the adapter separate first for testing and backend model selection. Merge only when a standalone model export is needed.
