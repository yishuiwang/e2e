"""
配置文件
"""
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

# 数据文件
TRAIN_FILE = DATA_DIR / "EduNER/train.csv"
DEV_FILE = DATA_DIR / "EduNER/dev.csv"
TEST_FILE = DATA_DIR / "EduNER/test.csv"

# 预训练模型
PRETRAINED_MODEL = str(MODEL_DIR / "hfl-chinese-roberta-wwm-ext")

# 标签定义
TAG2ID = {
    'O': 0,
    'B-ALG': 1, 'I-ALG': 2,
    'B-BOO': 3, 'I-BOO': 4,
    'B-COF': 5, 'I-COF': 6,
    'B-CON': 7, 'I-CON': 8,
    'B-COU': 9, 'I-COU': 10,
    'B-CRN': 11, 'I-CRN': 12,
    'B-DAT': 13, 'I-DAT': 14,
    'B-FRM': 15, 'I-FRM': 16,
    'B-JOU': 17, 'I-JOU': 18,
    'B-LOC': 19, 'I-LOC': 20,
    'B-ORG': 21, 'I-ORG': 22,
    'B-PER': 23, 'I-PER': 24,
    'B-POL': 25, 'I-POL': 26,
    'B-TER': 27, 'I-TER': 28,
    'B-THE': 29, 'I-THE': 30,
    'B-TOO': 31, 'I-TOO': 32,
    'PAD': 33
}
ID2TAG = {v: k for k, v in TAG2ID.items()}

# 模型超参数
class Config:
    # 模型参数
    pretrained_model = PRETRAINED_MODEL
    hidden_dim = 256  # BiLSTM隐藏层维度
    num_layers = 2    # BiLSTM层数
    dropout = 0.3
    
    # 训练参数
    batch_size = 16
    learning_rate = 2e-5
    num_epochs = 20
    warmup_steps = 100
    max_grad_norm = 1.0
    
    # 数据参数
    max_seq_length = 128
    
    # 标签
    tag2id = TAG2ID
    id2tag = ID2TAG
    num_tags = len(TAG2ID)
    
    # 路径
    train_file = str(TRAIN_FILE)
    dev_file = str(DEV_FILE)
    test_file = str(TEST_FILE)
    output_dir = str(OUTPUT_DIR)
    
    # 设备
    device = 'cpu'  # 如果没有GPU，改为 'cpu'
    
    # 其他
    seed = 42
    save_steps = 100  # 每多少步保存一次模型
    logging_steps = 20  # 每多少步打印一次日志
