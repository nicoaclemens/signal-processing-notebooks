import pathlib
import anywidget
import traitlets


class EpicyclesWidget(anywidget.AnyWidget):
    """
    Animated Fourier-epicycles visualiser.

    Traitlets
    ---------
    coeff_freqs : list[int]
        Frequency indices for each coefficient.
    coeff_reals : list[float]
        Real parts of the Fourier coefficients.
    coeff_imags : list[float]
        Imaginary parts of the Fourier coefficients.
    n_components : int
        How many coefficients to use for the animation.
    speed : float
        Animation speed multiplier (1.0 = normal).
    playing : bool
        Read-only reflection of play/stop state.
    """

    _esm = pathlib.Path(__file__).parent / "epicycles.js"
    _css = pathlib.Path(__file__).parent / "epicycles.css"

    coeff_freqs = traitlets.List(trait=traitlets.Int()).tag(sync=True)
    coeff_reals = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    coeff_imags = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    n_components = traitlets.Int(10).tag(sync=True)
    speed = traitlets.Float(1.0).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
