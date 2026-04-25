# used by: cells\filter_chain\ui.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py, cells\synthesizer.py
import pathlib
import anywidget
import traitlets

_DIR = pathlib.Path(__file__).parent
_THEME = (_DIR / "theme.css").read_text()


class AudioWidget(anywidget.AnyWidget):

    _esm = _DIR / "audio_engine.js"
    _css = _THEME + (_DIR / "audio_widget.css").read_text()

    components = traitlets.List(trait=traitlets.Dict()).tag(sync=True)
    frequencies = traitlets.Dict().tag(sync=True)
    enables = traitlets.Dict().tag(sync=True)
    waveforms = traitlets.Dict().tag(sync=True)
    periodic_coeffs = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    periodic_real_coeffs = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    volume = traitlets.Float(0.5).tag(sync=True)
    mono_frequency = traitlets.Float(0.0).tag(sync=True)
    glide_time = traitlets.Float(0.0).tag(sync=True)
    master_tune = traitlets.Float(0.0).tag(sync=True)
    osc_config = traitlets.Dict().tag(sync=True)
    mixer_volumes = traitlets.Dict().tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
