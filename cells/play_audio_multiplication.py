import ipywidgets as widgets
import numpy as np
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from widget import AudioWidget
from utils.signals import WAVE_FUNCS, parse_coeffs, custom_wave
from utils.ui import (
    section,
    dark_ax,
    SLIDER_LAYOUT,
    DD_LAYOUT,
    CB_LAYOUT,
    FFT_PLOT_COLORS,
)

_WAVE_OPTIONS = [
    ("Sine", "sine"),
    ("Sawtooth", "sawtooth"),
    ("Square", "square"),
    ("Triangle", "triangle"),
    ("Custom", "custom"),
]


def create_audio_ui(f1_init=440, f2_init=330):
    """
    Build the frequency-multiplication audio playback UI.

    """
    f1, f2 = f1_init, f2_init

    audio = AudioWidget(
        components=[
            {
                "id": "x1",
                "label": "x\u2081(t)",
                "oscs": [{"freq": f1, "gain": 1.0}],
                "enabled": True,
            },
            {
                "id": "x2",
                "label": "x\u2082(t)",
                "oscs": [{"freq": f2, "gain": 1.0}],
                "enabled": False,
            },
            {
                "id": "product",
                "label": "x\u2081 \u00b7 x\u2082",
                "mode": "multiply",
                "oscs": [{"freq": f1, "gain": 1.0}, {"freq": f2, "gain": 1.0}],
                "enabled": False,
            },
            {
                "id": "f_sum",
                "label": "f\u2081+f\u2082",
                "oscs": [{"freq": f1 + f2, "gain": 1.0}],
                "enabled": False,
            },
            {
                "id": "f_diff",
                "label": "|f\u2081\u2212f\u2082|",
                "oscs": [{"freq": abs(f1 - f2), "gain": 1.0}],
                "enabled": False,
            },
        ],
    )

    f1_slider = widgets.FloatSlider(
        value=f1,
        min=10,
        max=1000,
        step=10,
        description="f\u2081",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "24px"},
        readout_format=".0f",
    )
    f2_slider = widgets.FloatSlider(
        value=f2,
        min=10,
        max=1000,
        step=10,
        description="f\u2082",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "24px"},
        readout_format=".0f",
    )
    f2_mult = widgets.FloatLogSlider(
        value=1,
        base=10,
        min=-3,
        max=3,
        step=0.1,
        description="f\u2082 mult",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "50px"},
    )
    vol_slider = widgets.FloatSlider(
        value=0.5,
        min=0.0,
        max=1.0,
        step=0.05,
        description="\U0001f50a",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "24px"},
    )

    wave_x1 = widgets.Dropdown(
        options=_WAVE_OPTIONS,
        value="sine",
        description="x\u2081 shape",
        layout=DD_LAYOUT,
        style={"description_width": "56px"},
    )
    wave_x2 = widgets.Dropdown(
        options=_WAVE_OPTIONS,
        value="sine",
        description="x\u2082 shape",
        layout=DD_LAYOUT,
        style={"description_width": "56px"},
    )
    custom_input = widgets.Text(
        value="1,0.5,0.33,0.25",
        description="Harmonics",
        placeholder="e.g. 1,0.5,0.33,0.25",
        layout=widgets.Layout(width="340px", display="none"),
        style={"description_width": "64px"},
    )

    cb_x1 = widgets.Checkbox(
        value=True,
        description="x\u2081(t) = sin(2\u03c0f\u2081t)",
        layout=CB_LAYOUT,
        indent=False,
    )
    cb_x2 = widgets.Checkbox(
        value=False,
        description="x\u2082(t) = sin(2\u03c0f\u2082t)",
        layout=CB_LAYOUT,
        indent=False,
    )
    cb_product = widgets.Checkbox(
        value=False,
        description="x\u2081(t) \u00b7 x\u2082(t)",
        layout=CB_LAYOUT,
        indent=False,
    )
    cb_f_sum = widgets.Checkbox(
        value=False, description="sum component", layout=CB_LAYOUT, indent=False
    )
    cb_f_diff = widgets.Checkbox(
        value=False, description="diff component", layout=CB_LAYOUT, indent=False
    )

    _FREQ_LABEL = "font-size:12px; color:#333; font-family:monospace;"
    freq_info = widgets.HTML()

    def _update_freq_info():
        fv1 = f1_slider.value
        fv2 = f2_slider.value * f2_mult.value
        freq_info.value = (
            f'<span style="{_FREQ_LABEL}">'
            f"f\u2081+f\u2082 = <b>{fv1 + fv2:.0f}</b> Hz &nbsp;\u2502&nbsp; "
            f"|f\u2081\u2212f\u2082| = <b>{abs(fv1 - fv2):.0f}</b> Hz"
            f"</span>"
        )

    _update_freq_info()

    widgets.jslink((vol_slider, "value"), (audio, "volume"))

    def _update_freqs(change=None):
        fv1 = f1_slider.value
        fv2 = f2_slider.value * f2_mult.value
        _update_freq_info()
        audio.frequencies = {
            "x1": [fv1],
            "x2": [fv2],
            "product": [fv1, fv2],
            "f_sum": [fv1 + fv2],
            "f_diff": [abs(fv1 - fv2)],
        }
        _update_fft()

    def _update_enables(change=None):
        audio.enables = {
            "x1": cb_x1.value,
            "x2": cb_x2.value,
            "product": cb_product.value,
            "f_sum": cb_f_sum.value,
            "f_diff": cb_f_diff.value,
        }
        _update_fft()

    def _update_waveforms(change=None):
        w1, w2 = wave_x1.value, wave_x2.value
        show_custom = w1 == "custom" or w2 == "custom"
        custom_input.layout.display = "" if show_custom else "none"
        if show_custom:
            audio.periodic_coeffs = parse_coeffs(custom_input.value)
        audio.waveforms = {
            "x1": w1,
            "x2": w2,
            "product": [w1, w2],  # per oscillator
            "f_sum": "sine",
            "f_diff": "sine",
        }
        _update_fft()

    f1_slider.observe(_update_freqs, "value")
    f2_slider.observe(_update_freqs, "value")
    f2_mult.observe(_update_freqs, "value")
    wave_x1.observe(_update_waveforms, "value")
    wave_x2.observe(_update_waveforms, "value")

    def _update_custom(change=None):
        audio.periodic_coeffs = parse_coeffs(custom_input.value)
        _update_fft()

    custom_input.observe(_update_custom, "value")
    for cb in [cb_x1, cb_x2, cb_product, cb_f_sum, cb_f_diff]:
        cb.observe(_update_enables, "value")

    fft_out = widgets.Output()

    def _update_fft():
        fs = 44100
        N = fs  # 1 second of samples
        t = np.linspace(0, 1, N, endpoint=False)
        fv1 = f1_slider.value
        fv2 = f2_slider.value * f2_mult.value
        w1, w2 = wave_x1.value, wave_x2.value
        coeffs = parse_coeffs(custom_input.value)

        def _gen(wtype):
            if wtype == "custom":
                return lambda t, f: custom_wave(t, f, coeffs)
            return WAVE_FUNCS[wtype]

        gen1 = _gen(w1)
        gen2 = _gen(w2)

        signals = {}
        enables = {
            "x1": cb_x1.value,
            "x2": cb_x2.value,
            "product": cb_product.value,
            "f_sum": cb_f_sum.value,
            "f_diff": cb_f_diff.value,
        }
        colors = {
            "x\u2081": "#6a9ff7",
            "x\u2082": "#f7a16a",
            "x\u2081\u00b7x\u2082": "#c77dff",
            "f\u2081+f\u2082": "#5de8a0",
            "|f\u2081\u2212f\u2082|": "#f76a8a",
        }

        if enables["x1"]:
            signals["x\u2081"] = gen1(t, fv1)
        if enables["x2"]:
            signals["x\u2082"] = gen2(t, fv2)
        if enables["product"]:
            signals["x\u2081\u00b7x\u2082"] = gen1(t, fv1) * gen2(t, fv2)
        if enables["f_sum"]:
            signals["f\u2081+f\u2082"] = np.sin(2 * np.pi * (fv1 + fv2) * t)
        if enables["f_diff"]:
            signals["|f\u2081\u2212f\u2082|"] = np.sin(2 * np.pi * abs(fv1 - fv2) * t)

        freqs = fftfreq(N, 1 / fs)[: N // 2]
        x_max = max(fv1 + fv2, fv1, fv2) * 2.5
        mask = freqs <= x_max

        with fft_out:
            fft_out.clear_output(wait=True)
            fig, ax = plt.subplots(figsize=(10, 3))
            fig.patch.set_facecolor("#1a1a2e")
            ax.set_facecolor("#1a1a2e")

            if signals:
                for label, sig in signals.items():
                    magnitudes = 2.0 / N * np.abs(fft(sig)[: N // 2])
                    ax.plot(
                        freqs[mask],
                        magnitudes[mask],
                        label=label,
                        color=colors.get(label, None),
                        linewidth=1.2,
                        alpha=0.9,
                    )
                ax.legend(
                    fontsize=9,
                    facecolor="#2d2d4a",
                    edgecolor="#4a4a6a",
                    labelcolor="#e0e0e0",
                    loc="upper right",
                )
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Enable a signal to see its spectrum",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color="#666",
                    fontsize=12,
                )

            ax.set_xlabel("Frequency [Hz]", color="#aaa", fontsize=10)
            ax.set_ylabel("Magnitude", color="#aaa", fontsize=10)
            ax.set_title("Fourier Transform", color="#ddd", fontsize=11, pad=6)
            ax.tick_params(colors="#888", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#3a3a5a")
            ax.set_xlim(0, x_max)
            ax.grid(True, color="#2a2a4a", linewidth=0.5)
            plt.tight_layout()
            plt.show()
            plt.close(fig)

    # Initialise traitlets so js has the full state from the start
    audio.enables = {
        "x1": cb_x1.value,
        "x2": cb_x2.value,
        "product": cb_product.value,
        "f_sum": cb_f_sum.value,
        "f_diff": cb_f_diff.value,
    }
    audio.waveforms = {
        "x1": wave_x1.value,
        "x2": wave_x2.value,
        "product": "sine",
        "f_sum": "sine",
        "f_diff": "sine",
    }
    _update_fft()

    sliders = widgets.VBox(
        [
            section("Frequencies"),
            f1_slider,
            f2_slider,
            f2_mult,
            section("Waveform shape"),
            widgets.HBox([wave_x1, wave_x2]),
            custom_input,
            section("Volume"),
            vol_slider,
            section("Derived frequencies"),
            freq_info,
        ]
    )

    toggles = widgets.VBox(
        [
            section("Input signals"),
            cb_x1,
            cb_x2,
            section("Multiplication"),
            cb_product,
            section("Product components  \u00bd[cos(\u0394f) \u2212 cos(\u03a3f)]"),
            cb_f_sum,
            cb_f_diff,
        ]
    )

    return widgets.VBox(
        [
            widgets.HBox([sliders, toggles]),
            audio,
            fft_out,
        ]
    )
