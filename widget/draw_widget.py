# used by: cells\filter_chain.py, cells\play_audio_custom_wave.py
import pathlib
import anywidget
import traitlets


class DrawWidget(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "draw_canvas.js"
    _css = pathlib.Path(__file__).parent / "draw_canvas.css"

    samples = traitlets.List(trait=traitlets.Float()).tag(sync=True)

    def __init__(self, **kwargs):
        if "samples" not in kwargs:
            kwargs["samples"] = [0.0] * 256
        super().__init__(**kwargs)
