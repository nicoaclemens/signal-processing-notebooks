# used by:
import numpy as np
import argparse
import sounddevice as sd
import matplotlib.pyplot as plt


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
    try:
        idx = int(query)
        if idx < 0 or idx >= len(class_names):
            raise ValueError("Invalid class index")
        return idx
    except ValueError as e:
        if "Invalid class index" in str(e):
            raise
    matches = [i for i, n in enumerate(class_names) if query.lower() in n.lower()]
    if not matches:
        raise ValueError("No matching class name")
    if len(matches) > 1:
        print("Multiple matches:", [class_names[i] for i in matches])
        raise ValueError("Ambiguous class name")
    return matches[0]


def class_stats(ds, class_idx):
    samples = ds["X"][ds["y_label"] == class_idx]
    print(
        f"  min={samples.min():.4f} max={samples.max():.4f} mean_rms={np.sqrt(np.mean(samples**2)):.4f}"
    )
    silent = np.sum(np.max(np.abs(samples), axis=1) < 1e-4)
    if silent:
        print(f"  WARNING: {silent} silent samples detected")


def plot_sample(audio, fs, class_name, sample_idx):
    t = np.arange(len(audio)) / fs

    fft_mag = np.abs(np.fft.rfft(audio))
    fft_freqs = np.fft.rfftfreq(len(audio), d=1.0 / fs)

    peak_idx = np.argmax(fft_mag)
    peak_freq = max(fft_freqs[peak_idx], 1.0)
    period = 1.0 / peak_freq

    t_mid = t[len(t) // 2]
    t_lo = t_mid - 1.5 * period
    t_hi = t_mid + 1.5 * period

    fft_x_max = min(max(peak_freq * 12, 2_000), fs / 2)
    freq_mask = fft_freqs <= fft_x_max
    fft_mag_db = 20 * np.log10(fft_mag[freq_mask] + 1e-8)

    fig, (ax_sig, ax_fft) = plt.subplots(2, 1, figsize=(12, 6))
    fig.suptitle(
        f"{class_name}  —  sample #{sample_idx}  —  peak {peak_freq:.1f} Hz",
        fontsize=13,
    )

    ax_sig.plot(t, audio, linewidth=0.6, color="steelblue")
    ax_sig.set_xlabel("Time (s)")
    ax_sig.set_ylabel("Amplitude")
    ax_sig.set_title(f"Waveform (3 periods @ {peak_freq:.1f} Hz)")
    ax_sig.set_xlim(t_lo, t_hi)
    ax_sig.axhline(0, color="gray", linewidth=0.4)

    ax_fft.plot(fft_freqs[freq_mask], fft_mag_db, linewidth=0.7, color="coral")
    ax_fft.set_xlabel("Frequency (Hz)")
    ax_fft.set_ylabel("Magnitude (dB)")
    ax_fft.set_title(f"FFT (0 – {fft_x_max:.0f} Hz)")
    ax_fft.set_xlim(0, fft_x_max)
    ax_fft.axvline(peak_freq, color="gray", linewidth=0.8, linestyle="--")
    ax_fft.annotate(
        f"{peak_freq:.1f} Hz",
        xy=(peak_freq, fft_mag_db[peak_idx]),
        xytext=(peak_freq + fft_x_max * 0.02, fft_mag_db[peak_idx] - 5),
        fontsize=8,
        color="gray",
    )

    plt.tight_layout()
    plt.show()


def play_random(ds, class_idx):
    X = ds["X"]
    y = ds["y_label"]
    fs = ds["fs"]
    class_name = ds["class_names"][class_idx]

    indices = np.where(y == class_idx)[0]
    if len(indices) == 0:
        print("No samples in this class")
        return

    i = np.random.choice(indices)
    audio = X[i]
    print(f"\nPlaying sample index {i} (class {class_idx}: {class_name})")

    sd.play(audio, fs)
    plot_sample(audio, fs, class_name, i)
    sd.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to .npz dataset")
    parser.add_argument("--class", dest="cls", help="Class index or name (optional)")
    parser.add_argument("--play", action="store_true", help="Play random sample")
    args = parser.parse_args()

    if args.play and args.cls is None:
        parser.error("--play requires --class")

    ds = load_dataset(args.path)
    overview(ds)

    if args.cls is not None:
        idx = select_class(ds, args.cls)
        print(f"\nSelected class [{idx}] {ds['class_names'][idx]}")
        class_stats(ds, idx)
        if args.play:
            play_random(ds, idx)


if __name__ == "__main__":
    main()
