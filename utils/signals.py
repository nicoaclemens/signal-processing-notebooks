# used by: cells\filter_chain.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py
import numpy as np

WAVE_FUNCS = {
    "sine": lambda t, f: np.sin(2 * np.pi * f * t),
    "sawtooth": lambda t, f: 2 * (f * t - np.floor(0.5 + f * t)),
    "square": lambda t, f: np.sign(np.sin(2 * np.pi * f * t)),
    "triangle": lambda t, f: 2 * np.abs(2 * (f * t - np.floor(0.5 + f * t))) - 1,
}


def parse_coeffs(text):
    try:
        coeffs = [float(x.strip()) for x in text.split(",") if x.strip()]
        return coeffs if coeffs else [1.0]
    except ValueError:
        return [1.0]


def custom_wave(t, f, coeffs):
    sig = np.zeros_like(t)
    for n, c in enumerate(coeffs, 1):
        sig += c * np.sin(2 * np.pi * n * f * t)
    mx = np.max(np.abs(sig))
    return sig / mx if mx > 0 else sig


def samples_to_fourier_coeffs(samples, n_harmonics=64):
    samples = np.asarray(samples, dtype=float)
    N = len(samples)
    if N == 0:
        return [], []

    spectrum = np.fft.rfft(samples)
    n_harm = min(n_harmonics, len(spectrum) - 1)

    real_coeffs = (2 * spectrum[1 : n_harm + 1].real / N).tolist()
    imag_coeffs = (-2 * spectrum[1 : n_harm + 1].imag / N).tolist()

    return real_coeffs, imag_coeffs
