# used by:
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display


def _build_lattice_points(basis: np.ndarray, radius: int) -> np.ndarray:
    grid = np.arange(-radius, radius + 1, dtype=float)
    indices = np.stack(np.meshgrid(grid, grid, grid, indexing="ij"), axis=-1).reshape(
        -1, 3
    )
    return indices @ basis


def _set_axes_equal(ax, points: np.ndarray) -> None:
    if points.size == 0:
        return

    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    center = (mins + maxs) / 2.0
    span = float(np.max(maxs - mins))
    span = max(span, 1.0)
    half = span / 2.0

    ax.set_xlim(center[0] - half, center[0] + half)
    ax.set_ylim(center[1] - half, center[1] + half)
    ax.set_zlim(center[2] - half, center[2] + half)


def plot_lattice(basis: np.ndarray, radius: int = 2) -> tuple[plt.Figure, plt.Axes]:
    basis = np.asarray(basis, dtype=float)
    if basis.shape != (3, 3):
        raise ValueError("basis must be a 3x3 array of lattice vectors")

    points = _build_lattice_points(basis, radius)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title("3D Lattice")

    ax.scatter(
        points[:, 0],
        points[:, 1],
        points[:, 2],
        s=18,
        alpha=0.75,
        color="tab:blue",
    )

    colors = ["tab:red", "tab:green", "tab:orange"]
    for idx, color in enumerate(colors):
        vector = basis[idx]
        ax.quiver(
            0,
            0,
            0,
            vector[0],
            vector[1],
            vector[2],
            color=color,
            linewidth=2.5,
            arrow_length_ratio=0.12,
        )
        ax.text(vector[0], vector[1], vector[2], f"a{idx + 1}", color=color)

    ax.scatter([0], [0], [0], color="black", s=50)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.grid(alpha=0.25)
    _set_axes_equal(ax, np.vstack([points, np.zeros((1, 3))]))

    plt.tight_layout()
    return fig, ax


def create_lattice_ui() -> None:
    basis_defaults = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )

    vector_inputs: list[list[widgets.FloatText]] = []
    vector_rows = []

    for row_idx, row_label in enumerate(("a1", "a2", "a3")):
        inputs = [
            widgets.FloatText(
                value=float(basis_defaults[row_idx, col_idx]),
                layout=widgets.Layout(width="90px"),
            )
            for col_idx in range(3)
        ]
        vector_inputs.append(inputs)
        vector_rows.append(
            widgets.HBox(
                [widgets.Label(f"{row_label} =", layout=widgets.Layout(width="40px"))]
                + inputs
            )
        )

    radius_slider = widgets.IntSlider(
        value=2,
        min=1,
        max=6,
        step=1,
        description="Radius",
        continuous_update=False,
        style={"description_width": "initial"},
        layout=widgets.Layout(width="60%"),
    )

    controls = widgets.VBox(vector_rows + [radius_slider])
    output = widgets.Output()

    def _render(*_ignored) -> None:
        basis = np.array(
            [[field.value for field in row] for row in vector_inputs], dtype=float
        )
        with output:
            output.clear_output(wait=True)
            fig, _ = plot_lattice(basis, radius_slider.value)
            display(fig)
            plt.close(fig)

    for row in vector_inputs:
        for field in row:
            field.observe(_render, names="value")
    radius_slider.observe(_render, names="value")

    display(controls)
    display(output)
    _render()
