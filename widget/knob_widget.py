# used by: cells\synthesizer.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class KnobWidget(anywidget.AnyWidget):

    _esm = _DIR / "knob.js"
    _css = _THEME + (_DIR / "knob.css").read_text()

    value = traitlets.Float(0.0).tag(sync=True)
    default_value = traitlets.Float(0.0).tag(sync=True)

    min = traitlets.Float(0.0).tag(sync=True)
    max = traitlets.Float(1.0).tag(sync=True)
    step = traitlets.Float(0.01).tag(sync=True)

    options = traitlets.List(trait=traitlets.Unicode()).tag(sync=True)
    mode = traitlets.Unicode("continuous").tag(sync=True)

    label = traitlets.Unicode("").tag(sync=True)
    unit = traitlets.Unicode("").tag(sync=True)
    readout_format = traitlets.Unicode(".1f").tag(sync=True)
    color = traitlets.Unicode("#7c6ff7").tag(sync=True)
    size = traitlets.Int(80).tag(sync=True)

    @property
    def index(self) -> int:
        return int(round(self.value))

    @index.setter
    def index(self, idx: int):
        self.value = float(idx)

    @property
    def selected(self) -> str:
        idx = self.index
        if 0 <= idx < len(self.options):
            return self.options[idx]
        return ""
