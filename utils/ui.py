# used by: cells\epicycles.py, cells\filter_chain\plotting.py, cells\filter_chain\ui.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py, cells\synthesizer.py
import numpy as np
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from utils.STYLES import (
    COLORS,
    FFT_PLOT_COLORS,
    PLOT,
    SECTION_STYLE,
    SLIDER_LAYOUT,
    DD_LAYOUT,
    CB_LAYOUT,
)
import ipywidgets as widgets


def section(title):
    return widgets.HTML(f'<p style="{SECTION_STYLE}">{title}</p>')


def dark_ax(ax):
    c = FFT_PLOT_COLORS
    ax.set_facecolor(c["bg"])
    ax.tick_params(colors=c["tick"], labelsize=PLOT.tick_labelsize)
    for spine in ax.spines.values():
        spine.set_color(c["spine"])
    ax.grid(True, color=c["grid"], linewidth=PLOT.grid_linewidth)


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
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
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
            ax1.plot(
                t_preview * 1000,
                preview,
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
            )
        else:
            ax1.axhline(0, color=COLORS.surface_lighter, linewidth=1)

        ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize)
        ax1.set_ylabel("Amplitude", color=c["label"], fontsize=PLOT.label_fontsize)
        ax1.set_title(
            "Waveform Preview",
            color=c["title"],
            fontsize=PLOT.title_fontsize,
            pad=PLOT.title_pad,
        )

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
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
                alpha=PLOT.line_alpha,
            )
            ax2.legend(
                fontsize=PLOT.legend_fontsize,
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
                color=COLORS.text_muted,
                fontsize=PLOT.empty_fontsize,
            )

        ax2.set_xlabel("Frequency [Hz]", color=c["label"], fontsize=PLOT.label_fontsize)
        ax2.set_ylabel("Magnitude", color=c["label"], fontsize=PLOT.label_fontsize)
        ax2.set_title(
            "Fourier Transform",
            color=c["title"],
            fontsize=PLOT.title_fontsize,
            pad=PLOT.title_pad,
        )
        ax2.set_xlim(0, x_max)

        plt.tight_layout()
        plt.show()
        plt.close(fig)
