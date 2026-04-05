import pathlib
import anywidget
import traitlets


class DrawWidget(anywidget.AnyWidget):
    """
    Canvas widget for drawing a single-period waveshape.

    Traitlets
    ---------
    samples : list[float]
        Evenly-spaced Y values in [-1, 1] representing one period.
        Length is fixed at 256.
    """

    _esm = pathlib.Path(__file__).parent / "draw_canvas.js"
    _css = pathlib.Path(__file__).parent / "draw_canvas.css"

    samples = traitlets.List(trait=traitlets.Float()).tag(sync=True)

    def __init__(self, **kwargs):
        if "samples" not in kwargs:
            kwargs["samples"] = [0.0] * 256
        super().__init__(**kwargs)
