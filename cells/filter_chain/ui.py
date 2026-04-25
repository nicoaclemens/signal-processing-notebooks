# used by: cells\epicycles.py, cells\filter_chain\plotting.py, cells\play_audio_custom_wave.py, cells\play_audio_multiplication.py, cells\synthesizer.py
import ipywidgets as widgets
import numpy as np

from widget import AudioWidget, DrawWidget, KnobWidget
from utils.audio_files import build_audio_player_html, load_wav_from_upload
from utils.signals import samples_to_fourier_coeffs
from utils.ui import plot_waveform_and_fft, section

from .constants import (
    ARROW_HTML,
    BLOCK_HEADER_STYLE_LG,
    BLOCK_HEADER_STYLE_SM,
    BLOCK_LAYOUT,
    COLORS,
    DD_LAYOUT,
    FILTER_TYPES,
    FOURIER_MODES,
    SLIDER_LAYOUT,
    SOURCE_OPTIONS,
)
from .helpers import N_PERIOD, _block_formula_latex, _taper_knob
from .plotting import _plot_filter_response, _plot_uploaded_signal_and_fft
from .processing import _apply_filter_chain, _generate_source


def create_filter_ui(f_init=440):

    source_shape = widgets.Dropdown(
        options=SOURCE_OPTIONS,
        value="sine",
        layout=DD_LAYOUT,
        style={"description_width": "0px"},
    )
    freq_slider = widgets.FloatSlider(
        value=f_init,
        min=20,
        max=2000,
        step=1,
        description="Frequency",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "72px"},
        readout_format=".0f",
    )
    harmonics_input = widgets.Text(
        value="1,0.5,0.33,0.25",
        description="Harmonics",
        placeholder="e.g. 1,0.5,0.33",
        layout=widgets.Layout(width="340px", display="none"),
        style={"description_width": "64px"},
    )
    draw = DrawWidget()
    draw_box = widgets.VBox([draw], layout=widgets.Layout(display="none"))
    upload_input = widgets.FileUpload(
        accept=".wav,audio/wav",
        multiple=False,
        description="Upload WAV",
        layout=widgets.Layout(width="340px", display="none"),
    )
    upload_info = widgets.HTML(
        value=(
            f'<span style="color:{COLORS.text_muted};font-size:12px;">'
            "Upload a .wav file to use it as the source signal."
            "</span>"
        ),
        layout=widgets.Layout(display="none"),
    )
    upload_state = {"samples": None, "sample_rate": None, "name": None}

    def _on_source_shape(change=None):
        harmonics_input.layout.display = (
            "" if source_shape.value == "custom" else "none"
        )
        draw_box.layout.display = "" if source_shape.value == "drawn" else "none"
        show_upload = source_shape.value == "upload"
        upload_input.layout.display = "" if show_upload else "none"
        upload_info.layout.display = "" if show_upload else "none"
        _rebuild()

    def _on_upload(change=None):
        try:
            uploaded = load_wav_from_upload(upload_input.value)
            if uploaded is None:
                upload_state["samples"] = None
                upload_state["sample_rate"] = None
                upload_state["name"] = None
                upload_info.value = (
                    f'<span style="color:{COLORS.text_muted};font-size:12px;">'
                    "Upload a .wav file to use it as the source signal."
                    "</span>"
                )
            else:
                upload_state["samples"] = uploaded["samples"]
                upload_state["sample_rate"] = uploaded["sample_rate"]
                upload_state["name"] = uploaded["name"]
                upload_info.value = (
                    f'<span style="color:{COLORS.text};font-size:12px;">'
                    f'Loaded <b>{uploaded["name"]}</b> '
                    f'({uploaded["sample_rate"]} Hz, {uploaded["duration_s"]:.2f} s)'
                    "</span>"
                )
        except Exception as exc:
            upload_state["samples"] = None
            upload_state["sample_rate"] = None
            upload_state["name"] = None
            upload_info.value = (
                f'<span style="color:{COLORS.red};font-size:12px;">'
                f"Could not read WAV file: {exc}"
                "</span>"
            )

        _rebuild()

    source_shape.observe(_on_source_shape, "value")
    upload_input.observe(_on_upload, "value")

    source_header = widgets.HBox(
        [
            widgets.HTML(f'<b style="{BLOCK_HEADER_STYLE_LG}">Audio Source</b>'),
            widgets.Box(layout=widgets.Layout(flex="1 1 auto")),
            source_shape,
        ]
    )

    source_block = widgets.VBox(
        [
            source_header,
            section("Frequency"),
            freq_slider,
            harmonics_input,
            draw_box,
            upload_input,
            upload_info,
        ],
        layout=BLOCK_LAYOUT,
    )

    filter_blocks = []
    filter_container = widgets.VBox()

    def _make_filter_block():
        filter_type = widgets.Dropdown(
            options=FILTER_TYPES,
            value="fourier",
            layout=DD_LAYOUT,
            style={"description_width": "0px"},
        )
        enable_toggle = widgets.ToggleButton(
            value=True,
            description="On",
            tooltip="Enable/disable this filter",
            layout=widgets.Layout(width="52px", height="28px"),
            button_style="success",
        )
        remove_btn = widgets.Button(
            description="✕",
            layout=widgets.Layout(width="32px", height="28px"),
            button_style="danger",
        )

        fourier_mode = widgets.Dropdown(
            options=FOURIER_MODES,
            value="poly",
            description="Mode",
            layout=DD_LAYOUT,
            style={"description_width": "40px"},
        )
        fourier_var = widgets.Dropdown(
            options=[("Var: k", "k"), ("Var: f (Hz)", "f")],
            value="k",
            description="",
            layout=widgets.Layout(width="110px"),
            style={"description_width": "0px"},
        )
        p_input = widgets.Text(
            value="0, 1",
            description="P(k)",
            layout=widgets.Layout(width="300px"),
            style={"description_width": "36px"},
        )
        q_input = widgets.Text(
            value="1",
            description="Q(k)",
            layout=widgets.Layout(width="300px"),
            style={"description_width": "36px"},
        )
        func_input = widgets.Text(
            value="rect(k/10)",
            description="H(k)",
            layout=widgets.Layout(width="300px", display="none"),
            style={"description_width": "36px"},
        )
        knob = KnobWidget(
            value=0.5,
            default_value=0.5,
            min=0,
            max=1,
            step=0.01,
            label="Knob",
            readout_format=".2f",
            color=COLORS.blue,
            size=56,
        )
        knob_taper = widgets.ToggleButtons(
            options=[("A", "A"), ("B", "B"), ("C", "C")],
            value="B",
            description="Taper",
            style={"description_width": "44px"},
            layout=widgets.Layout(width="180px"),
            tooltips=["A: log", "B: linear", "C: anti-log"],
        )
        knob_hint = widgets.HTML(
            value=(
                f'<span style="color:{COLORS.text_muted};font-size:11px;">'
                "Use {knob} in formulas"
                "</span>"
            )
        )

        fourier_controls = widgets.VBox(
            [widgets.HBox([fourier_mode, fourier_var]), p_input, q_input, func_input]
        )

        kernel_input = widgets.Text(
            value="exp(-((t-0.5)*10)**2)",
            description="h(t)",
            layout=widgets.Layout(width="340px"),
            style={"description_width": "36px"},
        )
        conv_controls = widgets.VBox(
            [kernel_input], layout=widgets.Layout(display="none")
        )

        transform_input = widgets.Text(
            value="s * 2 - 1",
            description="g(s,t)",
            layout=widgets.Layout(width="340px"),
            style={"description_width": "48px"},
        )
        transform_controls = widgets.VBox(
            [transform_input], layout=widgets.Layout(display="none")
        )

        formula_html = widgets.HTMLMath(
            value="",
            layout=widgets.Layout(padding="4px 8px"),
        )
        preview_out = widgets.Output(layout=widgets.Layout(width="100%"))

        def _on_filter_type(change=None):
            ft = filter_type.value
            fourier_controls.layout.display = "" if ft == "fourier" else "none"
            conv_controls.layout.display = "" if ft == "convolution" else "none"
            transform_controls.layout.display = "" if ft == "transform" else "none"
            _rebuild()

        def _on_enable(change=None):
            is_on = enable_toggle.value
            enable_toggle.description = "On" if is_on else "Off"
            enable_toggle.button_style = "success" if is_on else "warning"
            _rebuild()

        def _on_fourier_mode(change=None):
            is_poly = fourier_mode.value == "poly"
            p_input.layout.display = "" if is_poly else "none"
            q_input.layout.display = "" if is_poly else "none"
            func_input.layout.display = "none" if is_poly else ""
            _rebuild()

        filter_type.observe(_on_filter_type, "value")
        enable_toggle.observe(_on_enable, "value")
        fourier_mode.observe(_on_fourier_mode, "value")
        for w in [
            p_input,
            q_input,
            func_input,
            kernel_input,
            transform_input,
            fourier_var,
            knob,
            knob_taper,
        ]:
            w.observe(lambda c: _rebuild(), "value")

        header = widgets.HBox(
            [
                widgets.HTML(f'<b style="{BLOCK_HEADER_STYLE_SM}">Filter</b>'),
                widgets.Box(layout=widgets.Layout(flex="1 1 auto")),
                enable_toggle,
                filter_type,
                remove_btn,
            ]
        )

        block_vbox = widgets.VBox(
            [
                header,
                fourier_controls,
                conv_controls,
                transform_controls,
                widgets.HBox([knob, widgets.VBox([knob_taper, knob_hint])]),
                formula_html,
                preview_out,
            ],
            layout=BLOCK_LAYOUT,
        )

        block = {
            "vbox": block_vbox,
            "filter_type": filter_type,
            "enable_toggle": enable_toggle,
            "fourier_mode": fourier_mode,
            "fourier_var": fourier_var,
            "p_input": p_input,
            "q_input": q_input,
            "func_input": func_input,
            "kernel_input": kernel_input,
            "transform_input": transform_input,
            "knob": knob,
            "knob_taper": knob_taper,
            "remove_btn": remove_btn,
            "formula_html": formula_html,
            "preview_out": preview_out,
        }

        def _remove(btn, b=block):
            filter_blocks.remove(b)
            _update_filter_container()
            _rebuild()

        remove_btn.on_click(_remove)
        return block

    def _update_filter_container():
        filter_container.children = tuple(b["vbox"] for b in filter_blocks)

    def _add_filter(btn=None):
        filter_blocks.append(_make_filter_block())
        _update_filter_container()
        _rebuild()

    add_filter_btn = widgets.Button(
        description="+ Add Filter",
        button_style="info",
        layout=widgets.Layout(width="120px", margin="4px 0"),
    )
    add_filter_btn.on_click(_add_filter)

    audio = AudioWidget(
        components=[
            {
                "id": "main",
                "label": "filtered",
                "oscs": [{"freq": f_init, "gain": 1.0}],
                "enabled": True,
            },
        ],
    )
    audio.waveforms = {"main": "custom"}

    vol_slider = widgets.FloatSlider(
        value=0.5,
        min=0.0,
        max=1.0,
        step=0.05,
        description="Volume",
        continuous_update=True,
        layout=SLIDER_LAYOUT,
        style={"description_width": "50px"},
    )
    widgets.jslink((vol_slider, "value"), (audio, "volume"))

    fft_out = widgets.Output()
    uploaded_audio_out = widgets.HTML(layout=widgets.Layout(display="none"))
    upload_loop = widgets.Checkbox(
        value=False,
        description="Loop",
        indent=False,
        layout=widgets.Layout(display="none"),
    )

    def _block_config(b, base_freq):
        ft = b["filter_type"].value
        taper = b["knob_taper"].value
        cfg = {
            "type": ft,
            "enabled": b["enable_toggle"].value,
            "knob_value": b["knob"].value,
            "knob_taper": taper,
            "knob_effective": _taper_knob(b["knob"].value, taper),
            "base_freq": float(base_freq),
        }
        if ft == "fourier":
            cfg["mode"] = b["fourier_mode"].value
            cfg["fourier_var"] = b["fourier_var"].value
            cfg["p_text"] = b["p_input"].value
            cfg["q_text"] = b["q_input"].value
            cfg["func_text"] = b["func_input"].value
        elif ft == "convolution":
            cfg["kernel_text"] = b["kernel_input"].value
        elif ft == "transform":
            cfg["expr_text"] = b["transform_input"].value
        return cfg

    def _rebuild(change=None):
        is_upload = source_shape.value == "upload"

        if is_upload and upload_state["samples"] is not None:
            source = np.asarray(upload_state["samples"], dtype=float)
            sr = int(upload_state["sample_rate"] or 44100)
            freq = max(sr / max(len(source), 1), 1.0)
        else:
            source = _generate_source(
                source_shape.value,
                harmonics_input.value,
                draw.samples,
                upload_state["samples"],
            )
            sr = 44100
            freq = freq_slider.value

        block_cfgs = []
        for b in filter_blocks:
            cfg = _block_config(b, freq)
            block_cfgs.append(cfg)
            b["formula_html"].value = _block_formula_latex(b)
            _plot_filter_response(b["preview_out"], cfg, freq)

        filtered = _apply_filter_chain(source, block_cfgs)

        if is_upload and upload_state["samples"] is not None:
            playback_signal = np.clip(filtered * float(vol_slider.value), -1.0, 1.0)
            uploaded_audio_out.value = build_audio_player_html(
                playback_signal, sr, loop=upload_loop.value, autoplay=True
            )
            audio.layout.display = "none"
            uploaded_audio_out.layout.display = ""
            upload_loop.layout.display = ""
            _plot_uploaded_signal_and_fft(fft_out, filtered, sr, label="filtered")
        else:
            uploaded_audio_out.value = ""
            uploaded_audio_out.layout.display = "none"
            upload_loop.layout.display = "none"
            audio.layout.display = ""

            real_c, imag_c = samples_to_fourier_coeffs(filtered)
            audio.periodic_real_coeffs = real_c
            audio.periodic_coeffs = imag_c
            audio.frequencies = {"main": [freq]}
            audio.waveforms = {"main": "custom"}

            plot_waveform_and_fft(fft_out, filtered, freq, label="filtered")

    freq_slider.observe(_rebuild, "value")
    harmonics_input.observe(_rebuild, "value")
    draw.observe(_rebuild, "samples")
    upload_loop.observe(_rebuild, "value")

    def _on_volume(change=None):
        if source_shape.value == "upload" and upload_state["samples"] is not None:
            _rebuild()

    vol_slider.observe(_on_volume, "value")

    _rebuild()

    output_block = widgets.VBox(
        [
            widgets.HTML(f'<b style="{BLOCK_HEADER_STYLE_LG}">Audio Output</b>'),
            section("Volume"),
            vol_slider,
            audio,
            upload_loop,
            uploaded_audio_out,
            fft_out,
        ],
        layout=BLOCK_LAYOUT,
    )

    return widgets.VBox(
        [
            source_block,
            widgets.HTML(ARROW_HTML),
            filter_container,
            add_filter_btn,
            widgets.HTML(ARROW_HTML),
            output_block,
        ]
    )


__all__ = ["N_PERIOD", "create_filter_ui"]
