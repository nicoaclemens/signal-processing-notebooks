# used by: utils\algorithms\op_search\solver.py
import math
import numpy as np
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy
import cma


class CMAES(Strategy):

    def _decode(self, vec: list[float]) -> dict[str, float]:
        x = {}
        for i, p in enumerate(self.problem.parameters):
            v = float(vec[i])
            if isinstance(p.space, (_E, DiscreteSpace)):
                x[p.name] = p.space.snap(math.exp(v))
            else:
                lo, hi = p.space
                x[p.name] = max(lo, min(hi, v))
        return x

    def _bounds_and_x0(self):
        lower, upper, x0 = [], [], []
        for p in self.problem.parameters:
            if isinstance(p.space, (_E, DiscreteSpace)):
                vals = p.space.values
                lo, hi = math.log(vals[0]), math.log(vals[-1])
                lower.append(lo)
                upper.append(hi)
                x0.append((lo + hi) / 2)
            else:
                lo, hi = p.space
                lower.append(lo)
                upper.append(hi)
                x0.append((lo + hi) / 2)
        return lower, upper, x0

    def run(self) -> OptimizationResult:

        lower, upper, x0 = self._bounds_and_x0()
        sigma0 = self.options.get("sigma0", 0.3)
        maxiter = self.options.get("maxiter", 500)
        verbose = self.options.get("verbose", -9)

        if "sigma0" not in self.options:
            ranges = [u - l for l, u in zip(lower, upper)]
            sigma0 = max(ranges) * 0.3

        es = cma.CMAEvolutionStrategy(
            x0,
            sigma0,
            {
                "bounds": [lower, upper],
                "maxiter": maxiter,
                "verbose": verbose,
            },
        )
        while not es.stop():
            solutions = es.ask()
            fitnesses = [self._evaluate(self._decode(s)) for s in solutions]
            es.tell(solutions, fitnesses)

        best_x = self._decode(es.result.xbest)
        return OptimizationResult(
            x=best_x,
            fx=float(es.result.fbest),
            strategy_used="cma_es",
            n_evaluations=self._n_evals,
            converged=not es.stop().get("maxiter", False),
            metadata={"stop_reason": es.stop()},
        )
