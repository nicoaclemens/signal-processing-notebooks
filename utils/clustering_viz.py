# used by:

from typing import Callable
import matplotlib.pyplot as plt
import numpy as np
import ipywidgets as widgets
from IPython.display import display, clear_output


def visualize_clustering_suite(
    datasets: dict[str, tuple[np.ndarray, np.ndarray]],
    solvers: dict[str, Callable],
    steps: int = 20,
    figsize: tuple[int, int] = (15, 12),
    K: int = 2,
) -> None:
    n_datasets = len(datasets)
    n_solvers = len(solvers)
    solver_items = list(solvers.items())
    dataset_items = list(datasets.items())

    # Precompute
    all_steps = {}
    max_steps = 0
    for solver_idx, (solver_name, solver_fn) in enumerate(solver_items):
        for dataset_idx, (dataset_name, (X, y_true)) in enumerate(dataset_items):
            try:
                steps_list = list(solver_fn(X, K=K, steps=steps))
            except Exception as e:
                steps_list = [(None, None)]
                print(f"Error with {solver_name} on {dataset_name}: {e}")
            all_steps[(solver_idx, dataset_idx)] = steps_list
            if len(steps_list) > max_steps:
                max_steps = len(steps_list)

    fig, axes = plt.subplots(n_solvers, n_datasets, figsize=figsize, squeeze=False)
    fig.suptitle(
        "Clustering Comparison (Rows: Algorithms, Columns: Datasets)",
        fontsize=16,
        fontweight="bold",
    )

    def plot_step(step):
        for solver_idx, (solver_name, _) in enumerate(solver_items):
            for dataset_idx, (dataset_name, _) in enumerate(dataset_items):
                ax = axes[solver_idx, dataset_idx]
                ax.clear()
                steps_list = all_steps[(solver_idx, dataset_idx)]
                if step < len(steps_list):
                    assignment, centroids = steps_list[step]
                else:
                    assignment, centroids = steps_list[-1]

                if assignment is not None:
                    X = datasets[dataset_name][0]
                    labels = assignment[:, -1] if assignment.ndim > 1 else assignment
                    ax.scatter(
                        X[:, 0],
                        X[:, 1],
                        c=labels,
                        cmap="viridis",
                        s=30,
                        alpha=0.6,
                        edgecolors="black",
                        linewidth=0.5,
                    )
                    if centroids is not None and len(centroids) > 0:
                        ax.scatter(
                            centroids[:, 0],
                            centroids[:, 1],
                            c="red",
                            marker="X",
                            s=200,
                            edgecolors="black",
                            linewidth=2,
                            label="Centroids",
                        )

                if dataset_idx == 0:
                    ax.set_ylabel(solver_name, fontsize=12, fontweight="bold")
                else:
                    ax.set_ylabel("")

                if solver_idx == 0:
                    ax.set_title(dataset_name, fontsize=12, fontweight="bold")
                else:
                    ax.set_title("")

                ax.set_xlabel("")
                ax.legend().set_visible(False)
                ax.grid(alpha=0.3)

        fig.tight_layout(rect=(0, 0, 1, 0.96))
        fig.canvas.draw_idle()

    slider = widgets.IntSlider(
        value=0,
        min=0,
        max=max_steps - 1,
        step=1,
        description="Step",
        continuous_update=False,
        style={"description_width": "initial"},
        layout=widgets.Layout(width="60%"),
    )

    def on_slider_change(change):
        plot_step(change["new"])

    slider.observe(on_slider_change, names="value")
    display(slider)
    plot_step(0)


def run_solver_on_dataset(
    X: np.ndarray,
    solver_fn: Callable,
    K: int = 2,
    step_delay: float = 0.5,
):
    fig, ax = plt.subplots(figsize=(8, 8))

    try:
        step_count = 0
        for assignment, centroids in solver_fn(X, K=K):
            ax.clear()

            labels = assignment[:, -1] if assignment.ndim > 1 else assignment

            ax.scatter(
                X[:, 0],
                X[:, 1],
                c=labels,
                cmap="viridis",
                s=30,
                alpha=0.6,
                edgecolors="black",
                linewidth=0.5,
            )

            if centroids is not None and len(centroids) > 0:
                ax.scatter(
                    centroids[:, 0],
                    centroids[:, 1],
                    c="red",
                    marker="X",
                    s=200,
                    edgecolors="black",
                    linewidth=2,
                    label="Centroids",
                )

            ax.set_title(f"Clustering - Step {step_count}")
            ax.set_xlabel("Feature 1")
            ax.set_ylabel("Feature 2")
            ax.legend()
            ax.grid(alpha=0.3)

            plt.pause(step_delay)
            step_count += 1

    except Exception as e:
        print(f"Error during clustering: {e}")

    plt.tight_layout()
    plt.show()
