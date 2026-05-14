# used by: utils\algorithms\op_search\strategies\bayesian.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\cma_es.py, utils\algorithms\op_search\strategies\diff_ev.py, utils\algorithms\op_search\strategies\local.py, utils\algorithms\op_search\strategies\simulated_annealing.py
from abc import ABC, abstractmethod
import time
from ..problem import Problem
from ..result import OptimizationResult


class Strategy(ABC):

    def __init__(self, problem: Problem, options: dict):
        self.problem = problem
        self.options = options
        self._n_evals = 0
        self._fx_history: list[float] = []
        self._objective_history: list[list[float]] = []
        self._elapsed_history: list[float] = []
        self._start_time = time.perf_counter()

    def _evaluate(self, x: dict[str, float]) -> float:
        self._n_evals += 1
        objective_values = [obj.evaluate(x) for obj in self.problem.objectives]
        self._objective_history.append(objective_values)
        fx = self.problem.evaluate(x)
        self._fx_history.append(fx)
        self._elapsed_history.append(time.perf_counter() - self._start_time)

        callback = self.options.get("evaluation_callback")
        if callback is not None:
            callback(self._n_evals, fx)

        return fx

    @abstractmethod
    def run(self) -> OptimizationResult: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__
