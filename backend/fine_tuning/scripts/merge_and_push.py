"""Merge the LoRA adapter into the base model and push the merged model to HF."""

from __future__ import annotations

import os
from pathlib import Path

from adapter_loader import AdapterConfig, _adapter_kwargs, adapter_source, print_config, validate_adapter_files


def main() -> None:
    config = AdapterConfig.from_env()
    merged_model_repo_id = os.getenv("MERGED_MODEL_REPO_ID", "Naman-1718/wanderly-llama32-3b-merged")
    local_output_dir = Path(os.getenv("MERGED_MODEL_LOCAL_DIR", "merged_model")).resolve()

    print_config(config)
    print(f"Merged repo     : {merged_model_repo_id}")
    print(f"Local output    : {local_output_dir}")
    validate_adapter_files(config)

    import torch
    from huggingface_hub import create_repo
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_id,
        token=config.hf_token,
        torch_dtype=dtype if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(
        model,
        adapter_source(config),
        token=config.hf_token,
        **_adapter_kwargs(config),
    )
    merged_model = model.merge_and_unload()

    tokenizer = AutoTokenizer.from_pretrained(
        adapter_source(config),
        token=config.hf_token,
        trust_remote_code=True,
        **_adapter_kwargs(config),
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    local_output_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(local_output_dir, safe_serialization=True)
    tokenizer.save_pretrained(local_output_dir)

    create_repo(merged_model_repo_id, token=config.hf_token, private=False, exist_ok=True)
    merged_model.push_to_hub(merged_model_repo_id, token=config.hf_token, safe_serialization=True)
    tokenizer.push_to_hub(merged_model_repo_id, token=config.hf_token)

    print(f"\nMerged model pushed to: {merged_model_repo_id}")
    print("Keep this repo ID for the serving/backend deployment branch.")


if __name__ == "__main__":
    main()
