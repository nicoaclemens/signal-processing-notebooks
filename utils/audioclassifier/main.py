# used by:
import argparse
from utils.audioclassifier.train import train


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train AudioClassificationModel")

    # data
    p.add_argument("--train-data", default="trainingdata-small.npz")
    p.add_argument("--val-data", default="validationdata-small.npz")
    p.add_argument(
        "--cache",
        action="store_true",
        help="Cache preprocessed tensors in RAM after first epoch",
    )

    # training
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument(
        "--grad-clip", type=float, default=1.0, help="Max gradient norm (0 = disabled)"
    )
    p.add_argument(
        "--type-weight",
        type=float,
        default=0.0,
        help="Weight for auxiliary synthetic-vs-midi loss (0 = off)",
    )

    # misc
    p.add_argument("--num-workers", type=int, default=4)
    p.add_argument("--out-dir", default="checkpoints/")

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
