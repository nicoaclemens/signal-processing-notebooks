# used by: cells\filter_chain\ui.py
import matplotlib.pyplot as plt
import numpy as np

from utils.STYLES import COLORS
from utils.ui import dark_ax

from .helpers import FFT_PLOT_COLORS, N_PERIOD, PLOT, _eval_fourier_H, _with_knob
from utils.filters import apply_transform, eval_kernel


def _plot_filter_response(output_widget, cfg, freq):
    c = FFT_PLOT_COLORS
    ft = cfg["type"]
    if not cfg.get("enabled", True):
        with output_widget:
            output_widget.clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
            fig.patch.set_facecolor(c["bg"])
            dark_ax(ax1)
            dark_ax(ax2)
            for ax in (ax1, ax2):
                ax.text(
                    0.5,
                    0.5,
                    "Bypassed",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=COLORS.text_muted,
                    fontsize=PLOT.empty_fontsize,
                )
            plt.tight_layout()
            plt.show()
            plt.close(fig)
        return

    period_s = 1.0 / freq

    def _freq_xlim(mag):
        peak = np.max(np.abs(mag))
        if peak == 0:
            return len(mag) - 1
        thresh = peak * 0.01
        nonzero = np.where(np.abs(mag) > thresh)[0]
        last = int(nonzero[-1]) if len(nonzero) else 0
        return max(last * 1.3, 1)

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        try:
            if ft == "fourier":
                k = np.arange(N_PERIOD // 2 + 1)
                H = _eval_fourier_H(cfg, k, freq)
                mag = np.abs(H)
                h = np.fft.irfft(H, n=N_PERIOD)
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, h, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Impulse Response  h(t)",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Amplitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )

            elif ft == "convolution":
                kernel = eval_kernel(
                    _with_knob(cfg["kernel_text"], cfg["knob_effective"]), N_PERIOD
                )
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, kernel, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Kernel  h(t)",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Amplitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
                K = np.fft.rfft(kernel)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )

            elif ft == "transform":
                s_in = np.linspace(-1, 1, N_PERIOD)
                expr = _with_knob(cfg["expr_text"], cfg["knob_effective"])
                s_out = apply_transform(s_in, expr)
                ax1.plot(s_in, s_out, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Transfer Curve",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Input  s", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Output  g(s)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                delta = np.zeros(N_PERIOD)
                delta[0] = 1.0
                imp = apply_transform(delta, expr)
                K = np.fft.rfft(imp)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Spectrum of Impulse Output",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
        except Exception:
            for ax in (ax1, ax2):
                ax.text(
                    0.5,
                    0.5,
                    "Error",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=COLORS.text_muted,
                    fontsize=PLOT.empty_fontsize,
                )

        plt.tight_layout()
        plt.show()
        plt.close(fig)


def _plot_uploaded_signal_and_fft(output_widget, signal, sample_rate, label="filtered"):
    c = FFT_PLOT_COLORS

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        n = len(signal)
        if n == 0:
            ax1.text(
                0.5,
                0.5,
                "No signal",
                ha="center",
                va="center",
                transform=ax1.transAxes,
                color=COLORS.text_muted,
                fontsize=PLOT.empty_fontsize,
            )
            ax2.text(
                0.5,
                0.5,
                "No spectrum",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                color=COLORS.text_muted,
                fontsize=PLOT.empty_fontsize,
            )
        else:
            preview_samples = min(n, max(int(sample_rate * 0.08), 256))
            t_ms = np.arange(preview_samples) / sample_rate * 1000.0
            ax1.plot(
                t_ms,
                signal[:preview_samples],
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
            )
            ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize)
            ax1.set_ylabel("Amplitude", color=c["label"], fontsize=PLOT.label_fontsize)
            ax1.set_title(
                "Waveform Preview",
                color=c["title"],
                fontsize=PLOT.title_fontsize,
                pad=PLOT.title_pad,
            )

            win_len = min(n, sample_rate)
            windowed = signal[:win_len]
            spectrum = np.fft.rfft(windowed)
            mags = np.abs(spectrum)
            freqs = np.fft.rfftfreq(win_len, d=1.0 / sample_rate)
            x_max = min(sample_rate / 2, 5000)
            mask = freqs <= x_max

            ax2.plot(
                freqs[mask],
                mags[mask],
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
                alpha=PLOT.line_alpha,
                label=label,
            )
            ax2.set_xlabel(
                "Frequency [Hz]", color=c["label"], fontsize=PLOT.label_fontsize
            )
            ax2.set_ylabel("Magnitude", color=c["label"], fontsize=PLOT.label_fontsize)
            ax2.set_title(
                "Fourier Transform",
                color=c["title"],
                fontsize=PLOT.title_fontsize,
                pad=PLOT.title_pad,
            )
            ax2.set_xlim(0, x_max)
            ax2.legend(
                fontsize=PLOT.legend_fontsize,
                facecolor=c["legend"],
                edgecolor=c["ledge"],
                labelcolor=c["ltxt"],
                loc="upper right",
            )

        plt.tight_layout()
        plt.show()
        plt.close(fig)


__all__ = ["_plot_filter_response", "_plot_uploaded_signal_and_fft"]
