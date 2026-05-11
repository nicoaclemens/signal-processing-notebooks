# used by: utils\algorithms\op_search\solver.py, utils\algorithms\op_search\strategies\base.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\diff_ev.py
from dataclasses import dataclass
from typing import Literal, Union, Callable
from .enumbers import _E, DiscreteSpace
import math

Space = Union[_E, DiscreteSpace, tuple[float, float]]


@dataclass
class Parameter:
    name: str
    space: Space
    kind: Literal["discrete", "continuous", "log_continuous"]
    tolerance: float = 0.05

    def is_continuous(self) -> bool:
        return self.kind in ("continuous", "log_continuous")

    def size(self) -> int | float:
        if isinstance(self.space, (list, tuple)) and self.kind == "continuous":
            return float("inf")
        return len(self.space)


from typing import Callable


class Objective:
    def __init__(
        self,
        func: Callable[[dict[str, float]], float],
        minimize: bool = True,
        weight: float = 1.0,
        name: str = "objective",
    ):
        self.func = func
        self.minimize = minimize
        self.weight = weight
        self.name = name

    def evaluate(self, x: dict[str, float]) -> float:
        return self.func(x)


class Problem:

    def __init__(self, parameters: list[Parameter], objectives: list[Objective]):
        self.parameters = parameters
        self.objectives = objectives

        self.traits = self._analyze()

    def evaluate(self, x: dict[str, float]) -> float:
        total = 0.0
        for obj in self.objectives:
            val = obj.evaluate(x)
            total += obj.weight * val
        return total

    def _analyze(self) -> dict:
        traits = {}

        traits["n_params"] = len(self.parameters)

        size = 1
        for p in self.parameters:
            if isinstance(p.space, (DiscreteSpace, _E)):
                size *= len(p.space)
            else:
                size *= float("inf")

        traits["search_space_size"] = size

        discrete = sum(
            isinstance(p.space, (_E, DiscreteSpace)) for p in self.parameters
        )
        traits["discreteness_ratio"] = discrete / len(self.parameters)

        traits["continuous_suitable"] = self._is_continuous_suitable()

        traits["log_suitable"] = self._is_log_suitable()

        traits["constraint_estimate"] = len(self.objectives) - len(self.parameters)

        return traits

    def _is_continuous_suitable(self) -> bool:
        return all(
            p.is_continuous() or isinstance(p.space, (_E, DiscreteSpace))
            for p in self.parameters
        )

    def _is_log_suitable(self) -> bool:
        return any(isinstance(p.space, (_E, DiscreteSpace)) for p in self.parameters)

    def to_continuous_space(self) -> list[tuple[float, float]]:
        bounds = []

        for p in self.parameters:
            if isinstance(p.space, (_E, DiscreteSpace)):
                vals = p.space.values
                bounds.append((math.log(min(vals)), math.log(max(vals))))
            else:
                bounds.append(p.space)

        return bounds

    def summary(self):
        return {
            "n_params": len(self.parameters),
            "traits": self.traits,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.kind,
                    "space_size": len(p.space) if hasattr(p.space, "__len__") else None,
                }
                for p in self.parameters
            ],
        }
