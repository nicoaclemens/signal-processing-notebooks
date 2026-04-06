# used by: cells\filter_chain.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py
import pathlib
import anywidget
import traitlets


class AudioWidget(anywidget.AnyWidget):

    _esm = pathlib.Path(__file__).parent / "audio_engine.js"
    _css = pathlib.Path(__file__).parent / "audio_widget.css"

    components = traitlets.List(trait=traitlets.Dict()).tag(sync=True)
    frequencies = traitlets.Dict().tag(sync=True)
    enables = traitlets.Dict().tag(sync=True)
    waveforms = traitlets.Dict().tag(sync=True)
    periodic_coeffs = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    periodic_real_coeffs = traitlets.List(trait=traitlets.Float()).tag(sync=True)
    volume = traitlets.Float(0.5).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
