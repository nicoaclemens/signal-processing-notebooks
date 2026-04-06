# used by:
import numpy as np
from scipy.fft import fft, fftfreq
import ipywidgets
from utils import PlotManager


def plot_signals(f1, f2, fs):
    """
    Plot time-domain signals and their frequency spectra using PlotManager.

    Args:
        f1: Frequency of first signal in Hz
        f2: Frequency of second signal in Hz
        fs: Sampling frequency (number of samples)
    """
    p = PlotManager()
    p.fs = fs

    p.add_plot(
        y={
            f"f1 = {f1} Hz": lambda t: np.sin(2 * np.pi * f1 * t),
            f"f2 = {f2} Hz": lambda t: np.sin(2 * np.pi * f2 * t),
        },
        x_min=0,
        x_max=1,
        title="Signals x1 and x2",
        xlabel="Time [s]",
        ylabel="Amplitude",
    )

    p.add_plot(
        y=lambda t: np.sin(2 * np.pi * f1 * t) * np.sin(2 * np.pi * f2 * t),
        x_min=0,
        x_max=1,
        title="Multiplication x1 * x2",
        xlabel="Time [s]",
        ylabel="Amplitude",
        color="purple",
    )

    nfft = 2**20  # Zero-padding

    def fft_x1(freq):
        t = np.linspace(0, 1, fs, endpoint=False)
        x1 = np.sin(2 * np.pi * f1 * t)
        X1 = fft(x1, n=nfft)
        freqs = fftfreq(nfft, 1 / fs)[: nfft // 2]
        magnitudes = np.abs(X1[: nfft // 2])
        return np.interp(freq, freqs, magnitudes)

    def fft_x2(freq):
        t = np.linspace(0, 1, fs, endpoint=False)
        x2 = np.sin(2 * np.pi * f2 * t)
        X2 = fft(x2, n=nfft)
        freqs = fftfreq(nfft, 1 / fs)[: nfft // 2]
        magnitudes = np.abs(X2[: nfft // 2])
        return np.interp(freq, freqs, magnitudes)

    def fft_mult(freq):
        t = np.linspace(0, 1, fs, endpoint=False)
        x_mult = np.sin(2 * np.pi * f1 * t) * np.sin(2 * np.pi * f2 * t)
        X_mult = fft(x_mult, n=nfft)
        freqs = fftfreq(nfft, 1 / fs)[: nfft // 2]
        magnitudes = np.abs(X_mult[: nfft // 2])
        return np.interp(freq, freqs, magnitudes)

    p.add_plot(
        y={"X1": fft_x1, "X2": fft_x2, "X1*X2": fft_mult},
        fs=(f1 + f2) * 128,
        x_min=0,
        x_max=(f1 + f2) * 2,
        title="Fourier Transforms",
        xlabel="Frequency [Hz]",
        ylabel="Magnitude",
    )

    p.render()
