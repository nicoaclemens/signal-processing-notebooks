# used by: tests\op_search\test_op_search.py, utils\algorithms\op_search\solver.py, utils\algorithms\op_search\strategies\base.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\diff_ev.py, utils\algorithms\op_search\visualization.py
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

    _VALID_KINDS = ("discrete", "continuous", "log_continuous")

    def __post_init__(self) -> None:
        if self.tolerance < 0:
            raise ValueError("tolerance must be >= 0.")

        if self.kind not in self._VALID_KINDS:
            raise ValueError(
                f"Invalid kind '{self.kind}'. Expected one of: {self._VALID_KINDS}."
            )

        if self.kind == "discrete":
            if not isinstance(self.space, (_E, DiscreteSpace)):
                raise TypeError(
                    "Discrete parameters require DiscreteSpace or E-series space."
                )
            return

        if not (
            isinstance(self.space, tuple)
            and len(self.space) == 2
            and all(isinstance(v, (int, float)) for v in self.space)
        ):
            raise TypeError("Continuous parameters require a bounds tuple (low, high).")

        lo, hi = float(self.space[0]), float(self.space[1])
        if lo >= hi:
            raise ValueError(f"Invalid bounds for '{self.name}': low must be < high.")

        if self.kind == "log_continuous" and (lo <= 0 or hi <= 0):
            raise ValueError("log_continuous bounds must be positive.")

    def is_continuous(self) -> bool:
        return self.kind in ("continuous", "log_continuous")

    def size(self) -> int | float:
        if self.is_continuous():
            return float("inf")
        return len(self.space)


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
        if not parameters:
            raise ValueError("Problem requires at least one parameter.")
        if not objectives:
            raise ValueError("Problem requires at least one objective.")

        self.parameters = parameters
        self.objectives = objectives

        self.traits = self._analyze()

    def evaluate(self, x: dict[str, float]) -> float:
        total = 0.0
        for obj in self.objectives:
            val = obj.evaluate(x)
            signed = val if obj.minimize else -val
            total += obj.weight * signed
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

        discrete = sum(p.kind == "discrete" for p in self.parameters)
        traits["discreteness_ratio"] = discrete / len(self.parameters)

        traits["continuous_suitable"] = self._is_continuous_suitable()

        traits["log_suitable"] = self._is_log_suitable()
        traits["n_objectives"] = len(self.objectives)

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
                    "space_size": len(p.space) if p.kind == "discrete" else None,
                }
                for p in self.parameters
            ],
        }
