import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Union, Tuple, Callable


class PlotManager:
    """
    A flexible plot manager that allows you to easily add multiple plots
    and render them with intelligent layout, sizing, and labeling.

    Usage:
        p = PlotManager()
        p.fs = 1000
        p.add_plot(
            fs=1000, x_min=0, x_max=1,
            y={'x1': lambda x: np.sin(2*np.pi*50*x), 'x2': lambda x: np.sin(2*np.pi*120*x)},
            title="Signals", xlabel="Time [s]", ylabel="Amplitude"
        )
        p.render()
    """

    def __init__(
        self, fs: Optional[float] = None, figsize: Optional[Tuple[float, float]] = None
    ):
        """
        Initialize the PlotManager.

        Args:
            fs: Default sampling frequency (optional, can be overridden per plot)
            figsize: Default figure size (width, height) in inches. If None, auto-calculated
        """
        self.fs = fs
        self.figsize = figsize
        self._plots = []
        self._default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def add_plot(
        self,
        y: Union[Dict[str, Callable], Callable],
        fs: Optional[float] = None,
        x_min: float = 0,
        x_max: float = 1,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        grid: bool = True,
        **kwargs,
    ):
        """
        Add a plot to the collection. Does not render immediately.

        Args:
            y: Y-axis function(s). Can be:
               - Dict mapping labels to functions: {'signal1': lambda x: ..., 'signal2': lambda x: ...}
               - Single function: lambda x: ...
            fs: Sampling frequency. If None, uses self.fs
            x_min: Minimum x value
            x_max: Maximum x value
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            **kwargs: Additional plotting options (i.e. color, linestyle, etc.)
        """
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
        """Clear all stored plots."""
        self._plots = []

    def _calculate_layout(self, num_plots: int) -> Tuple[int, int]:
        """
        alculate subplot layout

        Args:
            num_plots: Number of plots to display

        Returns:
            Tuple of (rows, cols) for subplot layout
        """
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

    def _calculate_figsize(self, rows: int, cols: int) -> Tuple[float, float]:
        """
        Calculate appropriate figure size based on layout.

        Args:
            rows: Number of subplot rows
            cols: Number of subplot columns

        Returns:
            Tuple of (width, height) in inches
        """
        if self.figsize is not None:
            return self.figsize

        width_per_col = 10 if cols == 1 else 6
        height_per_row = 4

        return (width_per_col * cols, height_per_row * rows)

    def render(self, tight_layout: bool = True, show: bool = True) -> plt.Figure:
        """
        Render all stored plots with intelligent layout and sizing.

        Args:
            tight_layout: Whether to apply tight_layout for better spacing
            show: Whether to call plt.show() after rendering

        Returns:
            The created matplotlib Figure object
        """
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

    def display(self, **kwargs) -> plt.Figure:
        """Alias for render(). Displays all stored plots."""
        return self.render(**kwargs)

    def __len__(self) -> int:
        """Return the number of stored plots."""
        return len(self._plots)

    def __repr__(self) -> str:
        """String representation of the PlotManager."""
        return f"PlotManager(plots={len(self._plots)}, fs={self.fs})"
