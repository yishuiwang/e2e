from pathlib import Path
from typing import List, Tuple
from infer_ner import load_model, predict
from transformers import pipeline


def bio_to_entities(tokens_with_labels: List[Tuple[str, str]]):
	entities = []
	cur_type, cur_tokens = None, []
	for tok, tag in tokens_with_labels:
		if tag.startswith("B-"):
			if cur_tokens:
				entities.append((cur_type, "".join(cur_tokens)))
			cur_type = tag[2:]
			cur_tokens = [tok]
		elif tag.startswith("I-") and cur_type == tag[2:]:
			cur_tokens.append(tok)
		else:
			if cur_tokens:
				entities.append((cur_type, "".join(cur_tokens)))
			cur_type, cur_tokens = None, []
	if cur_tokens:
		entities.append((cur_type, "".join(cur_tokens)))
	return entities


if __name__ == "__main__":
	model_dir = Path(__file__).parent / "ner_model"

	samples = [
		"北京是中国的首都",
		"上海在中国东部",
		"中南大学位于湖南长沙",
	]

	if (model_dir / "model.pt").exists():
		model, tokenizer, id2label = load_model(model_dir)
		for s in samples:
			pairs = predict(s, model, tokenizer, id2label)
			ents = bio_to_entities(pairs)
			print("句子:", s)
			print("标注:", " ".join([f"{t}/{y}" for t, y in pairs]))
			print("实体:", ", ".join([f"{typ}:{text}" for typ, text in ents]) or "(无)")
			print("-" * 40)
	else:
		# Fallback: use a pretrained Chinese NER model via Hugging Face pipeline
		fallback_model = "uer/roberta-base-finetuned-cluener2020-chinese"
		ner = pipeline("token-classification", model=fallback_model, tokenizer=fallback_model, aggregation_strategy="simple")
		for s in samples:
			preds = ner(s)
			ents = [f"{p['entity_group']}:{p['word']}" for p in preds]
			print("句子:", s)
			print("实体:", ", ".join(ents) or "(无)")
			print("-" * 40)