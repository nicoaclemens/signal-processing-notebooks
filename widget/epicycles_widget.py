# used by: cells\epicycles.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class EpicyclesWidget(anywidget.AnyWidget):

    _esm = _DIR / "epicycles.js"
    _css = _THEME + (_DIR / "epicycles.css").read_text()

    coeff_freqs = traitlets.List(trait=traitlets.Int()).tag(sync=True)
    coeff_reals = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    coeff_imags = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    n_components = traitlets.Int(10).tag(sync=True)
    speed = traitlets.Float(1.0).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
