# Fine-Tuning Backend

This branch stores the fine-tuning dataset, training script, adapter tests, JSON validation, base-vs-adapter comparison, and optional merge/export script. It does not contain serving code.

Model checkpoints and final merged models belong on Hugging Face or ignored local folders, not in GitHub.

## Structure

```text
backend_fine_tuning/
├── fine_tuning/
│   ├── configs/model_config.example.env
│   ├── data/processed/train.jsonl
│   ├── data/processed/validation.jsonl
│   ├── outputs/.gitkeep
│   ├── scripts/adapter_loader.py
│   ├── scripts/compare_base_vs_adapter.py
│   ├── scripts/merge_and_push.py
│   ├── scripts/test_adapter.py
│   ├── scripts/test_json_schema.py
│   └── scripts/train_unsloth.py
├── .env.example
├── README.md
└── requirements.txt
```

## Local Test Flow

1. Finish Kaggle training.
2. Identify the latest complete checkpoint.
3. Set `ADAPTER_REPO_ID` and `ADAPTER_SUBFOLDER`, or set `LOCAL_ADAPTER_PATH`.
4. Run `python test_adapter.py`.
5. Run `python test_json_schema.py --input ../outputs/<generated-output>.json` if validating a saved generation.
6. Run `python compare_base_vs_adapter.py`.
7. Run `python merge_and_push.py` only when you need a standalone merged model.

PEFT loads the adapter from the folder containing `adapter_config.json` and `adapter_model.safetensors`; do not point code directly at the `.safetensors` file.
