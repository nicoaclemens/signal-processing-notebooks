# used by:
from IPython.display import display
import ipywidgets as widgets
import numpy as np
import pandas as pd

from .STYLES import QUERY

_WIDGET_STYLE = {"description_width": "initial"}
_CELL_WIDTH = "90px"
_CELL_HEIGHT = "30px"

_HEADER_CORNER = (
    f"<div style='"
    f"background:{QUERY.header_color};color:{QUERY.header_text};"
    f"font-weight:bold;padding:4px 8px;"
    f"min-width:90px;border:{QUERY.border};box-sizing:border-box;'>"
    f"&nbsp;</div>"
)


def _HEADER_CELLS(x):
    return (
        f"<div style='"
        f"background:{QUERY.header_color};color:{QUERY.header_text};"
        f"font-weight:bold;padding:4px 6px;width:{_CELL_WIDTH};"
        f"text-align:center;border:{QUERY.border};box-sizing:border-box;'>"
        f"{x}</div>"
    )


def _ROW_HEADER(bg, label):
    return (
        f"<div style='"
        f"background:{bg};color:{QUERY.header_text};font-weight:bold;"
        f"padding:4px 8px;min-width:90px;"
        f"border:{QUERY.border};box-sizing:border-box;"
        f"display:flex;align-items:center;'>"
        f"{label}</div>"
    )


def _TITLE_HTML(x):
    return f"<h3 style='margin:4px 0 8px 0;color:{QUERY.title_color};'>{x}</h3>"


def _coerce(value, dtype):
    try:
        return dtype(value)
    except (ValueError, TypeError):
        return value


class Query:

    _GETTER_REGISTRY = {
        "table": "_get_table",
        "text": "_get_text",
        "checkboxes": "_get_checkboxes",
    }

    def __init__(self):
        self._type = None
        self._data = None

    def get(self, *args):
        if self._type == None:
            raise RuntimeError("No Query initialized yet")
        getter_name = self._GETTER_REGISTRY.get(self._type)
        if getter_name is None:
            raise RuntimeError(f"Unknown query type '{self._type}'")
        getter = getattr(self, getter_name)
        return getter(*args)

    def table(self, rows=3, cols=3, title="", dtype=str, default=""):  #

        row_labels = (
            [str(r) for r in rows]
            if not isinstance(rows, int)
            else [f"Row {i+1}" for i in range(rows)]
        )
        col_labels = (
            [str(r) for r in cols]
            if not isinstance(cols, int)
            else [f"Col {i+1}" for i in range(cols)]
        )
        n_rows = len(row_labels)
        n_cols = len(col_labels)

        cell_widgets = [
            [
                widgets.Text(
                    value=str(default),
                    layout=widgets.Layout(width=_CELL_WIDTH, height=_CELL_HEIGHT),
                    style={"description_width": "0px"},
                )
                for _ in range(n_cols)
            ]
            for __ in range(n_rows)
        ]

        self._data = {
            "cell_widgets": cell_widgets,
            "row_labels": row_labels,
            "col_labels": col_labels,
            "dtype": dtype,
        }

        header_corner = widgets.HTML(_HEADER_CORNER)
        header_cells = [header_corner] + [
            widgets.HTML(_HEADER_CELLS(col)) for col in col_labels
        ]
        header_row = widgets.HBox(header_cells)
        grid_rows = [header_row]
        for ri, (row_label, row_cells) in enumerate(zip(row_labels, cell_widgets)):
            bg = QUERY._ALT_ROW if ri % 2 else "white"
            row_header = widgets.HTML(_ROW_HEADER(bg, row_label))
            for cell in row_cells:
                cell.layout.border = QUERY._BORDER
            grid_rows.append(widgets.HBox([row_header] + row_cells))

        title_html = widgets.HTML(_TITLE_HTML(title))
        grid = widgets.VBox(grid_rows)
        display(widgets.VBox([title_html, grid]))

    def checkboxes(self, options, label="", defaults=None, description="", cols=1):
        self._type = "checkboxes"
        pre_checked = set(defaults or [])
        checkbox_widgets = [
            widgets.Checkbox(
                value=opt in pre_checked,
                description=opt,
                indent=False,
                style=_WIDGET_STYLE,
                layout=widgets.Layout(width="200px"),
            )
            for opt in options
        ]
        self._data = {"widgets": checkbox_widgets, "options": list(options)}
        label_html = widgets.HTML(f"<b style='color:#2C3E50;'>{label}</b>")
        cols = [[] for _ in range(cols)]
        for i, cb in enumerate(checkbox_widgets):
            cols[i % cols].append(cb)
        grid = widgets.HBox([widgets.VBox(col) for col in cols if col])
        children = [label_html, grid]
        if description:
            children.append(description)
        display(widgets.VBox(children))

    def _get_table(self, *args):

        cell_widgets = self._data["cell_widgets"]
        row_labels = self._data["row_labels"]
        col_labels = self._data["col_labels"]
        dtype = self._data["dtype"]
        fmt = args[0].lower() if args else "raw"

        if fmt == "raw":
            return [[cell.value for cell in row] for row in cell_widgets]

        data = [[_coerce(cell.value, dtype) for cell in row] for row in cell_widgets]

        if fmt == "coerced":
            return data

        if fmt == "dict":
            return {
                col: [data[ri][ci] for ri in range(len(data))]
                for ci, col in enumerate(col_labels)
            }

        if fmt == "pandas":
            return pd.DataFrame(data, index=row_labels, columns=col_labels)

        raise ValueError(f"Invalid Argument(s): {args}")

    def _get_checkboxes(self, *args):
        return [
            opt
            for opt, cb in zip(self._data["widgets"], self._data["options"])
            if cb.value
        ]

    def __repr__(self) -> str:
        if self._query_type is None:
            return "Query(no active widget)"
        return f"Query(type={self._query_type!r})"
