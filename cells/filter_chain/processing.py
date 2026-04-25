# used by: cells\filter_chain\ui.py
import numpy as np

from utils.audio_files import resample_for_periodic_source
from utils.filters import (
    apply_convolution,
    apply_fourier_filter,
    apply_transform,
    eval_kernel,
)
from utils.signals import WAVE_FUNCS, custom_wave, parse_coeffs

from .helpers import N_PERIOD, _eval_fourier_H, _with_knob


def _generate_source(shape, coeffs_text, drawn_samples, uploaded_samples):
    t = np.linspace(0, 1, N_PERIOD, endpoint=False)
    if shape == "drawn":
        if drawn_samples and any(s != 0 for s in drawn_samples):
            src = np.array(drawn_samples)
            indices = np.linspace(0, len(src) - 1, N_PERIOD)
            return np.interp(indices, np.arange(len(src)), src)
        return np.zeros(N_PERIOD)
    if shape == "upload":
        if uploaded_samples is None or len(uploaded_samples) == 0:
            return np.zeros(N_PERIOD)
        return resample_for_periodic_source(uploaded_samples, N_PERIOD)
    if shape == "custom":
        return custom_wave(t, 1.0, parse_coeffs(coeffs_text))
    return WAVE_FUNCS[shape](t, 1.0)


def _apply_single_filter(signal, cfg):
    if not cfg.get("enabled", True):
        return signal

    ft = cfg["type"]
    if ft == "fourier":
        return apply_fourier_filter(
            signal,
            lambda k, c=cfg: _eval_fourier_H(c, k, c.get("base_freq", 1.0)),
        )
    if ft == "convolution":
        kernel = eval_kernel(
            _with_knob(cfg["kernel_text"], cfg["knob_effective"]), len(signal)
        )
        return apply_convolution(signal, kernel)
    if ft == "transform":
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


__all__ = ["_apply_filter_chain", "_generate_source"]
