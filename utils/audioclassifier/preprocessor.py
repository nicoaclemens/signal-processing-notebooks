import torch
import torch.nn as nn
import torch.nn.functional as f
import numpy as np
FS = 44_100
N_FFT = 4_096
HOP_LENGTH = N_FFT // 2
SIGNAL_LEN = 16_384
F_MIN_HZ = 20
F_MAX_HZ = 10_000

ENV_SAMPLES = 120
EMBED_DIM = 256

def stft_freq_slice(n_fft = N_FFT, fs = FS, f_lo = F_MIN_HZ, f_hi = F_MAX_HZ):
    k_lo = int(np.floor(f_lo * n_fft / fs))
    k_hi = int(np.floor(f_hi * n_fft / fs))
    return slice(k_lo, k_hi + 1)

FREQ_SLICE = stft_freq_slice()
N_FREQ_BINS = FREQ_SLICE.stop - FREQ_SLICE.start
N_TIME_FRAMES = (SIGNAL_LEN - N_FFT) // HOP_LENGTH + 1
# N_TIME_FRAMES = 1+ SIGNAL_LEN // HOP_LENGTH

print(f"stft grid: {N_TIME_FRAMES} frames x {N_FREQ_BINS} freq bins")

class STFTProjector(nn.Module):
    def __init__(self, stft_embed_dim = 256):
        super().__init__()
        self.instance_norm = nn.InstanceNorm2d(1, affine=True)
        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=(3, 3), padding=(1, 1)),
            nn.LeakyReLU(.01),
            nn.MaxPool2d(kernel_size=(2,2)),
            nn.Conv2d(16, 32, kernel_size=(3,3), padding=(1,1)),
            nn.LeakyReLU(.01),
            nn.MaxPool2d(kernel_size=(1,2)),
        )

        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        flat_size = 32 * 4 * 4
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat_size, stft_embed_dim),
            nn.LeakyReLU(.01),
        )

    def forward(self, x: torch.Tensor):
        x = torch.log1p(x)
        x = self.instance_norm(x)
        x = self.conv(x)
        x = self.pool(x)
        return self.head(x)
    
class EnvelopeProjector(nn.Module):
    def __init__(self, env_samples = ENV_SAMPLES, env_embed_dim = 128):
        super().__init__()
        self.norm = nn.LayerNorm(env_samples)
        self.mlp = nn.Sequential(
            nn.Linear(env_samples, 128),
            nn.LeakyReLU(.01),
            nn.Linear(128, env_embed_dim),
            nn.LeakyReLU(.01),
        )
    def forward(self, x: torch.Tensor):
        x = self.norm(x)
        return self.mlp(x)

class FusionHead(nn.Module):
    def __init__(self, stft_embed_dim = 256, env_embed_dim = 128, output_dim = EMBED_DIM, dropout = .3):
        super().__init__()
        fused = stft_embed_dim + env_embed_dim
        self.net = nn.Sequential(
            nn.LayerNorm(fused),
            nn.Linear(fused, output_dim),
            nn.LeakyReLU(0.01),
            nn.Dropout(dropout),
        )

    def forward(self, stft_emb : torch.Tensor, env_emb : torch.Tensor):
        x = torch.cat([stft_emb, env_emb], dim=1)
        return self.net(x)
    

class AudioPreprocessor(nn.Module):
    def __init__(self, stft_embed_dim = 256, env_embed_dim = 128, output_dim = EMBED_DIM, dropout = .3):
        super().__init__()
        self.stft_proj = STFTProjector(stft_embed_dim)
        self.env_proj = EnvelopeProjector(ENV_SAMPLES, env_embed_dim)
        self.fusion = FusionHead(stft_embed_dim, env_embed_dim, output_dim, dropout)

    def forward(self, stft : torch.Tensor, envelope : torch.Tensor):
        stft_emb = self.stft_proj(stft)
        env_emb = self.env_proj(envelope)
        return self.fusion(stft_emb, env_emb)
    
if __name__ == "__main__":
    B = 4

    dummy_stft = torch.rand(B, 1, N_TIME_FRAMES, N_FREQ_BINS).abs()
    dummy_env = torch.rand(B, ENV_SAMPLES)

    model = AudioPreprocessor()
    output = model(dummy_stft, dummy_env)
    print(f"STFT Input shape: {dummy_stft.shape}\nEnvelope Input shape: {dummy_env.shape}\nOutput vector shape: {output.shape}")
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"trainable params: {total_params}")