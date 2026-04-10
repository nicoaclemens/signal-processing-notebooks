# used by: cells\synthesizer.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()

# temp
_CSS = """
.midi-container {
    display: flex;
    align-items: center;
    gap: 8px;
}

.midi-select {
    font-family: var(--w-font);
    font-size: 11px;
    color: var(--w-text);
    background: var(--w-surface);
    border: 1px solid var(--w-surface-light);
    border-radius: 4px;
    padding: 3px 6px;
    outline: none;
    cursor: pointer;
}

.midi-select:hover {
    border-color: var(--w-surface-lighter);
}

.midi-status {
    font-family: var(--w-font);
    font-size: 11px;
    color: var(--w-text-dim);
}
"""


class MidiInputWidget(anywidget.AnyWidget):

    _esm = _DIR / "midi_input.js"
    _css = _THEME + _CSS

    note = traitlets.Int(0).tag(sync=True)
    velocity = traitlets.Int(0).tag(sync=True)
    frequency = traitlets.Float(0.0).tag(sync=True)
    gate = traitlets.Bool(False).tag(sync=True)
    connected = traitlets.Bool(False).tag(sync=True)
    device_name = traitlets.Unicode("").tag(sync=True)
