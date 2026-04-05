import ipywidgets as widgets
import numpy as np
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from widget import AudioWidget, DrawWidget
from utils.signals import samples_to_fourier_coeffs
from utils.ui import section, dark_ax, SLIDER_LAYOUT, FFT_PLOT_COLORS


def create_custom_wave_ui(f_init=440):

    draw = DrawWidget()

    audio = AudioWidget(
        components=[
            {
                "id": "main",
                "label": "custom wave",
                "oscs": [{"freq": f_init, "gain": 1.0}],
                "enabled": True,
            },
        ],
    )
    audio.waveforms = {"main": "custom"}

    freq_slider = widgets.FloatSlider(
        value=f_init,
        min=20,
        max=2000,
        step=1,
        description="Frequency",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "72px"},
        readout_format=".0f",
    )
    vol_slider = widgets.FloatSlider(
        value=0.5,
        min=0.0,
        max=1.0,
        step=0.05,
        description="Vol",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "24px"},
    )

    widgets.jslink((vol_slider, "value"), (audio, "volume"))

    fft_out = widgets.Output()

    # cb

    def _push_coeffs():
        samples = draw.samples
        if not samples or all(s == 0 for s in samples):
            audio.periodic_real_coeffs = []
            audio.periodic_coeffs = []
        else:
            real_c, imag_c = samples_to_fourier_coeffs(samples)
            audio.periodic_real_coeffs = real_c
            audio.periodic_coeffs = imag_c
        audio.waveforms = {"main": "custom"}

    def _on_samples(change=None):
        _push_coeffs()
        _update_plots()

    def _on_freq(change=None):
        audio.frequencies = {"main": [freq_slider.value]}
        _update_plots()

    def _update_plots():
        samples = draw.samples
        freq = freq_slider.value
        c = FFT_PLOT_COLORS

        with fft_out:
            fft_out.clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3))
            fig.patch.set_facecolor(c["bg"])
            dark_ax(ax1)
            dark_ax(ax2)

            has_signal = samples and any(s != 0 for s in samples)

            # preview
            if has_signal:
                arr = np.array(samples)
                n_periods = 3
                total_t = n_periods / freq
                fs = 44100
                N = max(int(fs * total_t), 128)
                t = np.linspace(0, total_t, N, endpoint=False)
                phase = (t * freq) % 1.0
                indices = phase * (len(arr) - 1)
                signal = np.interp(indices, np.arange(len(arr)), arr)
                ax1.plot(t * 1000, signal, color="#7c6ff7", linewidth=1.2)
            else:
                ax1.axhline(0, color="#4a4a6a", linewidth=1)

            ax1.set_xlabel("Time (ms=", color=c["label"], fontsize=10)
            ax1.set_ylabel("Amplitude", color=c["label"], fontsize=10)
            ax1.set_title("Waveform Preview", color=c["title"], fontsize=11, pad=6)

            if has_signal:
                arr = np.array(samples)
                spectrum = np.fft.rfft(arr)
                magnitudes = np.abs(spectrum[1:]) * 2 / len(arr)
                harmonics = np.arange(1, len(magnitudes) + 1)
                n_show = min(32, len(magnitudes))
                ax2.bar(
                    harmonics[:n_show] * freq,
                    magnitudes[:n_show],
                    width=freq * 0.6,
                    color="#7c6ff7",
                    alpha=0.8,
                )
                ax2.set_xlim(0, (n_show + 1) * freq)

            ax2.set_xlabel("Frequency (Hz)", color=c["label"], fontsize=10)
            ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)
            ax2.set_title("Harmonic Spectrum", color=c["title"], fontsize=11, pad=6)

            plt.tight_layout()
            plt.show()
            plt.close(fig)

    draw.observe(_on_samples, "samples")
    freq_slider.observe(_on_freq, "value")

    _push_coeffs()
    _update_plots()

    controls = widgets.VBox(
        [
            section("Frequency"),
            freq_slider,
            section("Volume"),
            vol_slider,
        ]
    )

    return widgets.VBox([draw, controls, audio, fft_out])
