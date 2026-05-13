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


@dataclass
class SolverConfig:
    strategy: StrategyName = "auto"
    max_evaluations: int | None = None
    brute_force_max: int = _BRUTE_FORCE_MAX
    seed: int | None = None
    strategy_options: dict = field(default_factory=dict)
    verbose: bool = False

    def __post_init__(self) -> None:
        if self.max_evaluations is not None and self.max_evaluations <= 0:
            raise ValueError("max_evaluations must be > 0 when provided.")
        if self.brute_force_max <= 0:
            raise ValueError("brute_force_max must be > 0.")


class Solver:

    def __init__(self, problem: Problem, config: SolverConfig | None = None):
        self.problem = problem
        self.config = config or SolverConfig()
        self._strategy_name: str = ""

    def solve(self) -> OptimizationResult:
        self._strategy_name = self._select_strategy()
        options = self._build_options(self._strategy_name)

        visualizer = SolverVisualizer(self.problem, verbose=self.config.verbose)
        visualizer.print_analysis(self._strategy_name, options)

        strategy_cls = self._strategy_class(self._strategy_name)
        strategy = strategy_cls(self.problem, options)
        result = strategy.run()
        result.eval_history = strategy._fx_history
        visualizer.print_result(result)
        return result

    def solve_with_progress(self, desc: str = "Optimizing") -> OptimizationResult:
        """Solve with tqdm progress bar (if available)."""
        from .visualization import ProgressSolveWrapper

        with ProgressSolveWrapper(
            max_evaluations=self.config.max_evaluations, desc=desc
        ) as progress:
            result = self.solve()
            if progress.max_evaluations is not None:
                progress.pbar.close()
            return result

    def _select_strategy(self) -> str:
        if self.config.strategy != "auto":
            return self.config.strategy

        t = self.problem.traits
        n = t["n_params"]
        size = t["search_space_size"]
        dr = t["discreteness_ratio"]
        n_obj = len(self.problem.objectives)

        if n_obj > 1:
            warnings.warn(
                "Multi-objective detected; falling back to weighted-sum with "
                "differential_evolution. Consider a dedicated NSGA-II solver.",
                UserWarning,
            )

        if dr == 1.0 and size <= self.config.brute_force_max:
            return "brute_force"

        if dr == 0.0 and n <= _LOCAL_MAX_PARAMS:
            return "nelder_mead"

        if n <= _BAYESIAN_MAX_PARAMS and dr <= 0.5:
            return "bayesian_optimization"

        if dr > 0.5 and n <= _DE_MAX_PARAMS:
            return "simulated_annealing"

        if n <= _DE_MAX_PARAMS:
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
            popsize = max(15, 10 * n)
            if max_ev is not None:
                maxiter = max(1, max_ev // (popsize * n))
            else:
                maxiter = max(200, 50 * n)
            opts.update({"popsize": popsize, "maxiter": maxiter, "tol": 1e-6})

        elif strategy == "cma_es":
            lam = 4 + int(3 * math.log(max(n, 2)))
            if max_ev is not None:
                maxiter = max(50, max_ev // lam)
            else:
                maxiter = max(500, 200 * n)
            opts.update({"maxiter": maxiter, "verbose": -9})

        elif strategy == "bayesian_optimization":
            n_initial = max(5, 2 * n)
            if max_ev is not None:
                n_iterations = max(1, max_ev - n_initial)
                maxiter = max_ev
            else:
                n_iterations = max(10, 50 // n) if n > 0 else 10
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
            opts.update(
                {
                    "method": method,
                    "maxiter": max_ev or (1000 * n),
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
