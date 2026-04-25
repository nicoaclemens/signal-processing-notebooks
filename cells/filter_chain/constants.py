# used by: cells\filter_chain\ui.py
from utils.STYLES import (
    ARROW_HTML,
    BLOCK_HEADER_STYLE_LG,
    BLOCK_HEADER_STYLE_SM,
    BLOCK_LAYOUT,
    COLORS,
    DD_LAYOUT,
    SLIDER_LAYOUT,
)

SOURCE_OPTIONS = [
    ("Sine", "sine"),
    ("Sawtooth", "sawtooth"),
    ("Square", "square"),
    ("Triangle", "triangle"),
    ("Custom Series", "custom"),
    ("Drawn", "drawn"),
    ("Uploaded WAV", "upload"),
]

FILTER_TYPES = [
    ("Fourier-Domain Filter", "fourier"),
    ("Convolution", "convolution"),
    ("Transform", "transform"),
]

FOURIER_MODES = [
    ("Polynomial P(k)/Q(k)", "poly"),
    ("Function H(k)", "func"),
]

__all__ = [
    "ARROW_HTML",
    "BLOCK_HEADER_STYLE_LG",
    "BLOCK_HEADER_STYLE_SM",
    "BLOCK_LAYOUT",
    "COLORS",
    "DD_LAYOUT",
    "FILTER_TYPES",
    "FOURIER_MODES",
    "SLIDER_LAYOUT",
    "SOURCE_OPTIONS",
]
