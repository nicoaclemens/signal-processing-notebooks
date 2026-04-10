# used by: cells\synthesizer.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class SwitchWidget(anywidget.AnyWidget):

    _esm = _DIR / "switch.js"
    _css = _THEME + (_DIR / "switch.css").read_text()

    value = traitlets.Bool(False).tag(sync=True)
    label = traitlets.Unicode("").tag(sync=True)
    option_labels = traitlets.List(
        trait=traitlets.Unicode(), default_value=["Off", "On"]
    ).tag(sync=True)
    orientation = traitlets.Unicode("vertical").tag(sync=True)
    color = traitlets.Unicode("#f7a16a").tag(sync=True)
