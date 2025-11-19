import torch
from pathlib import Path
from transformers import AutoTokenizer
from model import BERTBiLSTMCRF

MODEL_ID = "hfl/chinese-roberta-wwm-ext"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model(model_dir: str):
    ckpt = torch.load(Path(model_dir) / "model.pt", map_location="cpu")
    label2id = ckpt["label2id"]
    id2label = {v: k for k, v in label2id.items()}
    model = BERTBiLSTMCRF(MODEL_ID, num_tags=len(label2id))
    model.load_state_dict(ckpt["state_dict"], strict=False)
    model.to(DEVICE)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    return model, tokenizer, id2label


def predict(sentence: str, model, tokenizer, id2label):
    encoding = tokenizer(sentence, return_tensors="pt")
    input_ids = encoding["input_ids"].to(DEVICE)
    attention_mask = encoding["attention_mask"].to(DEVICE)
    with torch.no_grad():
        paths = model(input_ids, attention_mask, labels=None)
    path = paths[0]
    seq_len = int(attention_mask[0].sum().item())
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])[:seq_len]
    results = []
    tag_idx = 0
    for tok in tokens:
        if tok in (tokenizer.cls_token, tokenizer.sep_token):
            continue
        if tag_idx >= len(path):
            break
        label = id2label[path[tag_idx]]
        results.append((tok, label))
        tag_idx += 1
    return results


if __name__ == "__main__":
    model_dir = Path(__file__).parent / "ner_model"
    model, tokenizer, id2label = load_model(model_dir)
    sent = "北京位于中国东部"
    res = predict(sent, model, tokenizer, id2label)
    for tok, label in res:
        print(f"{tok}\t{label}")
