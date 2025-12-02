"""
训练脚本
"""
import os
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import BertTokenizer, get_linear_schedule_with_warmup
from tqdm import tqdm
from pathlib import Path

from config import Config
from dataset import NERDataset, collate_fn
from model import BertBiLSTMCRF
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report


def set_seed(seed):
    """设置随机种子"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, dataloader, device, id2tag):
    """
    评估模型
    
    Returns:
        metrics: 包含precision, recall, f1的字典
    """
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            token_type_ids = batch['token_type_ids'].to(device)
            labels = batch['labels'].to(device)
            
            # 预测
            predictions = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids
            )
            
            # 处理预测结果和标签
            for pred, label, mask in zip(predictions, labels, attention_mask):
                # pred是list，label是tensor
                pred_tags = []
                true_tags = []
                
                for p, l, m in zip(pred, label.cpu().numpy(), mask.cpu().numpy()):
                    if m == 1:  # 只考虑非padding的部分
                        pred_tag = id2tag.get(p, 'O')
                        true_tag = id2tag.get(l, 'O')
                        
                        # 忽略PAD标签
                        if true_tag != 'PAD':
                            pred_tags.append(pred_tag)
                            true_tags.append(true_tag)
                
                if pred_tags and true_tags:
                    all_preds.append(pred_tags)
                    all_labels.append(true_tags)
    
    # 计算metrics (使用seqeval)
    precision = precision_score(all_labels, all_preds)
    recall = recall_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds)
    
    # 打印详细报告
    print("\n" + classification_report(all_labels, all_preds, digits=4))
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def train():
    """训练主函数"""
    
    # 配置
    config = Config()
    
    # 设置随机种子
    set_seed(config.seed)
    
    # 创建输出目录
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 设置设备
    device = torch.device(config.device if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # 加载tokenizer
    print(f"\nLoading tokenizer from {config.pretrained_model}...")
    tokenizer = BertTokenizer.from_pretrained(config.pretrained_model)
    
    # 加载数据集
    print("\nLoading datasets...")
    train_dataset = NERDataset(config.train_file, tokenizer, config)
    dev_dataset = NERDataset(config.dev_file, tokenizer, config)
    
    # 创建DataLoader
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        collate_fn=collate_fn
    )
    
    dev_dataloader = DataLoader(
        dev_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        collate_fn=collate_fn
    )
    
    # 初始化模型
    print("\nInitializing model...")
    from transformers import BertConfig as BertModelConfig
    bert_config = BertModelConfig.from_pretrained(config.pretrained_model)
    
    model = BertBiLSTMCRF(
        config=bert_config,
        num_tags=config.num_tags,
        hidden_dim=config.hidden_dim,
        num_layers=config.num_layers,
        dropout=config.dropout
    )
    
    model.to(device)
    
    # 优化器
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {
            'params': [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
            'weight_decay': 0.01
        },
        {
            'params': [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
            'weight_decay': 0.0
        }
    ]
    
    optimizer = AdamW(optimizer_grouped_parameters, lr=config.learning_rate)
    
    # 学习率调度器
    total_steps = len(train_dataloader) * config.num_epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config.warmup_steps,
        num_training_steps=total_steps
    )
    
    # 训练循环
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60)
    
    best_f1 = 0.0
    global_step = 0
    
    for epoch in range(config.num_epochs):
        print(f"\nEpoch {epoch + 1}/{config.num_epochs}")
        
        # 训练
        model.train()
        train_loss = 0.0
        train_steps = 0
        
        progress_bar = tqdm(train_dataloader, desc="Training")
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            token_type_ids = batch['token_type_ids'].to(device)
            labels = batch['labels'].to(device)
            
            # 前向传播
            loss = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                labels=labels
            )
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            
            # 更新参数
            optimizer.step()
            scheduler.step()
            
            # 统计
            train_loss += loss.item()
            train_steps += 1
            global_step += 1
            
            # 更新进度条
            progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            # 定期打印日志
            if global_step % config.logging_steps == 0:
                avg_loss = train_loss / train_steps
                print(f"\nStep {global_step}, Avg Loss: {avg_loss:.4f}")
        
        # 计算平均训练损失
        avg_train_loss = train_loss / train_steps
        print(f"\nAverage training loss: {avg_train_loss:.4f}")
        
        # 在验证集上评估
        print("\nEvaluating on dev set...")
        metrics = evaluate(model, dev_dataloader, device, config.id2tag)
        
        print(f"\nDev Metrics:")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")
        print(f"  F1: {metrics['f1']:.4f}")
        
        # 保存最佳模型
        if metrics['f1'] > best_f1:
            best_f1 = metrics['f1']
            print(f"\n✓ New best F1: {best_f1:.4f}, saving model...")
            
            # 保存模型
            model_save_path = output_dir / "best_model.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_f1': best_f1,
                'config': config
            }, model_save_path)
            
            print(f"  Model saved to {model_save_path}")
    
    print("\n" + "=" * 60)
    print("Training completed!")
    print(f"Best F1 score: {best_f1:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    train()
