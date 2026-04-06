# used by: cells\epicycles.py
import pathlib
import anywidget
import traitlets


class EpicyclesWidget(anywidget.AnyWidget):

    _esm = pathlib.Path(__file__).parent / "epicycles.js"
    _css = pathlib.Path(__file__).parent / "epicycles.css"

    coeff_freqs = traitlets.List(trait=traitlets.Int()).tag(sync=True)
    coeff_reals = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    coeff_imags = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    n_components = traitlets.Int(10).tag(sync=True)
    speed = traitlets.Float(1.0).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
