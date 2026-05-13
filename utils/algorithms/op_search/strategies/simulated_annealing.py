# used by: utils\algorithms\op_search\solver.py
# Simulated Annealing wrapper for dual_annealing from scipy
import math
import numpy as np
from scipy.optimize import dual_annealing
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy


class SimulatedAnnealing(Strategy):
    """Wrapper around scipy.optimize.dual_annealing."""

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
        seed = self.options.get("seed", None)
        initial_temp = self.options.get("initial_temp", 5230.0)
        restart_temp_ratio = self.options.get("restart_temp_ratio", 2e-5)

        result = dual_annealing(
            lambda v: self._evaluate(self._decode(v)),
            bounds=bounds,
            maxiter=maxiter,
            seed=seed,
            initial_temp=initial_temp,
            restart_temp_ratio=restart_temp_ratio,
        )

        best_x = self._decode(result.x)
        return OptimizationResult(
            x=best_x,
            fx=float(result.fun),
            strategy_used="simulated_annealing",
            n_evaluations=self._n_evals,
            converged=bool(result.success),
            metadata={"scipy_message": result.message},
        )
