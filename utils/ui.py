import ipywidgets as widgets

SECTION_STYLE = "margin:0 0 2px 0; color:#aaa; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;"
SLIDER_LAYOUT = widgets.Layout(width="340px")
DD_LAYOUT = widgets.Layout(width="160px")
CB_LAYOUT = widgets.Layout(width="auto")

FFT_PLOT_COLORS = {
    "bg": "#1a1a2e",
    "grid": "#2a2a4a",
    "spine": "#3a3a5a",
    "label": "#aaa",
    "title": "#ddd",
    "tick": "#888",
    "legend": "#2d2d4a",
    "ledge": "#4a4a6a",
    "ltxt": "#e0e0e0",
}


def section(title):
    return widgets.HTML(f'<p style="{SECTION_STYLE}">{title}</p>')


def dark_ax(ax):
    c = FFT_PLOT_COLORS
    ax.set_facecolor(c["bg"])
    ax.tick_params(colors=c["tick"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(c["spine"])
    ax.grid(True, color=c["grid"], linewidth=0.5)
