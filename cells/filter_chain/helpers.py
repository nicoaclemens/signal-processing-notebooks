# used by: cells\filter_chain\plotting.py, cells\filter_chain\processing.py, cells\filter_chain\ui.py
import re

import numpy as np

from utils.STYLES import FFT_PLOT_COLORS, FORMULA_STYLE, PLOT
from utils.filters import poly_ratio_H
from utils.texrender import expr_to_latex, poly_to_latex

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


__all__ = [
    "FFT_PLOT_COLORS",
    "N_PERIOD",
    "PLOT",
    "_block_formula_latex",
    "_eval_fourier_H",
    "_taper_knob",
    "_with_knob",
]
