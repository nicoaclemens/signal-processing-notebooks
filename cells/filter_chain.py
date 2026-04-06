import re

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

from widget import AudioWidget, DrawWidget
from utils.signals import (
    WAVE_FUNCS,
    parse_coeffs,
    custom_wave,
    samples_to_fourier_coeffs,
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
    SLIDER_LAYOUT,
    DD_LAYOUT,
    FFT_PLOT_COLORS,
    dark_ax,
    plot_waveform_and_fft,
)

_SOURCE_OPTIONS = [
    ("Sine", "sine"),
    ("Sawtooth", "sawtooth"),
    ("Square", "square"),
    ("Triangle", "triangle"),
    ("Custom Series", "custom"),
    ("Drawn", "drawn"),
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

_BLOCK_BORDER = "1px solid #3a3a5a"
_BLOCK_STYLE = widgets.Layout(
    border=_BLOCK_BORDER,
    padding="8px",
    margin="4px 0",
)

_ARROW_HTML = '<div style="text-align:center;color:#555;font-size:18px;">↓</div>'


def _parse_poly(text):
    try:
        return [float(x.strip()) for x in text.split(",") if x.strip()]
    except ValueError:
        return [1.0]


def _poly_to_latex(text, var="k"):
    coeffs = _parse_poly(text)
    n = len(coeffs) - 1
    if not coeffs:
        return "0"
    terms = []
    for i, c in enumerate(coeffs):
        deg = n - i
        if c == 0:
            continue
        abs_c = abs(c)
        sign = "-" if c < 0 else "+"
        if deg == 0:
            coeff_str = f"{abs_c:g}"
        elif deg == 1:
            coeff_str = var if abs_c == 1 else f"{abs_c:g}{var}"
        else:
            coeff_str = (
                f"{var}^{{{deg}}}" if abs_c == 1 else f"{abs_c:g}{var}^{{{deg}}}"
            )
        terms.append((sign, coeff_str))
    if not terms:
        return "0"
    parts = []
    for j, (sign, coeff_str) in enumerate(terms):
        if j == 0:
            parts.append(f"-{coeff_str}" if sign == "-" else coeff_str)
        else:
            parts.append(f" {sign} {coeff_str}")
    return "".join(parts)


def _expr_to_latex(expr):
    s = expr.strip()
    s = s.replace("np.", "")
    s = re.sub(r"\*\*(\d+)", r"^{\1}", s)
    s = re.sub(r"\*\*\(([^)]+)\)", r"^{(\1)}", s)
    s = s.replace("*", r" \cdot ")
    s = re.sub(r"\brect\b", r"\\operatorname{rect}", s)
    s = re.sub(r"\bsign\b", r"\\operatorname{sign}", s)
    s = re.sub(r"\bclip\b", r"\\operatorname{clip}", s)
    s = re.sub(r"\babs\b", r"\\operatorname{abs}", s)
    s = re.sub(r"\bexp\b", r"\\exp", s)
    s = re.sub(r"\bsin\b", r"\\sin", s)
    s = re.sub(r"\bcos\b", r"\\cos", s)
    s = re.sub(r"\bsqrt\b", r"\\sqrt", s)
    s = re.sub(r"\blog\b", r"\\ln", s)
    s = re.sub(r"\bpi\b", r"\\pi", s)
    return s


def _block_formula_latex(block):
    ft = block["filter_type"].value
    if ft == "fourier":
        if block["fourier_mode"].value == "poly":
            p = _poly_to_latex(block["p_input"].value)
            q = _poly_to_latex(block["q_input"].value)
            return (
                '<div style="color:#ddd;padding:4px 0;">'
                f"$$H(k) = \\frac{{{p}}}{{{q}}}$$"
                "</div>"
            )
        expr = _expr_to_latex(block["func_input"].value)
        return '<div style="color:#ddd;padding:4px 0;">' f"$$H(k) = {expr}$$" "</div>"
    if ft == "convolution":
        expr = _expr_to_latex(block["kernel_input"].value)
        return '<div style="color:#ddd;padding:4px 0;">' f"$$h(t) = {expr}$$" "</div>"
    if ft == "transform":
        expr = _expr_to_latex(block["transform_input"].value)
        return (
            '<div style="color:#ddd;padding:4px 0;">' f"$$g(s, t) = {expr}$$" "</div>"
        )
    return ""


def _plot_filter_response(output_widget, cfg, freq):
    c = FFT_PLOT_COLORS
    ft = cfg["type"]
    period_s = 1.0 / freq

    def _freq_xlim(mag):
        """Return a sensible upper harmonic index to display."""
        peak = np.max(np.abs(mag))
        if peak == 0:
            return len(mag) - 1
        thresh = peak * 0.01
        nonzero = np.where(np.abs(mag) > thresh)[0]
        last = int(nonzero[-1]) if len(nonzero) else 0
        return max(last * 1.3, 1)

    with output_widget:
        output_widget.clear_output(wait=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3))
        fig.patch.set_facecolor(c["bg"])
        dark_ax(ax1)
        dark_ax(ax2)

        try:
            if ft == "fourier":
                k = np.arange(N_PERIOD // 2 + 1)
                if cfg["mode"] == "poly":
                    p = _parse_poly(cfg["p_text"])
                    q = _parse_poly(cfg["q_text"])
                    H = np.asarray(poly_ratio_H(p, q)(k), dtype=complex)
                else:
                    H = np.asarray(eval_H_expr(cfg["func_text"], k), dtype=complex)
                mag = np.abs(H)
                h = np.fft.irfft(H, n=N_PERIOD)
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, h, color="#7c6ff7", linewidth=1.2)
                ax1.set_title(
                    "Impulse Response  h(t)", color=c["title"], fontsize=11, pad=6,
                )
                ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=10)
                ax1.set_ylabel("Amplitude", color=c["label"], fontsize=10)
                f_hz = k * freq
                ax2.plot(f_hz, mag, color="#7c6ff7", linewidth=1.2)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"], fontsize=11, pad=6,
                )
                ax2.set_xlabel("Frequency (Hz)", color=c["label"], fontsize=10)
                ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)

            elif ft == "convolution":
                kernel = eval_kernel(cfg["kernel_text"], N_PERIOD)
                t_ms = np.linspace(0, period_s * 1000, N_PERIOD, endpoint=False)
                ax1.plot(t_ms, kernel, color="#7c6ff7", linewidth=1.2)
                ax1.set_title(
                    "Kernel  h(t)", color=c["title"], fontsize=11, pad=6,
                )
                ax1.set_xlabel("Time (ms)", color=c["label"], fontsize=10)
                ax1.set_ylabel("Amplitude", color=c["label"], fontsize=10)
                K = np.fft.rfft(kernel)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color="#7c6ff7", linewidth=1.2)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Frequency Response  |H(f)|",
                    color=c["title"], fontsize=11, pad=6,
                )
                ax2.set_xlabel("Frequency (Hz)", color=c["label"], fontsize=10)
                ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)

            elif ft == "transform":
                s_in = np.linspace(-1, 1, N_PERIOD)
                s_out = apply_transform(s_in, cfg["expr_text"])
                ax1.plot(s_in, s_out, color="#7c6ff7", linewidth=1.2)
                ax1.set_title(
                    "Transfer Curve", color=c["title"], fontsize=11, pad=6,
                )
                ax1.set_xlabel("Input  s", color=c["label"], fontsize=10)
                ax1.set_ylabel("Output  g(s)", color=c["label"], fontsize=10)
                delta = np.zeros(N_PERIOD)
                delta[0] = 1.0
                imp = apply_transform(delta, cfg["expr_text"])
                K = np.fft.rfft(imp)
                mag = np.abs(K)
                k = np.arange(len(K))
                f_hz = k * freq
                ax2.plot(f_hz, mag, color="#7c6ff7", linewidth=1.2)
                ax2.set_xlim(0, _freq_xlim(mag) * freq)
                ax2.set_title(
                    "Spectrum of Impulse Output",
                    color=c["title"], fontsize=11, pad=6,
                )
                ax2.set_xlabel("Frequency (Hz)", color=c["label"], fontsize=10)
                ax2.set_ylabel("Magnitude", color=c["label"], fontsize=10)
        except Exception:
            for ax in (ax1, ax2):
                ax.text(
                    0.5, 0.5, "Error", ha="center", va="center",
                    transform=ax.transAxes, color="#666", fontsize=12,
                )

        plt.tight_layout()
        plt.show()
        plt.close(fig)


def _generate_source(shape, coeffs_text, drawn_samples):
    t = np.linspace(0, 1, N_PERIOD, endpoint=False)
    if shape == "drawn":
        if drawn_samples and any(s != 0 for s in drawn_samples):
            src = np.array(drawn_samples)
            indices = np.linspace(0, len(src) - 1, N_PERIOD)
            return np.interp(indices, np.arange(len(src)), src)
        return np.zeros(N_PERIOD)
    elif shape == "custom":
        return custom_wave(t, 1.0, parse_coeffs(coeffs_text))
    else:
        return WAVE_FUNCS[shape](t, 1.0)


def _apply_single_filter(signal, cfg):
    ft = cfg["type"]
    if ft == "fourier":
        if cfg["mode"] == "poly":
            p = _parse_poly(cfg["p_text"])
            q = _parse_poly(cfg["q_text"])
            return apply_fourier_filter(signal, poly_ratio_H(p, q))
        else:
            return apply_fourier_filter(
                signal, lambda k, e=cfg["func_text"]: eval_H_expr(e, k)
            )
    elif ft == "convolution":
        kernel = eval_kernel(cfg["kernel_text"], len(signal))
        return apply_convolution(signal, kernel)
    elif ft == "transform":
        return apply_transform(signal, cfg["expr_text"])
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

    def _on_source_shape(change=None):
        harmonics_input.layout.display = (
            "" if source_shape.value == "custom" else "none"
        )
        draw_box.layout.display = "" if source_shape.value == "drawn" else "none"
        _rebuild()

    source_shape.observe(_on_source_shape, "value")

    source_header = widgets.HBox(
        [
            widgets.HTML('<b style="color:#ddd;font-size:13px;">Audio Source</b>'),
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
        ],
        layout=_BLOCK_STYLE,
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
        fourier_controls = widgets.VBox([fourier_mode, p_input, q_input, func_input])

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

        def _on_fourier_mode(change=None):
            is_poly = fourier_mode.value == "poly"
            p_input.layout.display = "" if is_poly else "none"
            q_input.layout.display = "" if is_poly else "none"
            func_input.layout.display = "none" if is_poly else ""
            _rebuild()

        filter_type.observe(_on_filter_type, "value")
        fourier_mode.observe(_on_fourier_mode, "value")
        for w in [p_input, q_input, func_input, kernel_input, transform_input]:
            w.observe(lambda c: _rebuild(), "value")

        header = widgets.HBox(
            [
                widgets.HTML('<b style="color:#ddd;font-size:12px;">Filter</b>'),
                widgets.Box(layout=widgets.Layout(flex="1 1 auto")),
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
                formula_html,
                preview_out,
            ],
            layout=_BLOCK_STYLE,
        )

        block = {
            "vbox": block_vbox,
            "filter_type": filter_type,
            "fourier_mode": fourier_mode,
            "p_input": p_input,
            "q_input": q_input,
            "func_input": func_input,
            "kernel_input": kernel_input,
            "transform_input": transform_input,
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

    # pipline

    def _block_config(b):
        ft = b["filter_type"].value
        cfg = {"type": ft}
        if ft == "fourier":
            cfg["mode"] = b["fourier_mode"].value
            cfg["p_text"] = b["p_input"].value
            cfg["q_text"] = b["q_input"].value
            cfg["func_text"] = b["func_input"].value
        elif ft == "convolution":
            cfg["kernel_text"] = b["kernel_input"].value
        elif ft == "transform":
            cfg["expr_text"] = b["transform_input"].value
        return cfg

    def _get_filter_configs():
        return [_block_config(b) for b in filter_blocks]

    def _rebuild(change=None):
        source = _generate_source(
            source_shape.value, harmonics_input.value, draw.samples
        )
        freq = freq_slider.value

        for b in filter_blocks:
            b["formula_html"].value = _block_formula_latex(b)
            _plot_filter_response(b["preview_out"], _block_config(b), freq)

        filtered = _apply_filter_chain(source, _get_filter_configs())

        real_c, imag_c = samples_to_fourier_coeffs(filtered)
        audio.periodic_real_coeffs = real_c
        audio.periodic_coeffs = imag_c
        audio.frequencies = {"main": [freq]}
        audio.waveforms = {"main": "custom"}

        _update_plots(filtered, freq)

    def _update_plots(signal, freq):
        plot_waveform_and_fft(fft_out, signal, freq, label="filtered")

    # observers
    freq_slider.observe(_rebuild, "value")
    harmonics_input.observe(_rebuild, "value")
    draw.observe(_rebuild, "samples")

    _rebuild()

    # layout

    output_block = widgets.VBox(
        [
            widgets.HTML('<b style="color:#ddd;font-size:13px;">Audio Output</b>'),
            section("Volume"),
            vol_slider,
            audio,
            fft_out,
        ],
        layout=_BLOCK_STYLE,
    )

    return widgets.VBox(
        [
            source_block,
            widgets.HTML(_ARROW_HTML),
            filter_container,
            add_filter_btn,
            widgets.HTML(_ARROW_HTML),
            output_block,
        ]
    )
