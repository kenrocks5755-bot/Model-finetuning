#!/usr/bin/env python3
"""Prepare/run google/gemma-3-1b-it QLoRA training (GPU is explicit).

This script refuses to start without ``--allow-gpu``. It consumes only audited
records with ``assistant_response`` and uses AssistantOnlyCollator, so prompt
tokens do not contribute to the loss.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="google/gemma-3-1b-it")
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--allow-gpu", action="store_true", help="required safety acknowledgement")
    args = parser.parse_args()
    if not args.allow_gpu:
        raise SystemExit("Refusing to launch: this is a GPU job; pass --allow-gpu only when ready.")

    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainingArguments
    from relearn.training import AssistantOnlyCollator

    dataset = load_dataset("json", data_files=str(args.data), split="train")
    missing = [i for i, row in enumerate(dataset) if not row.get("assistant_response")]
    if missing:
        raise ValueError(f"{len(missing)} records lack audited assistant_response; refusing raw-outcome training")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype="bfloat16", bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, quantization_config=quant, device_map="auto")
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules="all-linear", task_type="CAUSAL_LM"))
    args.output.mkdir(parents=True, exist_ok=True)
    trainer = Trainer(model=model, tokenizer=tokenizer, train_dataset=dataset, data_collator=AssistantOnlyCollator(tokenizer, args.max_length), args=TrainingArguments(output_dir=str(args.output), per_device_train_batch_size=1, gradient_accumulation_steps=16, num_train_epochs=3, learning_rate=2e-4, bf16=True, logging_steps=10, save_strategy="steps", save_steps=200, report_to="none"))
    trainer.train()
    trainer.save_model(str(args.output))
    (args.output / "run_metadata.json").write_text(json.dumps({"base_model": args.model, "assistant_only_loss": True, "source_outcomes_are_not_labels": True}, indent=2) + "\n")


if __name__ == "__main__":
    main()
