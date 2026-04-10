# used by: cells\epicycles.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class DrawGridWidget(anywidget.AnyWidget):

    _esm = _DIR / "draw_grid.js"
    _css = _THEME + (_DIR / "draw_grid.css").read_text()

    grid_size = traitlets.Int(64).tag(sync=True)
    pixels = traitlets.List(trait=traitlets.Int()).tag(sync=True)

    def __init__(self, **kwargs):
        gs = kwargs.get("grid_size", 64)
        if "pixels" not in kwargs:
            kwargs["pixels"] = [0] * (gs * gs)
        super().__init__(**kwargs)
