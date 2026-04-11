# used by: cells\plot_multiplication.py
import numpy as np
import matplotlib.pyplot as plt


class PlotManager:

    def __init__(
        self, fs = None, figsize = None
    ):
        self.fs = fs
        self.figsize = figsize
        self._plots = []
        self._default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def add_plot(
        self,
        y,
        fs,
        x_min: float = 0,
        x_max: float = 1,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        grid: bool = True,
        **kwargs,
    ):
        if fs is None:
            if self.fs is None:
                raise ValueError(
                    "Sampling frequency (fs) must be provided either in __init__ or add_plot"
                )
            fs = self.fs

        plot_info = {
            "y": y,
            "fs": fs,
            "x_min": x_min,
            "x_max": x_max,
            "title": title,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "grid": grid,
            "kwargs": kwargs,
        }
        self._plots.append(plot_info)

    def clear(self):
        self._plots = []

    def _calculate_layout(self, num_plots: int):
        if num_plots == 1:
            return (1, 1)
        elif num_plots == 2:
            return (2, 1)
        elif num_plots <= 4:
            return (2, 2)
        elif num_plots <= 6:
            return (3, 2)
        elif num_plots <= 9:
            return (3, 3)
        else:
            cols = int(np.ceil(np.sqrt(num_plots)))
            rows = int(np.ceil(num_plots / cols))
            return (rows, cols)

    def _calculate_figsize(self, rows: int, cols: int):
        if self.figsize is not None:
            return self.figsize

        width_per_col = 10 if cols == 1 else 6
        height_per_row = 4

        return (width_per_col * cols, height_per_row * rows)

    def render(self, tight_layout: bool = True, show: bool = True) -> plt.Figure:
        if not self._plots:
            print("No plots to render. Use add_plot() to add plots first.")
            return None

        num_plots = len(self._plots)
        rows, cols = self._calculate_layout(num_plots)
        figsize = self._calculate_figsize(rows, cols)

        fig, axs = plt.subplots(rows, cols, figsize=figsize, squeeze=False)

        axs_flat = axs.flatten()

        for idx, plot_info in enumerate(self._plots):
            ax = axs_flat[idx]

            fs = int(plot_info["fs"])  # Ensure fs is an integer
            x_min = plot_info["x_min"]
            x_max = plot_info["x_max"]
            x = np.linspace(x_min, x_max, fs, endpoint=False)

            y_funcs = plot_info["y"]
            kwargs = plot_info["kwargs"].copy()

            if isinstance(y_funcs, dict):
                for label, y_func in y_funcs.items():
                    y = y_func(x)
                    ax.plot(x, y, label=label, **kwargs)
                ax.legend()
            else:
                y = y_funcs(x)
                ax.plot(x, y, **kwargs)

            if plot_info["title"]:
                ax.set_title(plot_info["title"])
            if plot_info["xlabel"]:
                ax.set_xlabel(plot_info["xlabel"])
            if plot_info["ylabel"]:
                ax.set_ylabel(plot_info["ylabel"])
            if plot_info["grid"]:
                ax.grid(True)

        for idx in range(num_plots, len(axs_flat)):
            axs_flat[idx].set_visible(False)

        if tight_layout:
            plt.tight_layout()

        if show:
            plt.show()

        return fig