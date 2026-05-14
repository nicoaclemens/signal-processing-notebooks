# used by: tests\op_search\test_op_search.py
from __future__ import annotations
import math
import warnings
from dataclasses import dataclass, field
from typing import Literal

from .problem import Problem
from .result import OptimizationResult
from .visualization import SolverVisualizer
from .strategies.brute_force import BruteForce

StrategyName = Literal[
    "auto",
    "brute_force",
    "differential_evolution",
    "cma_es",
    "bayesian_optimization",
    "simulated_annealing",
    "nelder_mead",
    "powell",
]
_BRUTE_FORCE_MAX = 100_000
_LOCAL_MAX_PARAMS = 6
_DE_MAX_PARAMS = 30
_BAYESIAN_MAX_PARAMS = 15
_DISCRETENESS_THRESHOLD = 0.8  # Treat as discrete if >= 80% discrete params


@dataclass
class SolverConfig:
    strategy: StrategyName = "auto"
    max_evaluations: int | None = None
    brute_force_max: int = _BRUTE_FORCE_MAX
    local_max_params: int = _LOCAL_MAX_PARAMS
    bayesian_max_params: int = _BAYESIAN_MAX_PARAMS
    de_max_params: int = _DE_MAX_PARAMS
    discreteness_threshold: float = _DISCRETENESS_THRESHOLD
    seed: int | None = None
    strategy_options: dict = field(default_factory=dict)
    verbose: bool = False
    allow_multiobj_approximate: bool = True

    def __post_init__(self) -> None:
        if self.max_evaluations is not None and self.max_evaluations <= 0:
            raise ValueError("max_evaluations must be > 0 when provided.")
        if self.brute_force_max <= 0:
            raise ValueError("brute_force_max must be > 0.")
        if not (0.0 <= self.discreteness_threshold <= 1.0):
            raise ValueError("discreteness_threshold must be in [0, 1].")
        if self.local_max_params < 1:
            raise ValueError("local_max_params must be >= 1.")
        if self.bayesian_max_params < 1:
            raise ValueError("bayesian_max_params must be >= 1.")
        if self.de_max_params < 1:
            raise ValueError("de_max_params must be >= 1.")


class Solver:

    def __init__(self, problem: Problem, config: SolverConfig | None = None):
        self.problem = problem
        self.config = config or SolverConfig()
        self._strategy_name: str = ""

    def solve(self) -> OptimizationResult:
        self._validate_problem()
        self._strategy_name = self._select_strategy()
        options = self._build_options(self._strategy_name)
        options_for_metadata = {
            key: val for key, val in options.items() if key != "evaluation_callback"
        }

        strategy_cls = self._strategy_class(self._strategy_name)
        strategy = strategy_cls(self.problem, options)
        result = strategy.run()
        result.eval_history = list(getattr(strategy, "_fx_history", []))
        result.metadata.setdefault(
            "objective_history", list(getattr(strategy, "_objective_history", []))
        )
        result.metadata.setdefault(
            "elapsed_history", list(getattr(strategy, "_elapsed_history", []))
        )
        result.metadata.setdefault("selected_strategy", self._strategy_name)
        result.metadata.setdefault("strategy_options", options_for_metadata)
        return result

    def solve_with_progress(self, desc: str = "Optimizing") -> OptimizationResult:
        """Solve with tqdm progress bar (if available)."""
        from .visualization import ProgressSolveWrapper

        self._validate_problem()
        self._strategy_name = self._select_strategy()
        options = self._build_options(self._strategy_name)
        options_for_metadata = {
            key: val for key, val in options.items() if key != "evaluation_callback"
        }

        with ProgressSolveWrapper(
            max_evaluations=self.config.max_evaluations, desc=desc
        ) as progress:
            options["evaluation_callback"] = progress.on_evaluation
            strategy_cls = self._strategy_class(self._strategy_name)
            strategy = strategy_cls(self.problem, options)
            result = strategy.run()
            result.eval_history = list(getattr(strategy, "_fx_history", []))
            result.metadata.setdefault(
                "objective_history", list(getattr(strategy, "_objective_history", []))
            )
            result.metadata.setdefault(
                "elapsed_history", list(getattr(strategy, "_elapsed_history", []))
            )
            result.metadata.setdefault("selected_strategy", self._strategy_name)
            result.metadata.setdefault("strategy_options", options_for_metadata)
            return result

    def print_analysis(self) -> None:
        """Print problem + strategy analysis without running optimization."""
        self._validate_problem()
        strategy_name = self._select_strategy()
        options = self._build_options(strategy_name)
        visualizer = SolverVisualizer(self.problem, verbose=True)
        visualizer.print_analysis(strategy_name, options)

    def print_result(self, result: OptimizationResult) -> None:
        """Print a formatted optimization result."""
        visualizer = SolverVisualizer(self.problem, verbose=True)
        visualizer.print_result(result)

    def plot_result(
        self,
        result: OptimizationResult,
        objective_targets: dict[str, float] | None = None,
        show: bool = True,
        save_path: str | None = None,
    ) -> None:
        """Plot objective values, convergence, and accuracy-over-time for a result."""
        visualizer = SolverVisualizer(self.problem, verbose=self.config.verbose)
        visualizer.plot_result(
            result,
            objective_targets=objective_targets,
            show=show,
            show_history=True,
            save_path=save_path,
        )

    def _validate_problem(self) -> None:
        n_obj = len(self.problem.objectives)
        if n_obj > 1 and not self.config.allow_multiobj_approximate:
            raise ValueError(
                f"Multi-objective problem detected ({n_obj} objectives). "
                "Solver uses weighted-sum approximation which may miss Pareto optima. "
                "Set allow_multiobj_approximate=True to proceed, or use a dedicated "
                "multi-objective solver (e.g., NSGA-II)."
            )

    def _select_strategy(self) -> str:
        if self.config.strategy != "auto":
            return self.config.strategy

        t = self.problem.traits
        n = t["n_params"]
        size = t["search_space_size"]
        dr = t["discreteness_ratio"]
        n_obj = len(self.problem.objectives)

        if n_obj > 1:
            if not self.config.allow_multiobj_approximate:
                raise ValueError(
                    f"Multi-objective problem detected ({n_obj} objectives). "
                    "Solver uses weighted-sum approximation which may miss Pareto optima. "
                    "Set allow_multiobj_approximate=True to proceed, or use a dedicated "
                    "multi-objective solver (e.g., NSGA-II)."
                )
            warnings.warn(
                f"Multi-objective detected ({n_obj} objectives); using weighted-sum "
                "with differential_evolution. This may not find true Pareto optima. "
                "Consider a dedicated NSGA-II solver for better coverage.",
                UserWarning,
            )

        if dr >= self.config.discreteness_threshold and size != float("inf"):
            if size <= self.config.brute_force_max:
                return "brute_force"

        if n <= self.config.local_max_params and dr < 0.3:
            return "nelder_mead"

        if dr >= 0.5 and n <= self.config.de_max_params:
            return "simulated_annealing"

        if n <= self.config.bayesian_max_params and dr <= 0.5:
            return "bayesian_optimization"

        if dr < 0.1 and n <= self.config.de_max_params:
            return "cma_es"

        if n <= self.config.de_max_params:
            return "differential_evolution"

        return "cma_es"

    def _build_options(self, strategy: str) -> dict:
        t = self.problem.traits
        n = t["n_params"]
        max_ev = self.config.max_evaluations
        opts: dict = {"seed": self.config.seed}

        if strategy == "brute_force":
            size = t["search_space_size"]
            if (
                size > self.config.brute_force_max
                and max_ev is None
                and not self.config.strategy_options.get(
                    "allow_large_bruteforce", False
                )
            ):
                raise ValueError(
                    "Brute-force search space exceeds brute_force_max. "
                    "Set max_evaluations, increase brute_force_max, or choose another strategy."
                )
            if max_ev is not None:
                opts["max_evaluations"] = max_ev

        elif strategy == "differential_evolution":
            popsize = min(max(15, 10 * n), 150)

            if max_ev is not None:
                maxiter = max(1, max_ev // popsize)
            else:
                maxiter = max(100, min(500, 30 * n))

            opts.update({"popsize": popsize, "maxiter": maxiter, "tol": 1e-6})

        elif strategy == "cma_es":
            lam = 4 + int(3 * math.log(max(n, 2)))

            if max_ev is not None:
                maxiter = max(10, max_ev // lam)
            else:
                maxiter = max(200, min(1000, 100 * n))

            opts.update({"maxiter": maxiter, "verbose": -9})

        elif strategy == "bayesian_optimization":
            n_initial = max(5, 2 * n)

            if max_ev is not None:
                n_iterations = max(0, max_ev - n_initial)
                maxiter = max_ev
            else:
                n_iterations = max(20, min(200, 50 // max(n, 1)))
                maxiter = n_initial + n_iterations

            opts.update(
                {
                    "n_initial": n_initial,
                    "n_iterations": n_iterations,
                    "maxiter": maxiter,
                }
            )

        elif strategy == "simulated_annealing":
            maxiter = max_ev or 1000
            opts.update(
                {"maxiter": maxiter, "initial_temp": 5230.0, "restart_temp_ratio": 2e-5}
            )

        elif strategy in ("nelder_mead", "powell"):
            method = "Nelder-Mead" if strategy == "nelder_mead" else "Powell"

            if max_ev is not None:
                maxiter = max(100, max_ev // max(1, n))
            else:
                maxiter = max(500, 1000 * n)

            opts.update(
                {
                    "method": method,
                    "maxiter": maxiter,
                }
            )

        opts.update(self.config.strategy_options)
        return opts

    @staticmethod
    def _strategy_class(name: str):
        if name == "brute_force":
            return BruteForce

        if name == "differential_evolution":
            try:
                from .strategies.diff_ev import DifferentialEvolution
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Strategy 'differential_evolution' requires scipy. "
                    "Install with: pip install scipy"
                ) from exc
            return DifferentialEvolution

        if name == "cma_es":
            try:
                from .strategies.cma_es import CMAES
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Strategy 'cma_es' requires cma. " "Install with: pip install cma"
                ) from exc
            return CMAES

        if name == "bayesian_optimization":
            try:
                from .strategies.bayesian import BayesianOptimization
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Strategy 'bayesian_optimization' requires scipy. "
                    "Install with: pip install scipy"
                ) from exc
            return BayesianOptimization

        if name == "simulated_annealing":
            try:
                from .strategies.simulated_annealing import SimulatedAnnealing
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Strategy 'simulated_annealing' requires scipy. "
                    "Install with: pip install scipy"
                ) from exc
            return SimulatedAnnealing

        if name in ("nelder_mead", "powell"):
            try:
                from .strategies.local import LocalSearch
            except ModuleNotFoundError as exc:
                raise ModuleNotFoundError(
                    "Local strategies require scipy. Install with: pip install scipy"
                ) from exc
            return LocalSearch

        raise ValueError(
            f"Unknown strategy '{name}'. "
            "Choose from: ['brute_force', 'differential_evolution', 'cma_es', 'bayesian_optimization', 'simulated_annealing', 'nelder_mead', 'powell']"
        )
