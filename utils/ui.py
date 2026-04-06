# used by: cells\epicycles.py, cells\filter_chain.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py
import ipywidgets as widgets
import numpy as np
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt

SECTION_STYLE = "margin:0 0 2px 0; color:#aaa; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;"
SLIDER_LAYOUT = widgets.Layout(width="340px")
DD_LAYOUT = widgets.Layout(width="160px")
CB_LAYOUT = widgets.Layout(width="auto")

FFT_PLOT_COLORS = {
    "bg": "#1a1a2e",
    "grid": "#2a2a4a",
    "spine": "#3a3a5a",
    "label": "#aaa",
    "title": "#ddd",
    "tick": "#888",
    "legend": "#2d2d4a",
    "ledge": "#4a4a6a",
    "ltxt": "#e0e0e0",
}


def section(title):
    return widgets.HTML(f'<p style="{SECTION_STYLE}">{title}</p>')


def dark_ax(ax):
    c = FFT_PLOT_COLORS
    ax.set_facecolor(c["bg"])
    ax.tick_params(colors=c["tick"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(c["spine"])
    ax.grid(True, color=c["grid"], linewidth=0.5)


def plot_waveform_and_fft(output_widget, one_period, freq, label="signal"):
    c = FFT_PLOT_COLORS
    fs = 44100
    N = fs  # 1 second

    has_signal = one_period is not None and np.any(one_period != 0)

    # synthesise 1 s from one period
    if has_signal:
        t = np.linspace(0, 1, N, endpoint=False)
        phase = (t * freq) % 1.0
        indices = phase * (len(one_period) - 1)
        signal = np.interp(indices, np.arange(len(one_period)), one_period)
    else:
        t = np.linspace(0, 1, N, endpoint=False)
        signal = np.zeros(N)

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3))
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        # waveform preview (3 periods)
        if has_signal:
            n_periods = 3
            total_t = n_periods / freq
            n_samples = max(int(fs * total_t), 128)
            t_preview = np.linspace(0, total_t, n_samples, endpoint=False)
            phase_p = (t_preview * freq) % 1.0
            idx_p = phase_p * (len(one_period) - 1)
            preview = np.interp(idx_p, np.arange(len(one_period)), one_period)
            ax1.plot(t_preview * 1000, preview, color="#7c6ff7", linewidth=1.2)
        else:
            ax1.axhline(0, color="#4a4a6a", linewidth=1)

        ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=10)
        ax1.set_ylabel("Amplitude", color=c["label"], fontsize=10)
        ax1.set_title("Waveform Preview", color=c["title"], fontsize=11, pad=6)

        # FFT (same style as frequency_multiplication)
        freqs = fftfreq(N, 1 / fs)[: N // 2]
        x_max = freq * 20

        if has_signal:
            magnitudes = 2.0 / N * np.abs(fft(signal)[: N // 2])
            mask = freqs <= x_max
            ax2.plot(
                freqs[mask],
                magnitudes[mask],
                label=label,
                color="#7c6ff7",
                linewidth=1.2,
                alpha=0.9,
            )
            ax2.legend(
                fontsize=9,
                facecolor=c["legend"],
                edgecolor=c["ledge"],
                labelcolor=c["ltxt"],
                loc="upper right",
            )
        else:
            ax2.text(
                0.5,
                0.5,
                "No signal",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                color="#666",
                fontsize=12,
            )

        ax2.set_xlabel("Frequency [Hz]", color=c["label"], fontsize=10)
        ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)
        ax2.set_title("Fourier Transform", color=c["title"], fontsize=11, pad=6)
        ax2.set_xlim(0, x_max)

        plt.tight_layout()
        plt.show()
        plt.close(fig)
