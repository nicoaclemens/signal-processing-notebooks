# used by:
import ipywidgets as widgets
import numpy as np
import matplotlib.pyplot as plt
from widget import DrawGridWidget, EpicyclesWidget
from utils.fourier import extract_contour, compute_dft, reconstruct_path
from utils.ui import section, dark_ax, SLIDER_LAYOUT, FFT_PLOT_COLORS


def create_epicycles_ui(grid_size=64):

    draw = DrawGridWidget(grid_size=grid_size)
    epicycles = EpicyclesWidget()

    n_slider = widgets.IntSlider(
        value=10,
        min=1,
        max=200,
        step=1,
        description="Components",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "80px"},
    )
    speed_slider = widgets.FloatSlider(
        value=1.0,
        min=0.1,
        max=5.0,
        step=0.1,
        description="Speed",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "80px"},
    )

    widgets.jslink((n_slider, "value"), (epicycles, "n_components"))
    widgets.jslink((speed_slider, "value"), (epicycles, "speed"))

    plot_out = widgets.Output()

    _state = {"freqs": None, "coeffs": None, "contour": None}

    def _push_coeffs(contour):
        if contour is None:
            epicycles.coeff_freqs = []
            epicycles.coeff_reals = []
            epicycles.coeff_imags = []
            _state["freqs"] = _state["coeffs"] = _state["contour"] = None
            n_slider.max = 200
            return

        freqs, coeffs = compute_dft(contour)
        epicycles.coeff_freqs = freqs.tolist()
        epicycles.coeff_reals = coeffs.real.tolist()
        epicycles.coeff_imags = coeffs.imag.tolist()
        _state["freqs"] = freqs
        _state["coeffs"] = coeffs
        _state["contour"] = contour
        n_slider.max = len(freqs)

    def _on_pixels(change=None):
        px = draw.pixels
        grid = np.array(px).reshape(grid_size, grid_size)
        contour = extract_contour(grid)
        _push_coeffs(contour)
        _update_plot()

    def _on_n(change=None):
        _update_plot()

    def _update_plot():
        c = FFT_PLOT_COLORS
        freqs = _state["freqs"]
        coeffs = _state["coeffs"]
        contour = _state["contour"]

        with plot_out:
            plot_out.clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            fig.patch.set_facecolor(c["bg"])
            dark_ax(ax1)
            dark_ax(ax2)

            if contour is not None and freqs is not None:
                n = n_slider.value
                recon = reconstruct_path(freqs, coeffs, n)

                ax1.plot(
                    contour.real,
                    contour.imag,
                    ".",
                    color="#4a4a6a",
                    markersize=2,
                    alpha=0.6,
                    label="original",
                )
                ax1.plot(
                    recon.real,
                    recon.imag,
                    color="#7c6ff7",
                    linewidth=1.5,
                    label=f"{n} components",
                )
                ax1.set_aspect("equal")
                ax1.legend(
                    fontsize=9,
                    facecolor=c["legend"],
                    edgecolor=c["ledge"],
                    labelcolor=c["ltxt"],
                    loc="upper right",
                )
                ax1.set_title("Reconstruction", color=c["title"], fontsize=11, pad=6)

                mags = np.abs(coeffs[1:])
                n_show = min(60, len(mags))
                ax2.bar(range(1, n_show + 1), mags[:n_show], color="#7c6ff7", alpha=0.8)
                if n - 1 <= n_show:
                    ax2.axvline(
                        n, color="#ff6b6b", linestyle="--", alpha=0.7, label=f"n = {n}"
                    )
                    ax2.legend(
                        fontsize=9,
                        facecolor=c["legend"],
                        edgecolor=c["ledge"],
                        labelcolor=c["ltxt"],
                    )
                ax2.set_xlabel("Component", color=c["label"], fontsize=10)
                ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)
                ax2.set_title(
                    "Coefficient Spectrum", color=c["title"], fontsize=11, pad=6
                )
            else:
                ax1.text(
                    0.5,
                    0.5,
                    "Draw a shape above",
                    ha="center",
                    va="center",
                    transform=ax1.transAxes,
                    color="#666",
                    fontsize=12,
                )
                ax1.set_title("Reconstruction", color=c["title"], fontsize=11, pad=6)
                ax2.set_title(
                    "Coefficient Spectrum", color=c["title"], fontsize=11, pad=6
                )

            plt.tight_layout()
            plt.show()
            plt.close(fig)

    draw.observe(_on_pixels, "pixels")
    n_slider.observe(_on_n, "value")

    _update_plot()

    controls = widgets.VBox(
        [
            section("Fourier Components"),
            n_slider,
            section("Animation Speed"),
            speed_slider,
        ]
    )

    return widgets.VBox([draw, controls, epicycles, plot_out])
