"""
数据集加载器
"""
import torch
from torch.utils.data import Dataset
from transformers import BertTokenizer
from typing import List, Tuple
from config import Config


class NERDataset(Dataset):
    """NER数据集类"""
    
    def __init__(self, file_path: str, tokenizer: BertTokenizer, config: Config):
        """
        Args:
            file_path: 数据文件路径
            tokenizer: BERT tokenizer
            config: 配置对象
        """
        self.tokenizer = tokenizer
        self.config = config
        self.max_seq_length = config.max_seq_length
        self.tag2id = config.tag2id
        
        # 加载数据
        self.sentences, self.tags = self._load_data(file_path)
        
    def _load_data(self, file_path: str) -> Tuple[List[List[str]], List[List[str]]]:
        """
        从BIO格式文件加载数据
        
        Returns:
            sentences: 字符列表的列表
            tags: 标签列表的列表
        """
        sentences = []
        tags = []
        
        current_chars = []
        current_tags = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line:  # 空行表示句子结束
                    if current_chars:
                        sentences.append(current_chars)
                        tags.append(current_tags)
                        current_chars = []
                        current_tags = []
                else:
                    # EduNER format: char tag (space separated)
                    parts = line.split()
                    if len(parts) >= 2:
                        char = parts[0]
                        tag = parts[-1] # Take the last part as tag to be safe
                        current_chars.append(char)
                        current_tags.append(tag)
        
        # 处理最后一个句子
        if current_chars:
            sentences.append(current_chars)
            tags.append(current_tags)
        
        print(f"Loaded {len(sentences)} sentences from {file_path}")
        return sentences, tags
    
    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, idx):
        """
        获取单个样本
        
        Returns:
            input_ids: token的ID序列
            attention_mask: attention mask
            token_type_ids: token type ids (segment ids)
            labels: 标签序列
            seq_len: 实际序列长度（不包括[CLS]和[SEP]）
        """
        chars = self.sentences[idx]
        tags = self.tags[idx]
        
        # 将字符转为token（BERT会进行wordpiece分词）
        # 使用is_split_into_words=True表示输入已经是分好的词
        text = " ".join(chars)  # 用空格连接，便于tokenizer处理
        
        # 简单处理：直接把字符序列转为字符串
        text = "".join(chars)
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_seq_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
            is_split_into_words=False
        )
        
        # 注意：BERT tokenizer可能会对字符进行进一步分词
        # 我们需要处理标签对齐问题
        # 为了简化，我们使用字符级别的tokenization
        
        # 重新实现：使用字符级别的方法
        tokens = ['[CLS]']
        label_ids = [self.tag2id['O']]  # [CLS] 标记为 O
        
        # 添加字符和标签
        for char, tag in zip(chars[:self.max_seq_length-2], tags[:self.max_seq_length-2]):
            tokens.append(char)
            label_ids.append(self.tag2id.get(tag, self.tag2id['O']))
        
        tokens.append('[SEP]')
        label_ids.append(self.tag2id['O'])  # [SEP] 标记为 O
        
        # 记录实际长度
        seq_len = len(tokens)
        
        # 填充到max_seq_length
        while len(tokens) < self.max_seq_length:
            tokens.append('[PAD]')
            label_ids.append(self.tag2id['PAD'])
        
        # 转换为ID
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        
        # 创建attention mask (1表示真实token，0表示padding)
        attention_mask = [1 if token != '[PAD]' else 0 for token in tokens]
        
        # token_type_ids全为0（单句子任务）
        token_type_ids = [0] * self.max_seq_length
        
        return {
            'input_ids': torch.tensor(input_ids, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'labels': torch.tensor(label_ids, dtype=torch.long),
            'seq_len': torch.tensor(seq_len, dtype=torch.long)
        }


def collate_fn(batch):
    """
    自定义collate函数，用于DataLoader
    """
    input_ids = torch.stack([item['input_ids'] for item in batch])
    attention_mask = torch.stack([item['attention_mask'] for item in batch])
    token_type_ids = torch.stack([item['token_type_ids'] for item in batch])
    labels = torch.stack([item['labels'] for item in batch])
    seq_len = torch.stack([item['seq_len'] for item in batch])
    
    return {
        'input_ids': input_ids,
        'attention_mask': attention_mask,
        'token_type_ids': token_type_ids,
        'labels': labels,
        'seq_len': seq_len
    }
