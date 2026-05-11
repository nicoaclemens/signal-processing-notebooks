# used by: utils\algorithms\op_search\solver.py
import math
import numpy as np
from scipy.optimize import minimize
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy


class LocalSearch(Strategy):

    def _decode(self, vec: np.ndarray) -> dict[str, float]:
        x = {}
        for i, p in enumerate(self.problem.parameters):
            v = float(vec[i])
            if isinstance(p.space, (_E, DiscreteSpace)):
                x[p.name] = p.space.snap(math.exp(v))
            else:
                lo, hi = p.space
                x[p.name] = max(lo, min(hi, v))
        return x

    def run(self) -> OptimizationResult:
        x0, bounds = [], []
        for p in self.problem.parameters:
            if isinstance(p.space, (_E, DiscreteSpace)):
                vals = p.space.values
                lo, hi = math.log(vals[0]), math.log(vals[-1])
                x0.append((lo + hi) / 2)
                bounds.append((lo, hi))
            else:
                lo, hi = p.space
                x0.append((lo + hi) / 2)
                bounds.append((lo, hi))

        method = self.options.get("method", "Nelder-Mead")
        maxiter = self.options.get("maxiter", 1000)

        result = minimize(
            lambda v: self._evaluate(self._decode(v)),
            x0,
            method=method,
            bounds=bounds if method not in ("Nelder-Mead", "Powell") else None,
            options={"maxiter": maxiter},
        )
        best_x = self._decode(result.x)
        return OptimizationResult(
            x=best_x,
            fx=float(result.fun),
            strategy_used=f"local_{method.lower()}",
            n_evaluations=self._n_evals,
            converged=bool(result.success),
            metadata={"scipy_message": result.message},
        )
