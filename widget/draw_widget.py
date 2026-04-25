# used by: cells\filter_chain\ui.py, cells\play_audio_custom_wave.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class DrawWidget(anywidget.AnyWidget):
    _esm = _DIR / "draw_canvas.js"
    _css = _THEME + (_DIR / "draw_canvas.css").read_text()

    samples = traitlets.List(trait=traitlets.Float()).tag(sync=True)

    def __init__(self, **kwargs):
        if "samples" not in kwargs:
            kwargs["samples"] = [0.0] * 256
        super().__init__(**kwargs)
