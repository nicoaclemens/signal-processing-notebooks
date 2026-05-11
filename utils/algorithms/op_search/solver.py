# used by:
from __future__ import annotations
import math
import warnings
from dataclasses import dataclass, field
from typing import Literal

from .problem import Problem
from .result import OptimizationResult
from .enumbers import _E, DiscreteSpace
from .strategies.brute_force import BruteForce
from .strategies.diff_ev import DifferentialEvolution
from .strategies.cma_es import CMAES
from .strategies.local import LocalSearch

StrategyName = Literal[
    "auto",
    "brute_force",
    "differential_evolution",
    "cma_es",
    "nelder_mead",
    "powell",
]
_BRUTE_FORCE_MAX = 100_000
_LOCAL_MAX_PARAMS = 6
_DE_MAX_PARAMS = 30


@dataclass
class SolverConfig:
    strategy: StrategyName = "auto"
    max_evaluations: int | None = None
    brute_force_max: int = _BRUTE_FORCE_MAX
    seed: int | None = None
    strategy_options: dict = field(default_factory=dict)
    verbose: bool = False


class Solver:

    def __init__(self, problem: Problem, config: SolverConfig | None = None):
        self.problem = problem
        self.config = config or SolverConfig()
        self._strategy_name: str = ""

    def solve(self) -> OptimizationResult:
        self._strategy_name = self._select_strategy()
        options = self._build_options(self._strategy_name)

        if self.config.verbose:
            self._print_report(self._strategy_name, options)

        strategy_cls = self._strategy_class(self._strategy_name)
        strategy = strategy_cls(self.problem, options)
        return strategy.run()

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

        if n <= _DE_MAX_PARAMS:
            return "differential_evolution"

        return "cma_es"

    def _build_options(self, strategy: str) -> dict:
        t = self.problem.traits
        n = t["n_params"]
        size = t["search_space_size"]
        max_ev = self.config.max_evaluations
        opts: dict = {"seed": self.config.seed}

        if strategy == "brute_force":
            pass

        elif strategy == "differential_evolution":
            popsize = max(15, 10 * n)
            if max_ev:
                maxiter = max(1, max_ev // (popsize * n))
            else:
                maxiter = max(200, 50 * n)
            opts.update({"popsize": popsize, "maxiter": maxiter, "tol": 1e-6})

        elif strategy == "cma_es":
            lam = 4 + int(3 * math.log(max(n, 2)))
            if max_ev:
                maxiter = max(50, max_ev // lam)
            else:
                maxiter = max(500, 200 * n)
            opts.update({"maxiter": maxiter, "verbose": -9})

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
        mapping = {
            "brute_force": BruteForce,
            "differential_evolution": DifferentialEvolution,
            "cma_es": CMAES,
            "nelder_mead": LocalSearch,
            "powell": LocalSearch,
        }
        if name not in mapping:
            raise ValueError(
                f"Unknown strategy '{name}'. " f"Choose from: {list(mapping)}"
            )
        return mapping[name]

    def _print_report(self, strategy: str, options: dict):
        t = self.problem.traits
        print("Solver analysis")
        print(f"  parameters        : {t['n_params']}")
        print(f"  search space size : {t['search_space_size']:.3g}")
        print(f"  discreteness      : {t['discreteness_ratio']:.0%}")
        print(
            f"  constraint delta  : {t['constraint_estimate']:+d} "
            f"({'over' if t['constraint_estimate'] > 0 else 'under'}determined)"
        )
        print(f"  -> selected        : {strategy}")
        print(f"  options           : {options}")
