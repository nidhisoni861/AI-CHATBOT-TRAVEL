"""Load a base model and optionally attach a PEFT/LoRA adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: str | os.PathLike[str] | None = None) -> None:
    """Load environment variables from .env files when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    if path:
        load_dotenv(path)
        return

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "configs" / "model_config.example.env",
        script_dir.parents[2] / ".env",
        script_dir.parents[2] / ".env.example",
    ]
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)


@dataclass(frozen=True)
class AdapterConfig:
    base_model_id: str
    adapter_repo_id: str
    adapter_subfolder: str
    local_adapter_path: str
    model_temperature: float
    model_max_new_tokens: int
    hf_token: str | None

    @classmethod
    def from_env(cls) -> "AdapterConfig":
        load_env_file()
        return cls(
            base_model_id=os.getenv("BASE_MODEL_ID", "unsloth/Llama-3.2-3B-Instruct"),
            adapter_repo_id=os.getenv("ADAPTER_REPO_ID", "Naman-1718/wanderly-training-backup"),
            adapter_subfolder=os.getenv("ADAPTER_SUBFOLDER", "checkpoint-1952").strip("/"),
            local_adapter_path=os.getenv("LOCAL_ADAPTER_PATH", "").strip(),
            model_temperature=float(os.getenv("MODEL_TEMPERATURE", "0.2")),
            model_max_new_tokens=int(os.getenv("MODEL_MAX_NEW_TOKENS", "900")),
            hf_token=os.getenv("HF_TOKEN") or os.getenv("HF_API_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN"),
        )


def adapter_source(config: AdapterConfig) -> str:
    return config.local_adapter_path or config.adapter_repo_id


def _adapter_kwargs(config: AdapterConfig) -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if not config.local_adapter_path and config.adapter_subfolder:
        kwargs["subfolder"] = config.adapter_subfolder
    return kwargs


def validate_adapter_files(config: AdapterConfig) -> None:
    """Ensure the adapter source contains the PEFT files we need."""
    if config.local_adapter_path:
        adapter_dir = Path(config.local_adapter_path)
        missing = [
            name
            for name in ("adapter_config.json", "adapter_model.safetensors")
            if not (adapter_dir / name).exists()
        ]
        if missing:
            raise FileNotFoundError(f"Missing adapter file(s) in {adapter_dir}: {', '.join(missing)}")
        return

    from huggingface_hub import hf_hub_download

    common_kwargs = {
        "repo_id": config.adapter_repo_id,
        "token": config.hf_token,
        **_adapter_kwargs(config),
    }
    hf_hub_download(filename="adapter_config.json", **common_kwargs)
    hf_hub_download(filename="adapter_model.safetensors", **common_kwargs)


def load_base_model_and_adapter(config: AdapterConfig | None = None):
    """Return tokenizer and model with the LoRA adapter attached."""
    config = config or AdapterConfig.from_env()
    validate_adapter_files(config)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        adapter_source(config),
        token=config.hf_token,
        trust_remote_code=True,
        **_adapter_kwargs(config),
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

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
    model.eval()
    return tokenizer, model


def load_base_model_only(config: AdapterConfig | None = None):
    """Return tokenizer and the base model without attaching the adapter."""
    config = config or AdapterConfig.from_env()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        config.base_model_id,
        token=config.hf_token,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_id,
        token=config.hf_token,
        torch_dtype=dtype if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model


def generate_text(tokenizer, model, prompt: str, config: AdapterConfig) -> str:
    """Generate text from a single user prompt."""
    import torch

    messages = [{"role": "user", "content": prompt}]
    if getattr(tokenizer, "chat_template", None):
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        input_text = prompt

    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    do_sample = config.model_temperature > 0
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=config.model_max_new_tokens,
            do_sample=do_sample,
            temperature=config.model_temperature if do_sample else None,
            top_p=0.9 if do_sample else None,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def print_config(config: AdapterConfig) -> None:
    subfolder = config.adapter_subfolder or "<repo root>"
    print(f"Base model      : {config.base_model_id}")
    if config.local_adapter_path:
        print(f"Local adapter   : {config.local_adapter_path}")
    else:
        print(f"Adapter repo    : {config.adapter_repo_id}")
        print(f"Adapter folder  : {subfolder}")
    print(f"Temperature     : {config.model_temperature}")
    print(f"Max new tokens  : {config.model_max_new_tokens}")
    print(f"HF token present: {bool(config.hf_token)}")
