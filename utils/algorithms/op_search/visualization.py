# used by: utils\algorithms\op_search\solver.py
# Visualization and reporting for Solver results
from typing import Optional
import numpy as np
from .problem import Problem
from .result import OptimizationResult

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


class SolverVisualizer:

    def __init__(self, problem: Problem, verbose: bool = False):
        self.problem = problem
        self.verbose = verbose
        self._eval_history = []

    def print_analysis(self, strategy: str, options: dict) -> None:
        if not self.verbose:
            return

        t = self.problem.traits
        print("Solver analysis")
        print(f"  parameters        : {t['n_params']}")
        print(f"  objectives        : {t['n_objectives']}")
        print(f"  search space size : {t['search_space_size']:.3g}")
        print(f"  discreteness      : {t['discreteness_ratio']:.0%}")
        print(f"  -> selected       : {strategy}")
        print(f"  options           : {options}")

    def print_result(self, result: OptimizationResult) -> None:
        """Print formatted result summary."""
        if not self.verbose:
            return

        print("\nOptimization Result")
        print(f"  strategy    : {result.strategy_used}")
        print(f"  objective   : {result.fx:.6g}")
        print(f"  evals       : {result.n_evaluations}")
        print(f"  converged   : {result.converged}")
        print("  parameters  :")
        for name, val in result.x.items():
            print(f"    {name:20s} = {val:.6g}")
        if result.metadata:
            print("  metadata    :")
            for key, val in result.metadata.items():
                print(f"    {key:20s} = {val}")

    def format_result(self, result: OptimizationResult) -> str:
        """Return a compact human-friendly summary string for a result."""
        lines = [
            "Optimization Result",
            f"  strategy    : {result.strategy_used}",
            f"  objective   : {result.fx:.6g}",
            f"  evals       : {result.n_evaluations}",
            f"  converged   : {result.converged}",
            "  parameters  :",
        ]
        for name, val in result.x.items():
            lines.append(f"    {name:20s} = {val:.6g}")
        return "\n".join(lines)

    def plot_result(
        self,
        result: OptimizationResult,
        objective_targets: Optional[dict[str, float]] = None,
        show: bool = True,
        show_history: bool = False,
        save_path: Optional[str] = None,
    ) -> None:
        if not HAS_MATPLOTLIB:
            if self.verbose:
                print("matplotlib not available; skipping plot")
            return

        objective_targets = objective_targets or {}
        obj_names = [obj.name for obj in self.problem.objectives]
        obj_vals = [obj.evaluate(result.x) for obj in self.problem.objectives]
        directions = [obj.minimize for obj in self.problem.objectives]
        target_vals = [float(objective_targets.get(name, 0.0)) for name in obj_names]

        objective_history = result.metadata.get("objective_history", [])
        elapsed_history = result.metadata.get("elapsed_history", [])
        has_weighted_history = show_history and bool(result.eval_history)
        has_obj_history = show_history and bool(objective_history)

        nrows = 2 if (has_weighted_history or has_obj_history) else 1
        fig, axes = plt.subplots(nrows, 2, figsize=(14, 5 * nrows))
        if nrows == 1:
            axes = np.array([axes])

        ax_obj = axes[0, 0]
        colors = ["steelblue" if m else "coral" for m in directions]
        x_idx = np.arange(len(obj_names))
        bars = ax_obj.bar(x_idx - 0.2, obj_vals, width=0.4, color=colors, label="value")
        ax_obj.bar(
            x_idx + 0.2,
            target_vals,
            width=0.4,
            color="gray",
            alpha=0.6,
            label="target",
        )
        ax_obj.set_xticks(x_idx)
        ax_obj.set_xticklabels(obj_names)
        ax_obj.set_ylabel("Value")
        ax_obj.set_title("Objectives at Optimum vs Target")
        ax_obj.grid(axis="y", alpha=0.3)
        ax_obj.legend()

        for bar, minimize in zip(bars, directions):
            label = "minimize" if minimize else "maximize"
            ax_obj.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="gray",
            )

        ax_acc = axes[0, 1]
        abs_errors = [abs(v - t) for v, t in zip(obj_vals, target_vals)]
        ax_acc.bar(obj_names, abs_errors, color="seagreen")
        if any(err > 0 for err in abs_errors):
            ax_acc.set_yscale("log")
        ax_acc.set_ylabel("|objective - target|")
        ax_acc.set_title("Accuracy to Target at Optimum")
        ax_acc.grid(axis="y", alpha=0.3)

        if nrows == 2:
            ax_conv = axes[1, 0]
            if has_weighted_history:
                running_best: list[float] = []
                best = float("inf")
                for v in result.eval_history:
                    best = min(best, v)
                    running_best.append(best)

                ax_conv.plot(
                    range(1, len(running_best) + 1),
                    running_best,
                    color="steelblue",
                    linewidth=1.5,
                    label="running best",
                )
                ax_conv.set_xlabel("Evaluations")
                ax_conv.set_ylabel("Best weighted objective")
                ax_conv.set_title("Convergence over Evaluations")
                ax_conv.grid(alpha=0.3)
                ax_conv.legend()
            else:
                ax_conv.set_axis_off()

            ax_traj = axes[1, 1]
            if has_obj_history:
                obj_hist = np.asarray(objective_history, dtype=float)
                eval_x = np.arange(1, obj_hist.shape[0] + 1)

                if elapsed_history and len(elapsed_history) == obj_hist.shape[0]:
                    x_vals = np.asarray(elapsed_history, dtype=float)
                    x_label = "Time (s)"
                    title = "Objective Accuracy over Time"
                else:
                    x_vals = eval_x
                    x_label = "Evaluations"
                    title = "Objective Accuracy over Evaluations"

                for i, name in enumerate(obj_names):
                    target = target_vals[i]
                    errors = np.abs(obj_hist[:, i] - target)
                    ax_traj.plot(x_vals, errors, linewidth=1.4, label=name)

                if np.any(obj_hist != np.asarray(target_vals, dtype=float)):
                    ax_traj.set_yscale("log")
                ax_traj.set_xlabel(x_label)
                ax_traj.set_ylabel("|objective - target|")
                ax_traj.set_title(title)
                ax_traj.grid(alpha=0.3)
                ax_traj.legend()
            else:
                ax_traj.set_axis_off()

        subtitle = (
            f"{result.strategy_used} | fx={result.fx:.4g} | "
            f"evals={result.n_evaluations} | converged={result.converged}"
        )
        fig.suptitle(subtitle)
        fig.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=100, bbox_inches="tight")
        if show:
            plt.show()


class ProgressSolveWrapper:
    """Context manager for solve() with optional tqdm progress."""

    def __init__(self, max_evaluations: Optional[int] = None, desc: str = "Optimizing"):
        self.max_evaluations = max_evaluations
        self.desc = desc
        self.pbar = None
        self.n_evals = 0

    def __enter__(self):
        if HAS_TQDM:
            self.pbar = tqdm(total=self.max_evaluations, desc=self.desc, unit="eval")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pbar is not None:
            self.pbar.close()

    def update(self, n: int = 1) -> None:
        self.n_evals += n
        if self.pbar is not None:
            self.pbar.update(n)

    def on_evaluation(self, n_eval: int, fx: float) -> None:
        """Progress callback invoked after each objective evaluation."""
        increment = max(0, n_eval - self.n_evals)
        if increment:
            self.update(increment)
        self.set_postfix(fx=f"{fx:.3g}")

    def set_postfix(self, **kwargs) -> None:
        """Update progress bar postfix."""
        if self.pbar is not None:
            self.pbar.set_postfix(**kwargs)
