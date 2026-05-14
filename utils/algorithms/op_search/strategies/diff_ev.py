# used by: tests\op_search\test_op_search.py, utils\algorithms\op_search\solver.py
import math
import numpy as np
from scipy.optimize import differential_evolution
from ..problem import Problem
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy

# Runtime Scaling: O(maxiter * popsize)


class DifferentialEvolution(Strategy):

    def _decode(self, vec: np.ndarray) -> dict[str, float]:
        x = {}
        for i, p in enumerate(self.problem.parameters):
            v = float(vec[i])
            if isinstance(p.space, (_E, DiscreteSpace)):
                x[p.name] = p.space.snap(math.exp(v))  # vec is in log-index space
            else:
                lo, hi = p.space
                if p.kind == "log_continuous":
                    x[p.name] = max(lo, min(hi, math.exp(v)))
                else:
                    x[p.name] = max(lo, min(hi, v))
        return x

    def run(self) -> OptimizationResult:
        bounds = []
        for p in self.problem.parameters:
            if isinstance(p.space, (_E, DiscreteSpace)):
                vals = p.space.values
                bounds.append((math.log(vals[0]), math.log(vals[-1])))
            else:
                lo, hi = p.space
                if p.kind == "log_continuous":
                    bounds.append((math.log(lo), math.log(hi)))
                else:
                    bounds.append((lo, hi))

        maxiter = self.options.get("maxiter", 1000)
        popsize = self.options.get("popsize", 15)
        tol = self.options.get("tol", 1e-6)
        seed = self.options.get("seed", None)

        result = differential_evolution(
            lambda v: self._evaluate(self._decode(v)),
            bounds=bounds,
            maxiter=maxiter,
            popsize=popsize,
            tol=tol,
            seed=seed,
            polish=True,
        )

        best_x = self._decode(result.x)
        return OptimizationResult(
            x=best_x,
            fx=float(result.fun),
            strategy_used="differential_evolution",
            n_evaluations=self._n_evals,
            converged=bool(result.success),
            metadata={"scipy_message": result.message},
        )
