import torch
import torch.nn as nn
import torch.nn.functional as f
import numpy as np
from preprocessor import AudioPreprocessor

class ResidualBlock(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim, dropout = 0.0):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, out_dim),
            nn.BatchNorm1d(out_dim),
        )
        self.skip = (
            nn.Identity() if in_dim == out_dim else nn.Linear(in_dim, out_dim, bias = False)
        )
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.act = nn.GELU()
    def forward(self, x: torch.Tensor):
        return self.dropout(self.act(self.skip(x)+self.block(x)))
    
class AudioClassifier(nn.Module):

    def __init__(self, input_dim = 256, n_classes = 10):
        super().__init__()
        self.input_norm = nn.BatchNorm1d(input_dim)
        self.block1 = ResidualBlock(in_dim = 256, hidden_dim=512, out_dim=256, dropout=0.3)
        self.block2 = ResidualBlock(in_dim = 256, hidden_dim=256, out_dim=128, dropout=0.2)
        self.head = nn.Linear(128, n_classes)
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    def forward(self, x: torch.Tensor):
        x = self.input_norm(x)
        x = self.block1(x)
        x = self.block2(x)
        return self.head(x)
    
class AudioClassificationModel(nn.Module):
    def __init__(self, n_classes = 10):
        super().__init__()
        self.preprocessor = AudioPreprocessor()
        self.classifier = AudioClassifier(input_dim=256, n_classes=n_classes)

    def forward(self, stft: torch.Tensor, envelope: torch.Tensor):
        features = self.preprocessor(stft, envelope)
        return self.classifier(features)