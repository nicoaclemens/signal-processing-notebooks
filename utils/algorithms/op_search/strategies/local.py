# used by: tests\op_search\test_op_search.py, utils\algorithms\op_search\solver.py
import math
import numpy as np
from scipy.optimize import minimize
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy

# Runtime Scaling: O(maxiter * n) for Nelder-Mead, O(maxiter) for Powell


class LocalSearch(Strategy):

    def _decode(self, vec: np.ndarray) -> dict[str, float]:
        x = {}
        for i, p in enumerate(self.problem.parameters):
            v = float(vec[i])
            if isinstance(p.space, (_E, DiscreteSpace)):
                x[p.name] = p.space.snap(math.exp(v))
            else:
                lo, hi = p.space
                if p.kind == "log_continuous":
                    x[p.name] = max(lo, min(hi, math.exp(v)))
                else:
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
                if p.kind == "log_continuous":
                    log_lo, log_hi = math.log(lo), math.log(hi)
                    x0.append((log_lo + log_hi) / 2)
                    bounds.append((log_lo, log_hi))
                else:
                    x0.append((lo + hi) / 2)
                    bounds.append((lo, hi))

        method = self.options.get("method", "Nelder-Mead")
        maxiter = self.options.get("maxiter", 1000)

        result = minimize(
            lambda v: self._evaluate(self._decode(v)),
            x0,
            method=method,
            bounds=bounds if method != "Nelder-Mead" else None,
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
