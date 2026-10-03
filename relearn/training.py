"""Chat formatting and assistant-only causal-LM collation.

Training examples must contain an audited ``assistant_response``. The canonical
source outcome/error fields are never silently converted into misconception
targets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def make_prompt(record: dict[str, Any]) -> str:
    return (
        "You are a patient Python tutor. Diagnose the learner's code and explain "
        "the next useful correction.\n\n"
        f"Question:\n{record['question']}\n\n"
        f"Learner code:\n```python\n{record['learner_code']}\n```\n\n"
        "Tutor response:\n"
    )


@dataclass
class AssistantOnlyCollator:
    tokenizer: Any
    max_length: int = 4096

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        import torch

        batch_ids, batch_labels, batch_masks = [], [], []
        for feature in features:
            prompt = make_prompt(feature)
            answer = feature.get("assistant_response")
            if not answer:
                raise ValueError("assistant_response is required and must be audited before training")
            prompt_ids = self.tokenizer(prompt, add_special_tokens=True, truncation=False)["input_ids"]
            answer_ids = self.tokenizer(str(answer), add_special_tokens=False, truncation=False)["input_ids"]
            eos = [self.tokenizer.eos_token_id] if self.tokenizer.eos_token_id is not None else []
            input_ids = (prompt_ids + answer_ids + eos)[: self.max_length]
            prompt_len = min(len(prompt_ids), len(input_ids))
            labels = [-100] * prompt_len + input_ids[prompt_len:]
            attention = [1] * len(input_ids)
            batch_ids.append(input_ids)
            batch_labels.append(labels)
            batch_masks.append(attention)
        width = max(map(len, batch_ids))
        pad_id = self.tokenizer.pad_token_id or 0
        for ids, labels, mask in zip(batch_ids, batch_labels, batch_masks):
            padding = width - len(ids)
            ids.extend([pad_id] * padding)
            labels.extend([-100] * padding)
            mask.extend([0] * padding)
        return {"input_ids": torch.tensor(batch_ids), "labels": torch.tensor(batch_labels), "attention_mask": torch.tensor(batch_masks)}

