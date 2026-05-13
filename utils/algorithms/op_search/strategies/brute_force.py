# used by: utils\algorithms\op_search\solver.py
import itertools
from ..problem import Problem
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy


class BruteForce(Strategy):
    """grid search over all discrete combinations"""

    def run(self) -> OptimizationResult:
        grids = []
        for p in self.problem.parameters:
            if isinstance(p.space, (_E, DiscreteSpace)):
                grids.append(list(p.space))
            else:
                raise TypeError(
                    f"BruteForce requires all parameters to be discrete; "
                    f"'{p.name}' is continuous."
                )

        names = [p.name for p in self.problem.parameters]
        best_x, best_fx = None, float("inf")
        max_evaluations = self.options.get("max_evaluations")
        converged = True

        for combo in itertools.product(*grids):
            if max_evaluations is not None and self._n_evals >= max_evaluations:
                converged = False
                break
            x = dict(zip(names, combo))
            fx = self._evaluate(x)
            if fx < best_fx:
                best_fx = fx
                best_x = x

        return OptimizationResult(
            x=best_x,
            fx=best_fx,
            strategy_used="brute_force",
            n_evaluations=self._n_evals,
            converged=converged,
        )
