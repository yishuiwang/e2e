"""
BERT + BiLSTM + CRF 模型定义
"""
import torch
import torch.nn as nn
from transformers import BertModel, BertPreTrainedModel
from torchcrf import CRF


class BertBiLSTMCRF(BertPreTrainedModel):
    """
    BERT + BiLSTM + CRF 模型用于NER任务
    
    架构:
    1. BERT: 提取字符级别的contextualized embeddings
    2. BiLSTM: 进一步建模序列依赖关系
    3. CRF: 解码最优标签序列，确保标签转移的合法性
    """
    
    def __init__(self, config, num_tags, hidden_dim=256, num_layers=2, dropout=0.3):
        """
        Args:
            config: BERT配置
            num_tags: 标签数量
            hidden_dim: BiLSTM隐藏层维度
            num_layers: BiLSTM层数
            dropout: dropout比例
        """
        super(BertBiLSTMCRF, self).__init__(config)
        
        self.num_tags = num_tags
        self.hidden_dim = hidden_dim
        
        # BERT层
        self.bert = BertModel(config)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # BiLSTM层
        self.bilstm = nn.LSTM(
            input_size=config.hidden_size,  # BERT输出维度 (通常是768)
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # 全连接层：将BiLSTM输出映射到标签空间
        self.classifier = nn.Linear(hidden_dim * 2, num_tags)  # *2因为是双向
        
        # CRF层
        self.crf = CRF(num_tags, batch_first=True)
        
        # 初始化权重
        self.init_weights()
    
    def forward(self, input_ids, attention_mask=None, token_type_ids=None, 
                labels=None, seq_len=None):
        """
        前向传播
        
        Args:
            input_ids: [batch_size, seq_len]
            attention_mask: [batch_size, seq_len]
            token_type_ids: [batch_size, seq_len]
            labels: [batch_size, seq_len] (可选，训练时需要)
            seq_len: [batch_size] 实际序列长度 (可选)
        
        Returns:
            如果labels不为None，返回loss
            否则返回预测的标签序列
        """
        # 1. BERT编码
        bert_outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        
        # 获取sequence output: [batch_size, seq_len, hidden_size]
        sequence_output = bert_outputs.last_hidden_state
        
        # 2. Dropout
        sequence_output = self.dropout(sequence_output)
        
        # 3. BiLSTM编码
        # LSTM需要先pack，以忽略padding部分（可选，这里简化处理）
        lstm_output, _ = self.bilstm(sequence_output)
        # lstm_output: [batch_size, seq_len, hidden_dim * 2]
        
        # 4. 应用dropout
        lstm_output = self.dropout(lstm_output)
        
        # 5. 映射到标签空间
        emissions = self.classifier(lstm_output)
        # emissions: [batch_size, seq_len, num_tags]
        
        # 6. CRF处理
        if labels is not None:
            # 训练模式：计算负对数似然损失
            # CRF的mask：1表示真实token，0表示padding
            mask = attention_mask.bool()
            
            # CRF loss (negative log likelihood)
            loss = -self.crf(emissions, labels, mask=mask, reduction='mean')
            return loss
        else:
            # 预测模式：使用viterbi算法解码最优路径
            mask = attention_mask.bool()
            predictions = self.crf.decode(emissions, mask=mask)
            return predictions
    
    def get_bert_embedding(self, input_ids, attention_mask=None, token_type_ids=None):
        """
        获取BERT的embedding（用于分析或可视化）
        """
        with torch.no_grad():
            bert_outputs = self.bert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids
            )
            return bert_outputs.last_hidden_state
