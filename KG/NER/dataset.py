from typing import List, Dict, Tuple
from pathlib import Path
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer


def read_bio(path: str) -> List[Tuple[List[str], List[str]]]:
    sentences = []
    chars = []
    tags = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if chars:
                    sentences.append((chars, tags))
                chars, tags = [], []
            else:
                parts = line.split()
                if len(parts) != 2:
                    continue
                c, t = parts
                chars.append(c)
                tags.append(t)
    if chars:
        sentences.append((chars, tags))
    return sentences


class NERDataset(Dataset):
    def __init__(self, file_path: str, label2id: Dict[str, int]):
        self.samples = read_bio(file_path)
        self.label2id = label2id

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        chars, tags = self.samples[idx]
        return chars, tags


class Collator:
    def __init__(self, tokenizer_name: str, label2id: Dict[str, int], max_length: int = 128):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
        self.label2id = label2id
        self.max_length = max_length

    def __call__(self, batch):
        texts = ["".join(chars) for chars, _ in batch]
        # Tokenize as characters joined; we assume one char per original token
        encoding = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        labels_batch = []
        for (chars, tags), input_ids in zip(batch, encoding["input_ids"]):
            # Map char-level tags to subword tokens: assign label to first subword of each char, others = O
            # For Chinese char-level tokenization with WWM, usually each char -> one token; fallback logic retained.
            word_ids = self.tokenizer.convert_ids_to_tokens(input_ids.tolist())
            # Build alignment naive: skip special tokens
            labels = []
            tag_idx = 0
            for tok in word_ids:
                if tok in (self.tokenizer.cls_token, self.tokenizer.sep_token) or tok.startswith("[PAD]"):
                    labels.append(-100)
                else:
                    if tag_idx < len(tags):
                        labels.append(self.label2id[tags[tag_idx]])
                        tag_idx += 1
                    else:
                        labels.append(-100)
            labels_batch.append(labels)
        max_len = encoding["input_ids"].size(1)
        labels_tensor = torch.tensor(labels_batch, dtype=torch.long)
        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": labels_tensor,
        }


def build_label_map(files: List[str]) -> Dict[str, int]:
    labels = set()
    for f in files:
        for chars, tags in read_bio(f):
            for t in tags:
                labels.add(t)
    sorted_labels = sorted(labels)
    return {l: i for i, l in enumerate(sorted_labels)}
