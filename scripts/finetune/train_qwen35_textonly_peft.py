#!/usr/bin/env python3
"""Minimal text-only Qwen3.5-35B-A3B PEFT trainer."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunConfig:
    model_name: str
    train_file: Path
    output_dir: Path
    max_seq_length: int
    trust_remote_code: bool
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    lora_bias: str
    lora_target_modules: list[str]
    gradient_checkpointing: bool
    num_train_epochs: float
    per_device_train_batch_size: int
    gradient_accumulation_steps: int
    warmup_steps: int
    learning_rate: float
    logging_steps: int
    save_steps: int
    max_steps: int
    weight_decay: float
    lr_scheduler_type: str
    optim: str
    seed: int
    dataloader_num_workers: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text-only PEFT train/smoke for Qwen3.5-35B-A3B")
    parser.add_argument(
        "--config",
        default="configs/finetune/unsloth_sft_qwen35_35b_a3b.json",
        help="Path to JSON config.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output dir override. Defaults to config.output.dir/text-only-peft.",
    )
    parser.add_argument(
        "--max-train-samples",
        type=int,
        default=0,
        help="Cap number of training rows for smoke. 0 = use all rows.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override max_steps for smoke.",
    )
    parser.add_argument(
        "--num-train-epochs",
        type=float,
        default=None,
        help="Optional epoch override.",
    )
    parser.add_argument(
        "--dtype",
        choices=["bf16", "fp16", "fp32"],
        default="bf16",
        help="Compute dtype for model load.",
    )
    parser.add_argument(
        "--train-device",
        default="auto",
        help=(
            'Single-device target for training model load. "auto" => cuda:0 if available, '
            'else cpu. Use "none" only to bypass and use --device-map directly.'
        ),
    )
    parser.add_argument(
        "--device-map",
        default="auto",
        help='Fallback Hugging Face device_map value (used only when --train-device=none).',
    )
    parser.add_argument(
        "--preload-hook",
        default=None,
        help="Optional hook module:function executed before model load.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + tokenize + setup only; skip trainer.train().",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_run_config(cfg: dict[str, Any], args: argparse.Namespace) -> RunConfig:
    model_cfg = cfg.get("model", {})
    data_cfg = cfg.get("data", {})
    lora_cfg = cfg.get("lora", {})
    train_cfg = cfg.get("training", {})
    out_cfg = cfg.get("output", {})

    raw_output_dir = args.output_dir
    if raw_output_dir is None:
        base = out_cfg.get("dir", "artifacts/finetune/text-only-peft")
        raw_output_dir = str(Path(base) / "text-only-peft")

    max_steps = train_cfg.get("max_steps", -1)
    if args.max_steps is not None:
        max_steps = args.max_steps

    epochs = train_cfg.get("num_train_epochs", train_cfg.get("epochs", 1))
    if args.num_train_epochs is not None:
        epochs = args.num_train_epochs

    grad_ckpt_raw = lora_cfg.get("gradient_checkpointing", False)
    gradient_checkpointing = bool(grad_ckpt_raw)
    if isinstance(grad_ckpt_raw, str):
        gradient_checkpointing = grad_ckpt_raw.lower() not in {"", "false", "0", "none"}

    return RunConfig(
        model_name=model_cfg.get("name", "Qwen/Qwen3.5-35B-A3B"),
        train_file=Path(data_cfg.get("train_file", "data/finetune/sft/final_train.jsonl")),
        output_dir=Path(raw_output_dir),
        max_seq_length=int(model_cfg.get("max_seq_length", 2048)),
        trust_remote_code=bool(model_cfg.get("trust_remote_code", True)),
        lora_r=int(lora_cfg.get("r", 16)),
        lora_alpha=int(lora_cfg.get("alpha", 32)),
        lora_dropout=float(lora_cfg.get("dropout", 0.0)),
        lora_bias=str(lora_cfg.get("bias", "none")),
        lora_target_modules=list(lora_cfg.get("target_modules", [])),
        gradient_checkpointing=gradient_checkpointing,
        num_train_epochs=float(epochs),
        per_device_train_batch_size=int(train_cfg.get("per_device_train_batch_size", 1)),
        gradient_accumulation_steps=int(train_cfg.get("gradient_accumulation_steps", 1)),
        warmup_steps=int(train_cfg.get("warmup_steps", 0)),
        learning_rate=float(train_cfg.get("learning_rate", 2e-5)),
        logging_steps=int(train_cfg.get("logging_steps", 10)),
        save_steps=int(train_cfg.get("save_steps", 100)),
        max_steps=int(max_steps),
        weight_decay=float(train_cfg.get("weight_decay", 0.0)),
        lr_scheduler_type=str(train_cfg.get("lr_scheduler_type", "cosine")),
        optim=map_optimizer(str(train_cfg.get("optimizer", "adamw_8bit"))),
        seed=int(train_cfg.get("seed", 3407)),
        dataloader_num_workers=int(train_cfg.get("dataloader_num_workers", 2)),
    )


def map_optimizer(name: str) -> str:
    mapping = {
        "adamw_8bit": "adamw_bnb_8bit",
        "paged_adamw_8bit": "paged_adamw_8bit",
        "adamw_torch": "adamw_torch",
    }
    return mapping.get(name, name)


def maybe_run_preload_hook(hook: str | None) -> None:
    if not hook:
        return

    if ":" not in hook:
        raise ValueError("--preload-hook format must be module:function")

    module_name, func_name = hook.split(":", 1)
    module = importlib.import_module(module_name)
    fn = getattr(module, func_name)
    print(f"[INFO] Running preload hook: {module_name}:{func_name}", flush=True)
    fn()


def resolve_dtype(name: str):
    import torch

    if name == "bf16":
        return torch.bfloat16
    if name == "fp16":
        return torch.float16
    return torch.float32


def resolve_train_device(train_device_arg: str, torch) -> str | None:
    cleaned = (train_device_arg or "auto").strip()
    raw = cleaned.lower()
    if raw in {"", "auto"}:
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if raw in {"none", "off", "disable", "disabled"}:
        return None
    if raw.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("[FAIL] --train-device cuda* istendi ama CUDA gorunmuyor.")
    return cleaned


def assert_training_device_integrity(model, train_device: str | None) -> None:
    meta_params = [
        name for name, param in model.named_parameters() if getattr(param, "device", None) and param.device.type == "meta"
    ]
    if meta_params:
        preview = ", ".join(meta_params[:8])
        raise SystemExit(
            "[FAIL] Meta device param tespit edildi (ilkler: "
            f"{preview}). device_map=auto/cpu-offload training icin desteklenmiyor."
        )

    if train_device and hasattr(model, "hf_device_map"):
        mapped_devices = {str(value) for value in model.hf_device_map.values()}
        if any(device in {"cpu", "disk", "meta"} for device in mapped_devices):
            raise SystemExit(
                "[FAIL] hf_device_map cpu/disk/meta offload iceriyor. "
                "Training icin --train-device ile tek cihaza yukleme zorunlu."
            )


def peak_memory_gb() -> float:
    import torch

    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / (1024**3)


def peak_reserved_memory_gb() -> float:
    import torch

    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_reserved() / (1024**3)


class PerfCallback:
    """Trainer callback for simple step-time + memory logging."""

    def __init__(self) -> None:
        self.step_start: float | None = None
        self.step_times: list[float] = []

    def on_train_begin(self, args, state, control, **kwargs):
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        self.step_times.clear()
        self.step_start = None

    def on_step_begin(self, args, state, control, **kwargs):
        self.step_start = time.perf_counter()

    def on_step_end(self, args, state, control, **kwargs):
        if self.step_start is None:
            return
        self.step_times.append(time.perf_counter() - self.step_start)
        self.step_start = None

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not self.step_times:
            return
        latest = self.step_times[-1]
        avg = sum(self.step_times) / len(self.step_times)
        msg = f"[PERF] step={state.global_step} step_time_s={latest:.3f} avg_step_time_s={avg:.3f}"
        mem = peak_memory_gb()
        mem_reserved = peak_reserved_memory_gb()
        if mem > 0:
            msg += f" max_mem_allocated_gb={mem:.2f}"
        if mem_reserved > 0:
            msg += f" max_mem_reserved_gb={mem_reserved:.2f}"
        print(msg, flush=True)

    def on_train_end(self, args, state, control, **kwargs):
        if not self.step_times:
            return
        avg = sum(self.step_times) / len(self.step_times)
        print(
            f"[PERF] train_done steps={len(self.step_times)} "
            f"avg_step_time_s={avg:.3f} "
            f"peak_mem_allocated_gb={peak_memory_gb():.2f} "
            f"peak_mem_reserved_gb={peak_reserved_memory_gb():.2f}",
            flush=True,
        )


def build_prompt(instruction: str, inp: str) -> str:
    return f"{instruction.strip()}\n\n{inp.strip()}\n\nYanit:"


def main() -> int:
    args = parse_args()
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"[FAIL] Config bulunamadi: {cfg_path}")

    cfg = load_json(cfg_path)
    run_cfg = parse_run_config(cfg, args)

    if not run_cfg.train_file.exists():
        raise SystemExit(f"[FAIL] Train file bulunamadi: {run_cfg.train_file}")

    maybe_run_preload_hook(args.preload_hook)

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Trainer,
        TrainerCallback,
        TrainingArguments,
        set_seed,
    )

    try:
        from transformers import Qwen3_5MoeForCausalLM
    except Exception:
        try:
            from transformers.models.qwen3_5_moe.modeling_qwen3_5_moe import Qwen3_5MoeForCausalLM
        except Exception:
            try:
                from transformers.models.qwen3_moe.modeling_qwen3_moe import Qwen3_5MoeForCausalLM
            except Exception as exc:
                raise SystemExit(
                    "[FAIL] Qwen3_5MoeForCausalLM import edilemedi. "
                    "Transformers surumunuzde text-only sinif yolu dogrulanmali."
                ) from exc

    class _PerfHFCallback(PerfCallback, TrainerCallback):
        pass

    print(f"[INFO] config={cfg_path}")
    print(f"[INFO] model={run_cfg.model_name}")
    print(f"[INFO] train_file={run_cfg.train_file}")
    print(f"[INFO] output_dir={run_cfg.output_dir}")
    if args.max_train_samples > 0:
        print(f"[INFO] max_train_samples={args.max_train_samples}")
    print(f"[INFO] max_steps={run_cfg.max_steps}")
    print(f"[INFO] train_device_arg={args.train_device}")

    dtype = resolve_dtype(args.dtype)
    train_device = resolve_train_device(args.train_device, torch)

    if train_device is None:
        if not args.dry_run:
            raise SystemExit(
                "[FAIL] --train-device=none yalnizca dry-run/load-probe icin kullanilabilir. "
                "Training icin tek cihaz zorunlu."
            )
        model_device_map: str | dict[str, str] = args.device_map
        print(f"[WARN] single-device kapali; fallback device_map={args.device_map}")
    else:
        model_device_map = {"": train_device}
        print(f"[INFO] train_device={train_device} single_device_load=enabled")

    load_t0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(run_cfg.model_name, trust_remote_code=run_cfg.trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = Qwen3_5MoeForCausalLM.from_pretrained(
        run_cfg.model_name,
        torch_dtype=dtype,
        trust_remote_code=run_cfg.trust_remote_code,
        low_cpu_mem_usage=True,
        device_map=model_device_map,
    )

    model_cls_name = model.__class__.__name__
    if "conditionalgeneration" in model_cls_name.lower():
        raise SystemExit(f"[FAIL] Wrong model class loaded: {model_cls_name}")
    print(f"[INFO] loaded_model_class={model_cls_name}")

    assert_training_device_integrity(model, train_device)
    if hasattr(model, "hf_device_map"):
        mapped_devices = sorted({str(value) for value in model.hf_device_map.values()})
        print(f"[INFO] hf_device_map_unique={mapped_devices}")

    print(f"[PERF] load_time_s={time.perf_counter() - load_t0:.2f}")

    peft_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=run_cfg.lora_r,
        lora_alpha=run_cfg.lora_alpha,
        lora_dropout=run_cfg.lora_dropout,
        bias=run_cfg.lora_bias,
        target_modules=run_cfg.lora_target_modules,
    )
    model = get_peft_model(model, peft_cfg)

    if run_cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    model.print_trainable_parameters()

    dataset = load_dataset("json", data_files=str(run_cfg.train_file), split="train")
    total_rows = len(dataset)
    if args.max_train_samples > 0:
        dataset = dataset.select(range(min(args.max_train_samples, total_rows)))
    print(f"[INFO] dataset_rows_total={total_rows} dataset_rows_used={len(dataset)}")

    def tokenize_row(row: dict[str, Any]) -> dict[str, list[int]]:
        prompt = build_prompt(str(row.get("instruction", "")), str(row.get("input", "")))
        answer = str(row.get("output", "")).strip()
        prompt_ids = tokenizer(prompt, add_special_tokens=True, truncation=False)["input_ids"]
        answer_ids = tokenizer(answer, add_special_tokens=False, truncation=False)["input_ids"]
        answer_ids.append(tokenizer.eos_token_id)
        input_ids = (prompt_ids + answer_ids)[: run_cfg.max_seq_length]
        labels = ([-100] * len(prompt_ids) + answer_ids)[: run_cfg.max_seq_length]
        if all(value == -100 for value in labels):
            labels[-1] = input_ids[-1]
        return {
            "input_ids": input_ids,
            "attention_mask": [1] * len(input_ids),
            "labels": labels,
        }

    tokenized = dataset.map(
        tokenize_row,
        remove_columns=dataset.column_names,
        desc="Tokenizing text-only SFT dataset",
    )

    run_cfg.output_dir.mkdir(parents=True, exist_ok=True)
    set_seed(run_cfg.seed)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    training_args = TrainingArguments(
        output_dir=str(run_cfg.output_dir),
        num_train_epochs=run_cfg.num_train_epochs,
        per_device_train_batch_size=run_cfg.per_device_train_batch_size,
        gradient_accumulation_steps=run_cfg.gradient_accumulation_steps,
        warmup_steps=run_cfg.warmup_steps,
        learning_rate=run_cfg.learning_rate,
        logging_steps=max(1, run_cfg.logging_steps),
        save_steps=max(1, run_cfg.save_steps),
        max_steps=run_cfg.max_steps,
        weight_decay=run_cfg.weight_decay,
        lr_scheduler_type=run_cfg.lr_scheduler_type,
        optim=run_cfg.optim,
        bf16=(args.dtype == "bf16"),
        fp16=(args.dtype == "fp16"),
        dataloader_num_workers=run_cfg.dataloader_num_workers,
        report_to="none",
        remove_unused_columns=False,
        seed=run_cfg.seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
        callbacks=[_PerfHFCallback()],
    )

    if args.dry_run:
        print("[RESULT] DRY_RUN_OK")
        print(f"[INFO] peak_mem_allocated_gb={peak_memory_gb():.2f}")
        print(f"[INFO] peak_mem_reserved_gb={peak_reserved_memory_gb():.2f}")
        return 0

    train_t0 = time.perf_counter()
    train_result = trainer.train()
    train_sec = time.perf_counter() - train_t0

    adapter_dir = run_cfg.output_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    print(f"[PERF] train_time_s={train_sec:.2f}")
    print(f"[PERF] peak_mem_allocated_gb={peak_memory_gb():.2f}")
    print(f"[PERF] peak_mem_reserved_gb={peak_reserved_memory_gb():.2f}")
    print(f"[INFO] train_global_steps={train_result.global_step}")
    print(f"[RESULT] TRAIN_OK adapter_dir={adapter_dir}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(main())
