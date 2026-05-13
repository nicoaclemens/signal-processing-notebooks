# used by: utils\algorithms\op_search\strategies\bayesian.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\cma_es.py, utils\algorithms\op_search\strategies\diff_ev.py, utils\algorithms\op_search\strategies\local.py, utils\algorithms\op_search\strategies\simulated_annealing.py
from abc import ABC, abstractmethod
from ..problem import Problem
from ..result import OptimizationResult


class Strategy(ABC):

    def __init__(self, problem: Problem, options: dict):
        self.problem = problem
        self.options = options
        self._n_evals = 0
        self._fx_history: list[float] = []

    def _evaluate(self, x: dict[str, float]) -> float:
        self._n_evals += 1
        fx = self.problem.evaluate(x)
        self._fx_history.append(fx)
        return fx

    @abstractmethod
    def run(self) -> OptimizationResult: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__
