# 课程名称NER - BERT + BiLSTM + CRF

基于 BERT + BiLSTM + CRF 的命名实体识别（NER）系统，用于从培养方案中提取课程名称。

## 模型架构

```
输入文本
    ↓
[BERT] - 提取contextualized embeddings (768维)
    ↓
[BiLSTM] - 建模序列依赖关系 (256维 × 2层)
    ↓
[全连接层] - 映射到标签空间
    ↓
[CRF] - 解码最优标签序列
    ↓
输出标签 (B-COURSE, I-COURSE, O)
```

### 关键特性

1. **BERT**: 使用 `hfl/chinese-roberta-wwm-ext` 预训练模型，专门针对中文优化
2. **BiLSTM**: 双向LSTM进一步捕获序列的上下文信息
3. **CRF**: 条件随机场确保标签转移的合法性（如B后面不能直接接B）

## 项目结构

```
KG/NER/
├── config.py              # 配置文件
├── model.py               # BERT+BiLSTM+CRF模型定义
├── dataset.py             # 数据加载器
├── train_ner.py           # 训练脚本
├── predict.py             # 预测脚本
├── prepare_training_data.py  # 数据准备脚本
├── download_model.py      # 下载预训练模型
├── requirements.txt       # 依赖包
├── data/                  # 数据目录
│   ├── train.txt         # 训练集 (BIO格式)
│   ├── dev.txt           # 验证集
│   ├── test.txt          # 测试集
│   └── courses.json      # 课程列表
├── models/               # 预训练模型目录
│   └── hfl-chinese-roberta-wwm-ext/
└── outputs/              # 输出目录
    └── best_model.pth    # 最佳模型
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载预训练模型（如果还没有）

```bash
python download_model.py
```

### 3. 准备训练数据（如果还没有）

```bash
python prepare_training_data.py
```

这将从中南大学的培养方案中提取课程名称，并生成BIO格式的训练数据。

### 4. 训练模型

```bash
python train_ner.py
```

训练过程会：
- 在训练集上训练模型
- 在验证集上评估性能
- 自动保存最佳模型（基于F1分数）
- 显示详细的评估指标（Precision, Recall, F1）

### 5. 使用模型进行预测

```bash
python predict.py
```

这将启动交互式预测模式，你可以输入文本来测试模型。

## 使用示例

### 在代码中使用

```python
from predict import CourseNER
from config import Config

# 初始化预测器
config = Config()
ner = CourseNER("outputs/best_model.pth", config)

# 预测文本
text = "本学期我修读了计算机网络和数据结构两门课程"
courses = ner.extract_courses(text)
print(courses)  # ['计算机网络', '数据结构']

# 获取详细信息
entities = ner.predict(text)
for entity_text, entity_type, start, end in entities:
    print(f"{entity_text} ({entity_type}): 位置 {start}-{end}")
```

### 命令行交互

```bash
$ python predict.py

课程名称抽取演示
============================================================

原文: 本学期我修读了计算机网络和数据结构两门课程
识别的实体:
  - [COURSE] 计算机网络 (位置: 7-12)
  - [COURSE] 数据结构 (位置: 13-17)
课程列表: 计算机网络, 数据结构

============================================================
交互式预测模式 (输入 'q' 退出)
============================================================

请输入文本: 专业核心课包括操作系统、编译原理和软件工程
识别的课程: 操作系统, 编译原理, 软件工程
```

## 数据格式

### BIO标注格式

训练数据使用BIO格式：
- `B-COURSE`: 课程名称的开始
- `I-COURSE`: 课程名称的内部
- `O`: 非实体

示例：
```
本 O
学 O
期 O
我 O
修 O
读 O
了 O
计 B-COURSE
算 I-COURSE
机 I-COURSE
网 I-COURSE
络 I-COURSE
课 O
程 O
```

## 模型配置

主要超参数（在 `config.py` 中）：

```python
# 模型参数
hidden_dim = 256      # BiLSTM隐藏层维度
num_layers = 2        # BiLSTM层数
dropout = 0.3         # Dropout比例

# 训练参数
batch_size = 16       # 批次大小
learning_rate = 2e-5  # 学习率
num_epochs = 20       # 训练轮数
max_seq_length = 128  # 最大序列长度
```

## 评估指标

模型使用 `seqeval` 库计算以下指标：
- **Precision**: 精确率
- **Recall**: 召回率
- **F1 Score**: F1分数（主要评估指标）

这些指标是实体级别的，而不是token级别的，更符合NER任务的评估标准。

## 性能优化建议

1. **增加训练数据**：当前数据是基于模板生成的，可以添加更多真实的培养方案文本
2. **调整超参数**：尝试不同的学习率、隐藏层维度等
3. **数据增强**：使用同义词替换、回译等技术增强数据
4. **fine-tune BERT**：当前会fine-tune BERT，但可以尝试冻结部分层
5. **使用更大的模型**：如 `hfl/chinese-roberta-wwm-ext-large`

## 常见问题

### Q: 训练时显示 CUDA out of memory

A: 减小 `batch_size` 或 `max_seq_length`

### Q: 模型预测效果不好

A: 
- 检查训练数据质量
- 增加训练epoch数
- 调整学习率
- 增加训练数据量

### Q: 如何在CPU上训练

A: 在 `config.py` 中修改 `device = 'cpu'`

## 技术栈

- **PyTorch**: 深度学习框架
- **Transformers**: Hugging Face的预训练模型库
- **torchcrf**: CRF层实现
- **seqeval**: NER评估指标

## License

MIT License

## 参考文献

1. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
2. Conditional Random Fields: Probabilistic Models for Segmenting and Labeling Sequence Data
3. Chinese BERT with Whole Word Masking (hfl/chinese-roberta-wwm-ext)
