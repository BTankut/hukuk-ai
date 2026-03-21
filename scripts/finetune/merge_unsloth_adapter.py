#!/usr/bin/env python3
"""Merge a Qwen3.5 LoRA adapter into a 16-bit Unsloth checkpoint."""

from __future__ import annotations

import argparse

import unsloth  # noqa: F401
from peft import PeftModel
from unsloth import FastModel


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


def main() -> None:
    args = parse_args()

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
        is_trainable=False,
    )
    clear_quant_flags(model)

    model.save_pretrained_merged(
        args.output_dir,
        tokenizer,
        save_method="merged_16bit",
    )
    print(f"Merged model saved to {args.output_dir}")


if __name__ == "__main__":
    main()
