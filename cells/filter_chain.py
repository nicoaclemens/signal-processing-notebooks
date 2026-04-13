# used by:
import re

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

from widget import AudioWidget, DrawWidget, KnobWidget
from utils.signals import (
    WAVE_FUNCS,
    parse_coeffs,
    custom_wave,
    samples_to_fourier_coeffs,
)
from utils.audio_files import (
    load_wav_from_upload,
    resample_for_periodic_source,
    build_audio_player_html,
)
from utils.filters import (
    apply_fourier_filter,
    poly_ratio_H,
    apply_convolution,
    apply_transform,
    eval_kernel,
    eval_H_expr,
)
from utils.ui import (
    section,
    dark_ax,
    plot_waveform_and_fft,
)
from utils.STYLES import (
    COLORS,
    FFT_PLOT_COLORS,
    PLOT,
    SLIDER_LAYOUT,
    DD_LAYOUT,
    BLOCK_BORDER,
    BLOCK_LAYOUT,
    ARROW_HTML,
    FORMULA_STYLE,
    BLOCK_HEADER_STYLE_LG,
    BLOCK_HEADER_STYLE_SM,
)

from utils.texrender import expr_to_latex, poly_to_latex, parse_poly

_SOURCE_OPTIONS = [
    ("Sine", "sine"),
    ("Sawtooth", "sawtooth"),
    ("Square", "square"),
    ("Triangle", "triangle"),
    ("Custom Series", "custom"),
    ("Drawn", "drawn"),
    ("Uploaded WAV", "upload"),
]

_FILTER_TYPES = [
    ("Fourier-Domain Filter", "fourier"),
    ("Convolution", "convolution"),
    ("Transform", "transform"),
]

_FOURIER_MODES = [
    ("Polynomial P(k)/Q(k)", "poly"),
    ("Function H(k)", "func"),
]

N_PERIOD = 512


def _taper_knob(knob_value, taper):
    x = float(np.clip(knob_value, 0.0, 1.0))
    if taper == "A":
        return x**2
    if taper == "C":
        return np.sqrt(x)
    return x


def _with_knob(text, knob_value):
    s = str(text)
    s = re.sub(r"(?<=[0-9A-Za-z_)\]])\s*\{knob\}", "*{knob}", s)
    s = re.sub(r"\{knob\}\s*(?=[0-9A-Za-z_(])", "{knob}*", s)
    return s.replace("{knob}", f"({float(knob_value):.6g})")


def _parse_poly_coeffs(text, knob_value):
    expanded = _with_knob(text, knob_value)
    parts = [p.strip() for p in expanded.split(",") if p.strip()]
    if not parts:
        return [1.0]

    ns = {
        "np": np,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "abs": np.abs,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "sign": np.sign,
    }

    coeffs = []
    for part in parts:
        value = eval(part, {"__builtins__": {}}, ns)
        coeffs.append(float(np.asarray(value).reshape(-1)[0]))
    return coeffs


def _eval_fourier_func(expr, x):
    ns = {
        "k": x.astype(float),
        "f": x.astype(float),
        "np": np,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "abs": np.abs,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "sign": np.sign,
        "rect": lambda y: (np.abs(y) <= 0.5).astype(float),
    }
    return eval(expr, {"__builtins__": {}}, ns)


def _eval_fourier_H(cfg, k, freq):
    var = cfg.get("fourier_var", "k")
    x = k.astype(float) if var == "k" else (k.astype(float) * float(freq))

    if cfg["mode"] == "poly":
        p = _parse_poly_coeffs(cfg["p_text"], cfg["knob_effective"])
        q = _parse_poly_coeffs(cfg["q_text"], cfg["knob_effective"])
        return np.asarray(poly_ratio_H(p, q)(x), dtype=complex)

    expr = _with_knob(cfg["func_text"], cfg["knob_effective"])
    return np.asarray(_eval_fourier_func(expr, x), dtype=complex)


def _block_formula_latex(block):
    ft = block["filter_type"].value
    knob_value = _taper_knob(block["knob"].value, block["knob_taper"].value)

    if ft == "fourier":
        var = block["fourier_var"].value
        var_tex = "k" if var == "k" else "f"
        if block["fourier_mode"].value == "poly":
            try:
                p_coeffs = _parse_poly_coeffs(block["p_input"].value, knob_value)
                q_coeffs = _parse_poly_coeffs(block["q_input"].value, knob_value)
                p = poly_to_latex(", ".join(f"{c:.6g}" for c in p_coeffs), var=var_tex)
                q = poly_to_latex(", ".join(f"{c:.6g}" for c in q_coeffs), var=var_tex)
            except Exception:
                p = expr_to_latex(_with_knob(block["p_input"].value, knob_value))
                q = expr_to_latex(_with_knob(block["q_input"].value, knob_value))
            return (
                f'<div style="{FORMULA_STYLE}">'
                f"$$H({var_tex}) = \\frac{{{p}}}{{{q}}}$$"
                "</div>"
            )
        expr = expr_to_latex(_with_knob(block["func_input"].value, knob_value))
        return f'<div style="{FORMULA_STYLE}">' f"$$H({var_tex}) = {expr}$$" "</div>"
    if ft == "convolution":
        expr = expr_to_latex(_with_knob(block["kernel_input"].value, knob_value))
        return f'<div style="{FORMULA_STYLE}">' f"$$h(t) = {expr}$$" "</div>"
    if ft == "transform":
        expr = expr_to_latex(_with_knob(block["transform_input"].value, knob_value))
        return f'<div style="{FORMULA_STYLE}">' f"$$g(s, t) = {expr}$$" "</div>"
    return ""


def _plot_filter_response(output_widget, cfg, freq):
    c = FFT_PLOT_COLORS
    ft = cfg["type"]
    if not cfg.get("enabled", True):
        with output_widget:
            output_widget.clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
            fig.patch.set_facecolor(c["bg"])
            dark_ax(ax1)
            dark_ax(ax2)
            for ax in (ax1, ax2):
                ax.text(
                    0.5,
                    0.5,
                    "Bypassed",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=COLORS.text_muted,
                    fontsize=PLOT.empty_fontsize,
                )
            plt.tight_layout()
            plt.show()
            plt.close(fig)
        return

    period_s = 1.0 / freq

    def _freq_xlim(mag):
        peak = np.max(np.abs(mag))
        if peak == 0:
            return len(mag) - 1
        thresh = peak * 0.01
        nonzero = np.where(np.abs(mag) > thresh)[0]
        last = int(nonzero[-1]) if len(nonzero) else 0
        return max(last * 1.3, 1)

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        try:
            if ft == "fourier":
                k = np.arange(N_PERIOD // 2 + 1)
                H = _eval_fourier_H(cfg, k, freq)
                mag = np.abs(H)
                h = np.fft.irfft(H, n=N_PERIOD)
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, h, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Impulse Response  h(t)",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Amplitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )

            elif ft == "convolution":
                kernel = eval_kernel(
                    _with_knob(cfg["kernel_text"], cfg["knob_effective"]), N_PERIOD
                )
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, kernel, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Kernel  h(t)",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Amplitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
                K = np.fft.rfft(kernel)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )

            elif ft == "transform":
                s_in = np.linspace(-1, 1, N_PERIOD)
                expr = _with_knob(cfg["expr_text"], cfg["knob_effective"])
                s_out = apply_transform(s_in, expr)
                ax1.plot(s_in, s_out, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax1.set_title(
                    "Transfer Curve",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax1.set_xlabel(
                    "Input  s", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax1.set_ylabel(
                    "Output  g(s)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                delta = np.zeros(N_PERIOD)
                delta[0] = 1.0
                imp = apply_transform(delta, expr)
                K = np.fft.rfft(imp)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color=PLOT.line_color, linewidth=PLOT.line_width)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Spectrum of Impulse Output",
                    color=c["title"],
                    fontsize=PLOT.title_fontsize,
                    pad=PLOT.title_pad,
                )
                ax2.set_xlabel(
                    "Frequency (Hz)", color=c["label"], fontsize=PLOT.label_fontsize
                )
                ax2.set_ylabel(
                    "Magnitude", color=c["label"], fontsize=PLOT.label_fontsize
                )
        except Exception:
            for ax in (ax1, ax2):
                ax.text(
                    0.5,
                    0.5,
                    "Error",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=COLORS.text_muted,
                    fontsize=PLOT.empty_fontsize,
                )

        plt.tight_layout()
        plt.show()
        plt.close(fig)


def _generate_source(shape, coeffs_text, drawn_samples, uploaded_samples):
    t = np.linspace(0, 1, N_PERIOD, endpoint=False)
    if shape == "drawn":
        if drawn_samples and any(s != 0 for s in drawn_samples):
            src = np.array(drawn_samples)
            indices = np.linspace(0, len(src) - 1, N_PERIOD)
            return np.interp(indices, np.arange(len(src)), src)
        return np.zeros(N_PERIOD)
    elif shape == "upload":
        if uploaded_samples is None or len(uploaded_samples) == 0:
            return np.zeros(N_PERIOD)
        return resample_for_periodic_source(uploaded_samples, N_PERIOD)
    elif shape == "custom":
        return custom_wave(t, 1.0, parse_coeffs(coeffs_text))
    else:
        return WAVE_FUNCS[shape](t, 1.0)


def _plot_uploaded_signal_and_fft(output_widget, signal, sample_rate, label="filtered"):
    c = FFT_PLOT_COLORS

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=PLOT.figsize_wide)
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        n = len(signal)
        if n == 0:
            ax1.text(
                0.5,
                0.5,
                "No signal",
                ha="center",
                va="center",
                transform=ax1.transAxes,
                color=COLORS.text_muted,
                fontsize=PLOT.empty_fontsize,
            )
            ax2.text(
                0.5,
                0.5,
                "No spectrum",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                color=COLORS.text_muted,
                fontsize=PLOT.empty_fontsize,
            )
        else:
            preview_samples = min(n, max(int(sample_rate * 0.08), 256))
            t_ms = np.arange(preview_samples) / sample_rate * 1000.0
            ax1.plot(
                t_ms,
                signal[:preview_samples],
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
            )
            ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=PLOT.label_fontsize)
            ax1.set_ylabel("Amplitude", color=c["label"], fontsize=PLOT.label_fontsize)
            ax1.set_title(
                "Waveform Preview",
                color=c["title"],
                fontsize=PLOT.title_fontsize,
                pad=PLOT.title_pad,
            )

            win_len = min(n, sample_rate)
            windowed = signal[:win_len]
            spectrum = np.fft.rfft(windowed)
            mags = np.abs(spectrum)
            freqs = np.fft.rfftfreq(win_len, d=1.0 / sample_rate)
            x_max = min(sample_rate / 2, 5000)
            mask = freqs <= x_max

            ax2.plot(
                freqs[mask],
                mags[mask],
                color=PLOT.line_color,
                linewidth=PLOT.line_width,
                alpha=PLOT.line_alpha,
                label=label,
            )
            ax2.set_xlabel(
                "Frequency [Hz]", color=c["label"], fontsize=PLOT.label_fontsize
            )
            ax2.set_ylabel("Magnitude", color=c["label"], fontsize=PLOT.label_fontsize)
            ax2.set_title(
                "Fourier Transform",
                color=c["title"],
                fontsize=PLOT.title_fontsize,
                pad=PLOT.title_pad,
            )
            ax2.set_xlim(0, x_max)
            ax2.legend(
                fontsize=PLOT.legend_fontsize,
                facecolor=c["legend"],
                edgecolor=c["ledge"],
                labelcolor=c["ltxt"],
                loc="upper right",
            )

        plt.tight_layout()
        plt.show()
        plt.close(fig)


def _apply_single_filter(signal, cfg):
    if not cfg.get("enabled", True):
        return signal

    ft = cfg["type"]
    if ft == "fourier":
        return apply_fourier_filter(
            signal,
            lambda k, c=cfg: _eval_fourier_H(c, k, c.get("base_freq", 1.0)),
        )
    elif ft == "convolution":
        kernel = eval_kernel(
            _with_knob(cfg["kernel_text"], cfg["knob_effective"]), len(signal)
        )
        return apply_convolution(signal, kernel)
    elif ft == "transform":
        return apply_transform(
            signal, _with_knob(cfg["expr_text"], cfg["knob_effective"])
        )
    return signal


def _apply_filter_chain(signal, filter_configs):
    s = signal.copy()
    for cfg in filter_configs:
        try:
            s = _apply_single_filter(s, cfg)
        except Exception:
            pass
    mx = np.max(np.abs(s))
    if mx > 0:
        s = s / mx
    return s


def create_filter_ui(f_init=440):

    # source
    source_shape = widgets.Dropdown(
        options=_SOURCE_OPTIONS,
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

    # filters

    filter_blocks = []
    filter_container = widgets.VBox()

    def _make_filter_block():
        filter_type = widgets.Dropdown(
            options=_FILTER_TYPES,
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
            options=_FOURIER_MODES,
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

        # transform controls
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
        preview_out = widgets.Output(
            layout=widgets.Layout(width="100%"),
        )

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
        children = []
        for b in filter_blocks:
            children.append(b["vbox"])
        filter_container.children = tuple(children)

    # btn oncliock cb
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

    # outp

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

    # pipline

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

    # rebuild on changes
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

    # observers
    freq_slider.observe(_rebuild, "value")
    harmonics_input.observe(_rebuild, "value")
    draw.observe(_rebuild, "samples")
    upload_loop.observe(_rebuild, "value")

    def _on_volume(change=None):
        if source_shape.value == "upload" and upload_state["samples"] is not None:
            _rebuild()

    vol_slider.observe(_on_volume, "value")

    _rebuild()

    # layout

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
