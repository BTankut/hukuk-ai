#!/usr/bin/env python3
"""Merge a Qwen3.5 LoRA adapter into a 16-bit Unsloth checkpoint."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import unsloth  # noqa: F401
from unsloth import FastModel
from peft import PeftModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge a LoRA adapter into a 16-bit Unsloth checkpoint."
    )
    parser.add_argument(
        "--model-name",
        default="unsloth/Qwen3.5-35B-A3B",
        help="Base model name or local path.",
    )
    parser.add_argument(
        "--adapter-path",
        required=True,
        help="Path to the trained LoRA adapter.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the merged model will be written.",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=2048,
        help="Maximum sequence length for model loading.",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.95,
        help="GPU memory utilization hint passed to Unsloth.",
    )
    return parser.parse_args()


def clear_quant_flags(model) -> None:
    for obj in (model, getattr(model, "model", None), getattr(model, "base_model", None)):
        if obj is None:
            continue
        for attr in ("is_loaded_in_4bit", "is_loaded_in_8bit"):
            if hasattr(obj, attr):
                setattr(obj, attr, False)


def looks_like_merged_model_dir(output_dir: Path) -> bool:
    if not output_dir.is_dir():
        return False
    if not (output_dir / "config.json").exists():
        return False
    weight_files = list(output_dir.glob("*.safetensors")) + list(output_dir.glob("*.bin"))
    return any(path.stat().st_size > 1_000_000_000 for path in weight_files)


def save_with_unsloth_merge(model, tokenizer, output_dir: Path) -> bool:
    model.save_pretrained_merged(
        str(output_dir),
        tokenizer,
        save_method="merged_16bit",
    )
    return looks_like_merged_model_dir(output_dir)


def save_with_hf_merge(model, tokenizer, output_dir: Path) -> None:
    merged_model = model.merge_and_unload(safe_merge=True)
    merged_model.save_pretrained(str(output_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(output_dir))


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)

    model, tokenizer = FastModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        load_in_4bit=False,
        load_in_16bit=True,
        device_map={"": "cuda:0"},
        gpu_memory_utilization=args.gpu_memory_utilization,
        use_gradient_checkpointing=False,
    )
    clear_quant_flags(model)

    model = PeftModel.from_pretrained(
        model,
        args.adapter_path,
        is_trainable=True,
    )
    clear_quant_flags(model)

    print(f"Loaded model class: {type(model).__name__}")
    print(f"Has peft_config: {hasattr(model, 'peft_config')}")
    print(f"Has merge_and_unload: {hasattr(model, 'merge_and_unload')}")

    if output_dir.exists():
        shutil.rmtree(output_dir)

    print("Attempting official Unsloth merged_16bit export...")
    if save_with_unsloth_merge(model, tokenizer, output_dir):
        print(f"Merged model saved to {args.output_dir} via Unsloth merged_16bit")
        return

    print("Unsloth merged_16bit export did not produce a valid full checkpoint; falling back to safe HF merge_and_unload().")
    if output_dir.exists():
        shutil.rmtree(output_dir)

    save_with_hf_merge(model, tokenizer, output_dir)
    if not looks_like_merged_model_dir(output_dir):
        raise RuntimeError(f"Fallback merge completed but {args.output_dir} does not look like a full merged checkpoint.")
    print(f"Merged model saved to {args.output_dir} via HF merge_and_unload fallback")


if __name__ == "__main__":
    main()
