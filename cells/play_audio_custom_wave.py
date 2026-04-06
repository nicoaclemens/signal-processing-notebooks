import ipywidgets as widgets
import numpy as np
from widget import AudioWidget, DrawWidget
from utils.signals import samples_to_fourier_coeffs
from utils.ui import section, SLIDER_LAYOUT, plot_waveform_and_fft


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
        one_period = np.array(samples) if samples else None
        plot_waveform_and_fft(fft_out, one_period, freq, label="custom wave")

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
