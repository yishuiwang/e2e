"""
预测脚本 - 使用训练好的模型进行课程名称抽取
"""
import torch
from transformers import BertTokenizer, BertConfig as BertModelConfig
from typing import List, Tuple
from pathlib import Path

from config import Config
from model import BertBiLSTMCRF


class CourseNER:
    """课程名称实体识别器"""
    
    def __init__(self, model_path: str, config: Config = None):
        """
        Args:
            model_path: 训练好的模型路径
            config: 配置对象
        """
        self.config = config if config else Config()
        self.device = torch.device(self.config.device if torch.cuda.is_available() else 'cpu')
        
        # 加载tokenizer
        print(f"Loading tokenizer from {self.config.pretrained_model}...")
        self.tokenizer = BertTokenizer.from_pretrained(self.config.pretrained_model)
        
        # 加载模型
        print(f"Loading model from {model_path}...")
        bert_config = BertModelConfig.from_pretrained(self.config.pretrained_model)
        
        self.model = BertBiLSTMCRF(
            config=bert_config,
            num_tags=self.config.num_tags,
            hidden_dim=self.config.hidden_dim,
            num_layers=self.config.num_layers,
            dropout=self.config.dropout
        )
        
        # 加载权重
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded successfully! Best F1: {checkpoint.get('best_f1', 'N/A')}")
    
    def predict(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        预测文本中的课程名称
        
        Args:
            text: 输入文本
        
        Returns:
            List of (entity_text, entity_type, start_pos, end_pos)
            例如: [("计算机网络", "COURSE", 10, 15)]
        """
        # 将文本转为字符列表
        chars = list(text)
        
        # 准备输入
        tokens = ['[CLS]'] + chars[:self.config.max_seq_length-2] + ['[SEP]']
        
        # 填充
        while len(tokens) < self.config.max_seq_length:
            tokens.append('[PAD]')
        
        # 转换为ID
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        attention_mask = [1 if token != '[PAD]' else 0 for token in tokens]
        token_type_ids = [0] * self.config.max_seq_length
        
        # 转为tensor
        input_ids = torch.tensor([input_ids], dtype=torch.long).to(self.device)
        attention_mask = torch.tensor([attention_mask], dtype=torch.long).to(self.device)
        token_type_ids = torch.tensor([token_type_ids], dtype=torch.long).to(self.device)
        
        # 预测
        with torch.no_grad():
            predictions = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids
            )
        
        # 解析预测结果
        pred_tags = predictions[0]  # 第一个样本
        
        # 提取实体
        entities = []
        current_entity = []
        current_type = None
        start_pos = -1
        
        for i, (char, tag_id) in enumerate(zip(chars, pred_tags[1:])):  # 跳过[CLS]
            tag = self.config.id2tag.get(tag_id, 'O')
            
            if tag.startswith('B-'):
                # 开始一个新实体
                if current_entity:
                    # 保存之前的实体
                    entity_text = "".join(current_entity)
                    entities.append((entity_text, current_type, start_pos, start_pos + len(current_entity)))
                
                current_entity = [char]
                current_type = tag[2:]  # 去掉 'B-' 前缀
                start_pos = i
                
            elif tag.startswith('I-') and current_type == tag[2:]:
                # 继续当前实体
                current_entity.append(char)
                
            else:
                # 结束当前实体
                if current_entity:
                    entity_text = "".join(current_entity)
                    entities.append((entity_text, current_type, start_pos, start_pos + len(current_entity)))
                    current_entity = []
                    current_type = None
                    start_pos = -1
        
        # 处理最后一个实体
        if current_entity:
            entity_text = "".join(current_entity)
            entities.append((entity_text, current_type, start_pos, start_pos + len(current_entity)))
        
        return entities
    
    def extract_courses(self, text: str) -> List[str]:
        """
        提取文本中的所有课程名称
        
        Args:
            text: 输入文本
        
        Returns:
            课程名称列表
        """
        entities = self.predict(text)
        courses = [entity[0] for entity in entities if entity[1] == 'COURSE']
        return courses


def demo():
    """演示预测功能"""
    
    config = Config()
    
    # 模型路径
    model_path = Path(config.output_dir) / "best_model.pth"
    
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print("Please train the model first using: python train_ner.py")
        return
    
    # 初始化预测器
    ner = CourseNER(str(model_path), config)
    
    # 测试样例
    test_texts = [
        "本学期我修读了计算机网络和数据结构两门课程",
        "我对人工智能很感兴趣",
        "专业核心课包括操作系统、编译原理和软件工程",
        "今年新开设了深度学习和机器学习课程",
        "中国近现代史纲要是必修课程之一"
    ]
    
    print("\n" + "=" * 60)
    print("课程名称抽取演示")
    print("=" * 60)
    
    for text in test_texts:
        print(f"\n原文: {text}")
        
        # 预测
        entities = ner.predict(text)
        courses = ner.extract_courses(text)
        
        if entities:
            print(f"识别的实体:")
            for entity_text, entity_type, start, end in entities:
                print(f"  - [{entity_type}] {entity_text} (位置: {start}-{end})")
        else:
            print("  未识别到课程名称")
        
        if courses:
            print(f"课程列表: {', '.join(courses)}")
    
    # 交互式预测
    print("\n" + "=" * 60)
    print("交互式预测模式 (输入 'q' 退出)")
    print("=" * 60)
    
    while True:
        text = input("\n请输入文本: ").strip()
        
        if text.lower() == 'q':
            break
        
        if not text:
            continue
        
        courses = ner.extract_courses(text)
        
        if courses:
            print(f"识别的课程: {', '.join(courses)}")
        else:
            print("未识别到课程名称")
    
    print("\n感谢使用!")


if __name__ == "__main__":
    demo()
