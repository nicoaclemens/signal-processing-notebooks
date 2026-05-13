# used by: utils\algorithms\op_search\solver.py
# Visualization and reporting for Solver results
import math
from typing import Optional
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
    """Visualization, progress tracking, and reporting for op_search optimization."""

    def __init__(self, problem: Problem, verbose: bool = False):
        self.problem = problem
        self.verbose = verbose
        self._eval_history = []

    def print_analysis(self, strategy: str, options: dict) -> None:
        """Print pre-solve analysis: problem traits and selected strategy."""
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

    def plot_result(
        self,
        result: OptimizationResult,
        show: bool = True,
        show_history: bool = False,
        save_path: Optional[str] = None,
    ) -> None:
        """
        Plot per-objective values at the optimum.
        show_history=True adds a convergence subplot (requires eval_history in result).
        """
        if not HAS_MATPLOTLIB:
            if self.verbose:
                print("matplotlib not available; skipping plot")
            return

        has_history = show_history and bool(result.eval_history)
        ncols = 2 if has_history else 1
        fig, axes = plt.subplots(1, ncols, figsize=(7 * ncols, 5))
        if ncols == 1:
            axes = [axes]

        # --- Left: per-objective bar chart ---
        ax_obj = axes[0]
        obj_names = [obj.name for obj in self.problem.objectives]
        obj_vals = [obj.evaluate(result.x) for obj in self.problem.objectives]
        directions = [obj.minimize for obj in self.problem.objectives]
        colors = ["steelblue" if m else "coral" for m in directions]

        bars = ax_obj.bar(obj_names, obj_vals, color=colors)
        ax_obj.set_ylabel("Value")
        ax_obj.set_title("Objectives at Optimum")
        ax_obj.grid(axis="y", alpha=0.3)

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

        # --- Right: convergence curve (running best) ---
        if has_history:
            ax_conv = axes[1]
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
            )
            ax_conv.set_xlabel("Evaluations")
            ax_conv.set_ylabel("Best Objective (weighted sum)")
            ax_conv.set_title("Convergence")
            ax_conv.grid(alpha=0.3)

        fig.suptitle(
            f"{result.strategy_used}  |  fx={result.fx:.4g}"
            f"  |  evals={result.n_evaluations}  |  converged={result.converged}"
        )
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
        if HAS_TQDM and self.max_evaluations is not None:
            self.pbar = tqdm(total=self.max_evaluations, desc=self.desc, unit="eval")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pbar:
            self.pbar.close()

    def update(self, n: int = 1) -> None:
        """Update progress bar by n evaluations."""
        self.n_evals += n
        if self.pbar:
            self.pbar.update(n)

    def set_postfix(self, **kwargs) -> None:
        """Update progress bar postfix."""
        if self.pbar:
            self.pbar.set_postfix(**kwargs)
