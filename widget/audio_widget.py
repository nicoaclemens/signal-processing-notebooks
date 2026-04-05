import pathlib
import anywidget
import traitlets


class AudioWidget(anywidget.AnyWidget):
    """
    browser-side audio synthesiser widget.

     Traitlets
     ---------
     components : list[dict]
         Component structure, set at creation time
           Each:
             {"id": str, "label": str,
              "oscs": [{"freq": float, "gain": float}, ...],
              "enabled": bool}
     frequencies : dict[str, list[float]]
         Live frequency updates keyed by component id
     enables : dict[str, bool]
         Live enable/disable updates keyed by component id
     volume : float
         0.0 - 1.0
     playing : bool
         Read-only reflection of the play/stop state (toggled by the JS
         play button).
    """

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
