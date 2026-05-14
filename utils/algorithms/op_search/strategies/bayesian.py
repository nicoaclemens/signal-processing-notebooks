# used by: utils\algorithms\op_search\solver.py
# Lightweight Bayesian Optimization using Expected Improvement
import math
import numpy as np
from ..result import OptimizationResult
from ..enumbers import _E, DiscreteSpace
from .base import Strategy

# Runtime Scaling: O((n_initial + n_iterations) * n^3) for GP fitting
# Initial random sampling: O(n_initial). Iterative refinement with GP model fitting ~O(n^3).
# Best for low-dim (n <= 15), mixed discrete/continuous problems with expensive objectives.


class BayesianOptimization(Strategy):

    def run(self) -> OptimizationResult:
        n_initial = self.options.get(
            "n_initial", max(5, 2 * len(self.problem.parameters))
        )
        n_iterations = self.options.get("n_iterations", 20)
        maxiter = self.options.get("maxiter", n_initial + n_iterations)
        seed = self.options.get("seed", None)

        if seed is not None:
            np.random.seed(seed)

        bounds = self._get_bounds()
        x_list, fx_list = [], []

        for _ in range(min(n_initial, maxiter)):
            x_candidate = self._random_point(bounds)
            x_dict = self._decode(x_candidate)
            fx = self._evaluate(x_dict)
            x_list.append(x_candidate)
            fx_list.append(fx)

        best_x = x_list[np.argmin(fx_list)]
        best_fx = min(fx_list)
        try:
            gp = self._build_gp(np.array(x_list), np.array(fx_list))
            use_gp = gp is not None
        except Exception:
            use_gp = False

        for _ in range(n_iterations):
            if self._n_evals >= maxiter:
                break

            if use_gp:
                x_candidate = self._next_point_gp(gp, bounds, x_list, fx_list)
            else:
                x_candidate = self._next_point_random(bounds)

            x_dict = self._decode(x_candidate)
            fx = self._evaluate(x_dict)
            x_list.append(x_candidate)
            fx_list.append(fx)

            if fx < best_fx:
                best_fx = fx
                best_x = x_candidate

        best_x_dict = self._decode(best_x)
        return OptimizationResult(
            x=best_x_dict,
            fx=best_fx,
            strategy_used="bayesian_optimization",
            n_evaluations=self._n_evals,
            converged=True,
            metadata={"n_initial": n_initial, "n_iterations": len(x_list) - n_initial},
        )

    def _get_bounds(self) -> list[tuple[float, float]]:
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
        return bounds

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

    def _random_point(self, bounds: list[tuple[float, float]]) -> np.ndarray:
        return np.array([np.random.uniform(lo, hi) for lo, hi in bounds])

    def _build_gp(self, X: np.ndarray, y: np.ndarray):
        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import RBF, ConstantKernel

            kernel = ConstantKernel(1.0) * RBF(1.0)
            gp = GaussianProcessRegressor(
                kernel=kernel, n_restarts_optimizer=5, alpha=1e-6
            )
            gp.fit(X, y)
            return gp
        except ImportError:
            return None

    def _next_point_gp(
        self, gp, bounds: list[tuple[float, float]], X_list: list, y_list: list
    ) -> np.ndarray:
        best_y = min(y_list)
        n_candidates = 100

        candidates = np.array([self._random_point(bounds) for _ in range(n_candidates)])
        y_pred, y_std = gp.predict(candidates, return_std=True)

        ei = np.zeros(n_candidates)
        for i in range(n_candidates):
            if y_std[i] > 1e-6:
                z = (best_y - y_pred[i]) / y_std[i]
                ei[i] = (best_y - y_pred[i]) * self._norm_cdf(z) + y_std[
                    i
                ] * self._norm_pdf(z)
            else:
                ei[i] = 0.0

        best_idx = np.argmax(ei)
        return candidates[best_idx]

    def _next_point_random(self, bounds: list[tuple[float, float]]) -> np.ndarray:
        return self._random_point(bounds)

    @staticmethod
    def _norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @staticmethod
    def _norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
