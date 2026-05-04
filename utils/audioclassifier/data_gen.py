import numpy as np
import pretty_midi
from tqdm import tqdm
import os


# -------------------- SIGNAL GENERATORS --------------------

def supersaw(f, t, voices=7, detune=0.01):
    result = np.zeros_like(t, dtype=np.float32)
    for i in range(voices):
        offset = (i - voices // 2) * detune
        freq = f * (1 + offset)
        phi = np.random.uniform(0, 1)
        p = t * freq + phi
        result += 2 * (p - np.floor(p + 0.5))
    return (result / voices).astype(np.float32)


def saw(f, t):
    phi = np.random.uniform(0, 1)
    p = t * f + phi
    return (2 * (p - np.floor(p + 0.5))).astype(np.float32)


def triangle(f, t):
    phi = np.random.uniform(0, 1)
    p = t * f + phi
    return (2 * np.abs(2 * (p - np.floor(p + 0.5))) - 1).astype(np.float32)


def sine(f, t):
    phi = np.random.uniform(0, 2 * np.pi)
    return np.sin(2 * np.pi * f * t + phi).astype(np.float32)


def square(f, t):
    phi = np.random.uniform(0, 2 * np.pi)
    return np.sign(np.sin(2 * np.pi * f * t + phi)).astype(np.float32)


generators = {
    "sine": sine,
    "square": square,
    "saw": saw,
    "triangle": triangle,
    "supersaw": supersaw,
}


midi_programs = {
    "acoustic_grand_piano": 0,
    "bright_acoustic_piano": 1,
    "electric_piano": 4,
    "harpsichord": 6,
    "drawbar_organ": 16,
    "church_organ": 19,
    "celesta": 8,
    "glockenspiel": 9,
    "acoustic_guitar_nylon": 24,
    "electric_guitar_muted": 28,
    "electric_guitar_overdriven": 29,
    "electric_bass_finger": 33,
    "string_ensemble": 48,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "french_horn": 60,
    "soprano_sax": 64,
    "oboe": 68,
    "bassoon": 70,
    "clarinet": 71,
    "flute": 73,
    "timpani": 47,
}


# -------------------- AUDIO UTILS --------------------

def apply_random_adsr(audio, fs):
    n = len(audio)
    a = int(np.random.uniform(0.005, 0.05) * fs)
    d = int(np.random.uniform(0.01, 0.1) * fs)
    s_level = np.random.uniform(0.5, 0.9)
    r = int(np.random.uniform(0.01, 0.1) * fs)

    env = np.ones(n, dtype=np.float32) * s_level
    env[:a] = np.linspace(0, 1, a, dtype=np.float32)
    env[a:a + d] = np.linspace(1, s_level, d, dtype=np.float32)
    env[max(0, n - r):] = np.linspace(s_level, 0, min(r, n), dtype=np.float32)
    return audio * env


def _freq_to_midi_pitch(freq):
    pitch = int(round(69 + 12 * np.log2(freq / 440.0)))
    return max(0, min(127, pitch))


# -------------------- SAMPLE GENERATION --------------------

def gen_samples(generator, frequency, fs, samples):
    t = np.arange(samples, dtype=np.float32) / fs
    return generator(frequency, t)


def gen_samples_midi(program, frequency, fs, samples):
    duration = samples / fs

    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=program)

    note = pretty_midi.Note(
        velocity=np.random.randint(60, 110),
        pitch=_freq_to_midi_pitch(frequency),
        start=0.0,
        end=duration,
    )

    inst.notes.append(note)
    pm.instruments.append(inst)

    audio = pm.fluidsynth(fs=fs)

    if audio.ndim > 1:
        audio = audio.mean(axis=0)

    if len(audio) < samples:
        audio = np.pad(audio, (0, samples - len(audio)))
    else:
        audio = audio[:samples]

    return audio.astype(np.float32)


# -------------------- STREAMING DATASET BUILDER --------------------

def build_dataset_streaming(
    out_path,
    generators,
    midi_programs,
    samples_per_class=1000,
    fs=44100,
    n_samples=32768,
    f_lo=40,
    f_hi=2000,
):
    class_names = list(generators.keys()) + list(midi_programs.keys())
    class_type = [0] * len(generators) + [1] * len(midi_programs)

    total_classes = len(class_names)
    total_samples = total_classes * samples_per_class

    print(f"Total samples: {total_samples}")

    # Create memmap files
    X = np.memmap(out_path + "_X.dat", dtype=np.float32, mode="w+",
                  shape=(total_samples, n_samples))
    y_label = np.memmap(out_path + "_y_label.dat", dtype=np.int64, mode="w+",
                        shape=(total_samples,))
    y_type = np.memmap(out_path + "_y_type.dat", dtype=np.int64, mode="w+",
                       shape=(total_samples,))

    idx = 0

    for class_idx in tqdm(range(total_classes), desc="Classes"):
        name = class_names[class_idx]
        is_midi = class_type[class_idx]

        for _ in tqdm(range(samples_per_class), leave=False):

            freq = np.exp(np.random.uniform(np.log(f_lo), np.log(f_hi)))

            if is_midi == 0:
                audio = gen_samples(generators[name], freq, fs, n_samples)
                audio = apply_random_adsr(audio, fs)
            else:
                audio = gen_samples_midi(midi_programs[name], freq, fs, n_samples)

            # augment
            audio += np.random.normal(0, 1e-4, len(audio)).astype(np.float32)
            audio /= (np.max(np.abs(audio)) + 1e-8)
            audio *= np.random.uniform(0.3, 1.0)

            X[idx] = audio
            y_label[idx] = class_idx
            y_type[idx] = is_midi

            idx += 1

    X.flush()
    y_label.flush()
    y_type.flush()

    np.savez(
        out_path + "_meta.npz",
        class_names=np.array(class_names),
        class_type=np.array(class_type),
        fs=fs,
        samples=n_samples,
    )

    print(f"Dataset written to {out_path}_*.dat")


if __name__ == "__main__":
    np.random.seed(42)

    N_TOTAL_PER_CLASS = 3000

    splits = {
        "trainingdata": int(0.8 * N_TOTAL_PER_CLASS),
        "validationdata": int(0.1 * N_TOTAL_PER_CLASS),
        "testingdata": int(0.1 * N_TOTAL_PER_CLASS),
    }

    for name, spc in splits.items():
        build_dataset_streaming(
            name,
            generators,
            midi_programs,
            samples_per_class=spc,
        )

        meta = np.load(name + "_meta.npz", allow_pickle=True)
        class_names = meta["class_names"]
        class_type = meta["class_type"]
        fs = int(meta["fs"])
        n_samples = int(meta["samples"])

        total_classes = len(class_names)
        total_samples = total_classes * spc

        X = np.memmap(
            name + "_X.dat",
            dtype=np.float32,
            mode="r",
            shape=(total_samples, n_samples),
        )

        y_label = np.memmap(
            name + "_y_label.dat",
            dtype=np.int64,
            mode="r",
            shape=(total_samples,),
        )

        y_type = np.memmap(
            name + "_y_type.dat",
            dtype=np.int64,
            mode="r",
            shape=(total_samples,),
        )

        np.savez_compressed(
            name + ".npz",
            X=X,
            y_label=y_label,
            y_type=y_type,
            class_names=class_names,
            class_type=class_type,
            fs=fs,
            samples=n_samples,
        )

        print(f"Saved {name}.npz (DAT files retained)")