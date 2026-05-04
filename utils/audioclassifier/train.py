import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from preprocessor import (
    FREQ_SLICE,
    ENV_SAMPLES,
    N_FFT,
    HOP_LENGTH,
    SIGNAL_LEN,
    FS,
)
from model import AudioClassificationModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class AudioDataset(Dataset):

    def __init__(self, path: str, use_cache: bool = False):
        data = np.load(path, allow_pickle=True)

        X_raw: np.ndarray = data["X"] 
        raw_len = X_raw.shape[1]
        if raw_len >= SIGNAL_LEN:
            X_raw = X_raw[:, :SIGNAL_LEN]
        else:
            pad = SIGNAL_LEN - raw_len
            X_raw = np.pad(X_raw, ((0, 0), (0, pad)))

        self.X = torch.from_numpy(X_raw) 
        self.y_label = torch.from_numpy(data["y_label"].astype(np.int64))
        self.y_type = torch.from_numpy(data["y_type"].astype(np.int64))
        self.class_names = list(data["class_names"])

        self.use_cache = use_cache
        self._cache: dict[int, tuple] = {}

        self.window = torch.hann_window(N_FFT)

    def __len__(self) -> int:
        return len(self.X)


    def _compute_stft(self, waveform: torch.Tensor) -> torch.Tensor:
        spec = torch.stft(
            waveform,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            window=self.window,
            return_complex=True,
        )
        mag = spec.abs()
        mag = mag[FREQ_SLICE, :] 
        mag = mag.T 
        return mag.unsqueeze(0)

    def _compute_envelope(self, waveform: torch.Tensor) -> torch.Tensor:
        frames = waveform.unfold(0, SIGNAL_LEN // ENV_SAMPLES, SIGNAL_LEN // ENV_SAMPLES)
        rms = frames.pow(2).mean(dim=-1).sqrt()
        return rms

    def __getitem__(self, idx: int):
        if self.use_cache and idx in self._cache:
            return self._cache[idx]

        waveform = self.X[idx] 
        stft     = self._compute_stft(waveform) 
        envelope = self._compute_envelope(waveform) 

        sample = (stft, envelope, self.y_label[idx], self.y_type[idx])

        if self.use_cache:
            self._cache[idx] = sample

        return sample

class CombinedLoss(nn.Module):
    def __init__(self, type_weight: float = 0.0):
        super().__init__()
        self.type_weight = type_weight

    def forward(
        self,
        logits_label: torch.Tensor,
        y_label: torch.Tensor,
        logits_type: torch.Tensor | None = None,
        y_type: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, dict]:
        label_loss = F.cross_entropy(logits_label, y_label)
        loss = label_loss
        breakdown = {"label_loss": label_loss.item()}

        if self.type_weight > 0.0 and logits_type is not None:
            type_loss = F.binary_cross_entropy_with_logits(
                logits_type.squeeze(-1), y_type.float()
            )
            loss = loss + self.type_weight * type_loss
            breakdown["type_loss"] = type_loss.item()

        breakdown["total_loss"] = loss.item()
        return loss, breakdown

def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    preds = logits.argmax(dim=-1)
    return (preds == targets).float().mean().item()


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion: CombinedLoss) -> dict:
    model.eval()
    total_loss, total_acc, n_batches = 0.0, 0.0, 0

    for stft, envelope, y_label, y_type in loader:
        stft     = stft.to(DEVICE)
        envelope = envelope.to(DEVICE)
        y_label  = y_label.to(DEVICE)
        y_type   = y_type.to(DEVICE)

        logits = model(stft, envelope)
        loss, breakdown = criterion(logits, y_label)

        total_loss += breakdown["total_loss"]
        total_acc  += accuracy(logits, y_label)
        n_batches  += 1

    return {
        "val_loss": total_loss / n_batches,
        "val_acc":  total_acc  / n_batches,
    }


def save_checkpoint(state: dict, path: Path) -> None:
    torch.save(state, path)
    print(f"checkpoint saved -> {path}")


def train(args: argparse.Namespace) -> None:
    print(f"Device : {DEVICE}")

    train_ds = AudioDataset(args.train_data, use_cache=args.cache)
    val_ds   = AudioDataset(args.val_data,   use_cache=args.cache)

    n_classes = len(train_ds.class_names)
    print(f"Classes: {n_classes}  |  Train: {len(train_ds)}  |  Val: {len(val_ds)}")

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(DEVICE.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(DEVICE.type == "cuda"),
    )

    model = AudioClassificationModel(n_classes=n_classes).to(DEVICE)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parameters: {total_params:,}")

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=args.lr,
        steps_per_epoch=len(train_loader),
        epochs=args.epochs,
        pct_start=0.1,
        anneal_strategy="cos",
    )

    criterion = CombinedLoss(type_weight=args.type_weight)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt  = out_dir / "best.pt"
    last_ckpt  = out_dir / "last.pt"
    log_file   = out_dir / "train_log.csv"

    with open(log_file, "w") as f:
        f.write("epoch,train_loss,train_acc,val_loss,val_acc,lr,elapsed_s\n")

    best_val_loss = float("inf")
    t0 = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss, epoch_acc, n_batches = 0.0, 0.0, 0

        for stft, envelope, y_label, y_type in train_loader:
            stft     = stft.to(DEVICE)
            envelope = envelope.to(DEVICE)
            y_label  = y_label.to(DEVICE)
            y_type   = y_type.to(DEVICE)

            optimizer.zero_grad()
            logits = model(stft, envelope)
            loss, breakdown = criterion(logits, y_label)
            loss.backward()

            if args.grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)

            optimizer.step()
            scheduler.step()

            epoch_loss += breakdown["total_loss"]
            epoch_acc  += accuracy(logits, y_label)
            n_batches  += 1

        train_loss = epoch_loss / n_batches
        train_acc  = epoch_acc  / n_batches
        current_lr = scheduler.get_last_lr()[0]

        metrics   = evaluate(model, val_loader, criterion)
        val_loss  = metrics["val_loss"]
        val_acc   = metrics["val_acc"]
        elapsed   = time.time() - t0

        print(
            f"Epoch {epoch:03d}/{args.epochs}  "
            f"train_loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
            f"val_loss={val_loss:.4f}  val_acc={val_acc:.3f}  "
            f"lr={current_lr:.2e}  ({elapsed:.0f}s)"
        )

        with open(log_file, "a") as f:
            f.write(
                f"{epoch},{train_loss:.6f},{train_acc:.6f},"
                f"{val_loss:.6f},{val_acc:.6f},{current_lr:.6e},{elapsed:.1f}\n"
            )

        checkpoint = {
            "epoch":       epoch,
            "model_state": model.state_dict(),
            "optim_state": optimizer.state_dict(),
            "sched_state": scheduler.state_dict(),
            "val_loss":    val_loss,
            "val_acc":     val_acc,
            "class_names": train_ds.class_names,
            "args":        vars(args),
        }

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_checkpoint(checkpoint, best_ckpt)

        save_checkpoint(checkpoint, last_ckpt)

    print(f"\nTraining complete. Best val_loss={best_val_loss:.4f}")
    print(f"Checkpoints → {out_dir}")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train AudioClassificationModel")

    # data
    p.add_argument("--train-data",   default="trainingdata-small.npz")
    p.add_argument("--val-data",     default="validationdata-small.npz")
    p.add_argument("--cache",        action="store_true",
                   help="Cache preprocessed tensors in RAM after first epoch")

    # training
    p.add_argument("--epochs",       type=int,   default=40)
    p.add_argument("--batch-size",   type=int,   default=64)
    p.add_argument("--lr",           type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--grad-clip",    type=float, default=1.0,
                   help="Max gradient norm (0 = disabled)")
    p.add_argument("--type-weight",  type=float, default=0.0,
                   help="Weight for auxiliary synthetic-vs-midi loss (0 = off)")

    # misc
    p.add_argument("--num-workers",  type=int,   default=4)
    p.add_argument("--out-dir",      default="checkpoints/")

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)