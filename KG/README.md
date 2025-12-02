1. 绝对统治地位：BERT (RoBERTa/MacBERT) + 下游层
这是目前的工业界“黄金标准”。
预训练模型底座：通常使用 RoBERTa-wwm-ext 或 MacBERT（哈工大讯飞联合实验室出品）。这些模型在中文任务上比原始 Google BERT 强很多。
解码层变化：
BERT + CRF：最经典的组合。虽然 CRF（条件随机场）解码速度稍慢，但能保证标签的合法性（不会出现 O 后面接 I 的情况）。
BERT + Softmax/Span：为了追求极致速度，很多场景直接去掉 CRF，改用简单的分类或 Span 指针网络。



Schema

定义schema
专业、课程、知识点；
岗位、技能、行业、职责。


EduNER: a Chinese named entity recognition dataset for education research
https://link.springer.com/article/10.1007/s00521-023-08635-5
### **✔ 提取教育领域文本中的实体**
中文

* **PER**：作者、教育人物
* **DAT**：日期
* **TER**：教育术语、概念
* **ORG**：学校、机构
* **LOC**：地点
* …以及共 **16 种实体类型**


https://huggingface.co/datasets/Mehyaar/Annotated_NER_PDF_Resumes/tree/main
包含5,029个CV样本的NER数据集，手动标注IT技能，从PDF简历中提取。IT技能（skills，如Python、Machine Learning）、职位（role）等。
英文