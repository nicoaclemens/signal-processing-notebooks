import numpy as np
import argparse
import sounddevice as sd


def load_dataset(path):
    data = np.load(path, allow_pickle=True)

    X = data["X"]
    y_label = data["y_label"]
    y_type = data["y_type"]
    class_names = data["class_names"]
    class_type = data["class_type"]
    fs = int(data["fs"])
    samples = int(data["samples"])

    return {
        "X": X,
        "y_label": y_label,
        "y_type": y_type,
        "class_names": class_names,
        "class_type": class_type,
        "fs": fs,
        "samples": samples,
    }


def overview(ds):
    X = ds["X"]
    y = ds["y_label"]
    class_names = ds["class_names"]
    class_type = ds["class_type"]

    print("\n=== DATASET OVERVIEW ===")
    print(f"X shape        : {X.shape}")
    print(f"dtype          : {X.dtype}")
    print(f"sample length  : {ds['samples']}")
    print(f"sample rate    : {ds['fs']}")
    print(f"num classes    : {len(class_names)}")

    print("\n--- Classes ---")
    for i, name in enumerate(class_names):
        count = np.sum(y == i)
        t = "synth" if class_type[i] == 0 else "midi"
        print(f"[{i:02d}] {name:30s} | type={t:5s} | samples={count}")


def select_class(ds, query):
    class_names = ds["class_names"]

    # index
    if query.isdigit():
        idx = int(query)
        if idx < 0 or idx >= len(class_names):
            raise ValueError("Invalid class index")
        return idx

    # name
    matches = [i for i, n in enumerate(class_names) if query.lower() in n.lower()]
    if not matches:
        raise ValueError("No matching class name")
    if len(matches) > 1:
        print("Multiple matches:", [class_names[i] for i in matches])
        raise ValueError("Ambiguous class name")

    return matches[0]


def play_random(ds, class_idx):
    X = ds["X"]
    y = ds["y_label"]
    fs = ds["fs"]

    indices = np.where(y == class_idx)[0]
    if len(indices) == 0:
        print("No samples in this class")
        return

    i = np.random.choice(indices)
    audio = X[i]

    print(f"\nPlaying sample index {i} (class {class_idx})")
    sd.play(audio, fs)
    sd.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to .npz dataset")
    parser.add_argument("--class", dest="cls", help="Class index or name (optional)")
    parser.add_argument("--play", action="store_true", help="Play random sample")
    args = parser.parse_args()

    ds = load_dataset(args.path)
    overview(ds)

    if args.cls is not None:
        idx = select_class(ds, args.cls)
        print(f"\nSelected class [{idx}] {ds['class_names'][idx]}")

        if args.play:
            play_random(ds, idx)


if __name__ == "__main__":
    main()