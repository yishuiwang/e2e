import torch
import torch.nn as nn
from transformers import AutoModel


class CRFLayer(nn.Module):
    def __init__(self, num_tags: int):
        super().__init__()
        self.num_tags = num_tags
        self.start_transitions = nn.Parameter(torch.empty(num_tags))
        self.end_transitions = nn.Parameter(torch.empty(num_tags))
        self.transitions = nn.Parameter(torch.empty(num_tags, num_tags))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.uniform_(self.start_transitions, -0.1, 0.1)
        nn.init.uniform_(self.end_transitions, -0.1, 0.1)
        nn.init.uniform_(self.transitions, -0.1, 0.1)

    def forward(self, emissions, tags, mask):
        # emissions: [B, T, C]; tags: [B, T]; mask: [B, T]
        log_den = self._compute_log_partition_function(emissions, mask)
        log_num = self._compute_gold_score(emissions, tags, mask)
        return log_num - log_den

    def decode(self, emissions, mask):
        return self._viterbi_decode(emissions, mask)

    def _compute_gold_score(self, emissions, tags, mask):
        bsz, seq_len, num_tags = emissions.size()
        score = self.start_transitions[tags[:, 0]] + emissions[:, 0, :].gather(1, tags[:, 0].unsqueeze(1)).squeeze(1)
        for t in range(1, seq_len):
            mask_t = mask[:, t]
            emit_t = emissions[:, t, :].gather(1, tags[:, t].unsqueeze(1)).squeeze(1)
            trans_t = self.transitions[tags[:, t - 1], tags[:, t]]
            score += (emit_t + trans_t) * mask_t
        last_mask_index = mask.sum(1).long() - 1
        last_tags = tags.gather(1, last_mask_index.unsqueeze(1)).squeeze(1)
        score += self.end_transitions[last_tags]
        return score.sum()

    def _compute_log_partition_function(self, emissions, mask):
        bsz, seq_len, num_tags = emissions.size()
        log_alpha = self.start_transitions + emissions[:, 0]
        for t in range(1, seq_len):
            emit_t = emissions[:, t]  # [B, C]
            mask_t = mask[:, t].unsqueeze(1)  # [B,1]
            score_t = log_alpha.unsqueeze(2) + self.transitions.unsqueeze(0) + emit_t.unsqueeze(1)
            new_log_alpha = torch.logsumexp(score_t, dim=1)
            log_alpha = torch.where(mask_t.bool(), new_log_alpha, log_alpha)
        log_alpha = log_alpha + self.end_transitions
        return torch.logsumexp(log_alpha, dim=1).sum()

    def _viterbi_decode(self, emissions, mask):
        bsz, seq_len, num_tags = emissions.size()
        viterbi = self.start_transitions + emissions[:, 0]  # [B, C]
        backpointers = []
        for t in range(1, seq_len):
            broadcast_viterbi = viterbi.unsqueeze(2)
            broadcast_trans = self.transitions.unsqueeze(0)
            score_t = broadcast_viterbi + broadcast_trans
            best_score, best_path = score_t.max(1)
            viterbi = best_score + emissions[:, t]
            mask_t = mask[:, t].unsqueeze(1)
            backpointers.append(best_path)
            viterbi = torch.where(mask_t.bool(), viterbi, viterbi)
        viterbi += self.end_transitions
        best_last_score, best_last_tag = viterbi.max(1)
        # backtrack
        best_paths = []
        for i in range(bsz):
            seq_end = int(mask[i].sum().item())
            bp = backpointers[: seq_end - 1]
            last = best_last_tag[i].item()
            path = [last]
            for bptrs_t in reversed(bp):
                last = bptrs_t[i][last].item()
                path.append(last)
            best_paths.append(list(reversed(path)))
        return best_paths


class BERTBiLSTMCRF(nn.Module):
    def __init__(self, bert_model: str, num_tags: int, lstm_hidden: int = 256, dropout: float = 0.1):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model)
        self.lstm = nn.LSTM(self.bert.config.hidden_size, lstm_hidden // 2, num_layers=1, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(lstm_hidden, num_tags)
        self.crf = CRFLayer(num_tags)

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        lstm_out, _ = self.lstm(sequence_output)
        emissions = self.fc(self.dropout(lstm_out))
        mask = attention_mask.bool()
        if labels is not None:
            # labels shape [B, T]; mask [B, T]
            loss = -self.crf(emissions, labels, mask) / input_ids.size(0)
            return loss
        else:
            paths = self.crf.decode(emissions, mask)
            return paths
