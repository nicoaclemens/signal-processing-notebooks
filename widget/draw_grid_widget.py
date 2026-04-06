# used by: cells\epicycles.py
import pathlib
import anywidget
import traitlets


class DrawGridWidget(anywidget.AnyWidget):

    _esm = pathlib.Path(__file__).parent / "draw_grid.js"
    _css = pathlib.Path(__file__).parent / "draw_grid.css"

    grid_size = traitlets.Int(64).tag(sync=True)
    pixels = traitlets.List(trait=traitlets.Int()).tag(sync=True)

    def __init__(self, **kwargs):
        gs = kwargs.get("grid_size", 64)
        if "pixels" not in kwargs:
            kwargs["pixels"] = [0] * (gs * gs)
        super().__init__(**kwargs)
