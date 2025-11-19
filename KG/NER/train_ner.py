import torch
from pathlib import Path
from typing import List, Dict
from datasets import load_dataset
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from seqeval.metrics import classification_report
from model import BERTBiLSTMCRF

MODEL_ID = "hfl/chinese-roberta-wwm-ext"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class HFNERDataset(Dataset):
    def __init__(self, records: List[Dict], label_list: List[str], tokenizer_name: str, max_length: int = 256):
        self.records = records
        self.label_list = label_list
        self.label2id = {l: i for i, l in enumerate(label_list)}
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
        self.max_length = max_length

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        return self.records[idx]

    def collate_fn(self, batch: List[Dict]):
        # Expect each record to have tokens list and tags list; attempt to auto-detect keys.
        sample = batch[0]
        tokens_key = None
        labels_key = None
        for k in sample.keys():
            if isinstance(sample[k], list):
                if all(isinstance(x, str) for x in sample[k]):
                    if tokens_key is None:
                        tokens_key = k
                if all(isinstance(x, str) for x in sample[k]):
                    # heuristic: if key name contains 'label' or 'tag'
                    if 'label' in k.lower() or 'tag' in k.lower():
                        labels_key = k
        # fallback common names
        if tokens_key is None:
            tokens_key = 'tokens'
        if labels_key is None:
            labels_key = 'ner_tags' if 'ner_tags' in sample else 'labels'

        texts = ["".join(item[tokens_key]) for item in batch]
        encodings = self.tokenizer(texts, return_tensors='pt', padding=True, truncation=True, max_length=self.max_length)
        labels_batch = []
        for item, input_ids, attention_mask in zip(batch, encodings['input_ids'], encodings['attention_mask']):
            word_tokens = item[tokens_key]
            word_labels = item[labels_key]
            # Align char-level labels with tokens produced.
            tokens = self.tokenizer.convert_ids_to_tokens(input_ids.tolist())
            labels = []
            idx_word = 0
            for tok in tokens:
                if tok in (self.tokenizer.cls_token, self.tokenizer.sep_token) or tok.startswith('[PAD]'):
                    labels.append(-100)
                else:
                    if idx_word < len(word_labels):
                        labels.append(self.label2id.get(word_labels[idx_word], -100))
                        idx_word += 1
                    else:
                        labels.append(-100)
            labels_batch.append(labels)
        labels_tensor = torch.tensor(labels_batch, dtype=torch.long)
        return {
            'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask'],
            'labels': labels_tensor
        }


def load_hf_dataset(name: str = "ttxy/cn_ner"):
    ds = load_dataset(name)
    # Determine splits
    train_split = ds['train']
    dev_split = ds['validation'] if 'validation' in ds else ds.get('dev', ds['train'])
    test_split = ds.get('test', None)
    # Infer label list from a feature (try typical keys)
    candidate_keys = ['ner_tags', 'labels', 'tags']
    label_list = None
    for key in candidate_keys:
        if key in train_split.features:
            feat = train_split.features[key]
            if hasattr(feat, 'names'):
                label_list = feat.names
                break
    if label_list is None:
        # Fallback: collect unique labels from a sample subset
        label_set = set()
        for ex in train_split.select(range(min(100, len(train_split)))):
            for k in candidate_keys:
                if k in ex:
                    label_set.update(ex[k])
        label_list = sorted(label_set)
    return train_split, dev_split, test_split, label_list


def evaluate(model, loader, id2label):
    model.eval()
    true_tags, pred_tags = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            labels = batch['labels'].to(DEVICE)
            paths = model(input_ids, attention_mask, labels=None)
            for path, gold, mask in zip(paths, labels, attention_mask):
                seq_len = int(mask.sum().item())
                gold_seq = [id2label[int(t.item())] for t in gold[:seq_len] if int(t.item()) != -100]
                pred_seq = [id2label[tag] for tag in path[:len(gold_seq)]]
                true_tags.append(gold_seq)
                pred_tags.append(pred_seq)
    print(classification_report(true_tags, pred_tags))
    model.train()


def train(epochs: int = 3, batch_size: int = 8, lr: float = 3e-5):
    print("加载数据集 ttxy/cn_ner ...")
    train_split, dev_split, test_split, label_list = load_hf_dataset("ttxy/cn_ner")
    print(f"标签集合: {label_list}")

    # Convert HF dataset to list-of-dict for our Dataset wrapper
    train_records = [train_split[i] for i in range(len(train_split))]
    dev_records = [dev_split[i] for i in range(len(dev_split))]

    train_ds = HFNERDataset(train_records, label_list, MODEL_ID)
    dev_ds = HFNERDataset(dev_records, label_list, MODEL_ID)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=train_ds.collate_fn)
    dev_loader = DataLoader(dev_ds, batch_size=batch_size, shuffle=False, collate_fn=dev_ds.collate_fn)

    model = BERTBiLSTMCRF(MODEL_ID, num_tags=len(label_list)).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    total_steps = epochs * len(train_loader)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * total_steps), total_steps)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(DEVICE)
            attention_mask = batch['attention_mask'].to(DEVICE)
            labels = batch['labels'].to(DEVICE)
            loss = model(input_ids, attention_mask, labels=labels)
            loss.backward()
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()
        avg_loss = total_loss / max(1, len(train_loader))
        print(f"Epoch {epoch} loss={avg_loss:.4f}")
        evaluate(model, dev_loader, {i: l for i, l in enumerate(label_list)})

    save_dir = Path(__file__).parent / 'ner_model'
    save_dir.mkdir(exist_ok=True)
    torch.save({'state_dict': model.state_dict(), 'label2id': {l: i for i, l in enumerate(label_list)}}, save_dir / 'model.pt')
    print(f"模型已保存到 {save_dir}")


if __name__ == '__main__':
    train()
