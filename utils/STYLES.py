# used by: cells\epicycles.py, cells\filter_chain.py, cells\play_audio_multiplication.py, utils\ui.py

import ipywidgets as widgets


class _AttrDict(dict):
    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            return _AttrDict(value)
        return value


COLORS = _AttrDict(
    {
        # dark-theme base surfaces
        "bg": "#1a1a2e",
        "bg_deep": "#12121f",
        "surface": "#2d2d4a",
        "surface_light": "#3a3a5a",
        "surface_lighter": "#4a4a6a",
        # primary accent
        "primary": "#7c6ff7",
        "primary_hover": "#6a5ce0",
        "primary_active": "#5a4cc8",
        "primary_glow": "rgba(124, 111, 247, 0.4)",
        # secondary accents
        "red": "#e05555",
        "red_hover": "#c94444",
        "red_glow": "rgba(224, 85, 85, 0.4)",
        "red_marker": "#ff6b6b",
        "green": "#5de8a0",
        "blue": "#6a9ff7",
        "orange": "#f7a16a",
        "purple": "#c77dff",
        "pink": "#f76a8a",
        # text hierarchy
        "text": "#e0e0e0",
        "text_title": "#ddd",
        "text_label": "#aaa",
        "text_tick": "#888",
        "text_muted": "#666",
        "text_subtle": "#555",
        "text_dark": "#333",
        "text_status": "#8888aa",
        "text_dim": "#6a6a8a",
        # borders / grid
        "border": "#2d2d4a",
        "grid": "#2a2a4a",
        "grid_fine": "rgba(255,255,255,0.06)",
    }
)

FFT_PLOT_COLORS = _AttrDict(
    {
        "bg": COLORS.bg,
        "grid": COLORS.grid,
        "spine": COLORS.surface_light,
        "label": COLORS.text_label,
        "title": COLORS.text_title,
        "tick": COLORS.text_tick,
        "legend": COLORS.surface,
        "ledge": COLORS.surface_lighter,
        "ltxt": COLORS.text,
    }
)

SIGNAL_COLORS = _AttrDict(
    {
        "x1": COLORS.blue,
        "x2": COLORS.orange,
        "product": COLORS.purple,
        "f_sum": COLORS.green,
        "f_diff": COLORS.pink,
    }
)


SLIDER_LAYOUT = widgets.Layout(width="340px")
DD_LAYOUT = widgets.Layout(width="160px")
CB_LAYOUT = widgets.Layout(width="auto")


PLOT = _AttrDict(
    {
        "line_color": COLORS.primary,
        "line_width": 1.2,
        "line_alpha": 0.9,
        "bar_alpha": 0.8,
        "marker_color": COLORS.surface_lighter,
        "marker_size": 2,
        "marker_alpha": 0.6,
        "grid_linewidth": 0.5,
        "tick_labelsize": 8,
        "label_fontsize": 10,
        "title_fontsize": 11,
        "title_pad": 6,
        "legend_fontsize": 9,
        "empty_fontsize": 12,
        "figsize_wide": (12, 3),
        "figsize_tall": (12, 5),
        "figsize_medium": (10, 3),
    }
)

# inline html
SECTION_STYLE = (
    f"margin:0 0 2px 0; color:{COLORS.text_label}; font-size:11px;"
    " font-weight:600; text-transform:uppercase; letter-spacing:0.05em;"
)

FREQ_LABEL_STYLE = f"font-size:12px; color:{COLORS.text_dark}; font-family:monospace;"

BLOCK_BORDER = f"1px solid {COLORS.surface_light}"
BLOCK_LAYOUT = widgets.Layout(
    border=BLOCK_BORDER,
    padding="8px",
    margin="4px 0",
)
ARROW_HTML = f'<div style="text-align:center;color:{COLORS.text_subtle};font-size:18px;">↓</div>'
FORMULA_STYLE = f"color:{COLORS.text_title};padding:4px 0;"
BLOCK_HEADER_STYLE_LG = f"color:{COLORS.text_title};font-size:13px;"
BLOCK_HEADER_STYLE_SM = f"color:{COLORS.text_title};font-size:12px;"