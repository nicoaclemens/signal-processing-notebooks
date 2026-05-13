# used by: tests\op_search\test_op_search.py, utils\algorithms\op_search\problem.py, utils\algorithms\op_search\strategies\bayesian.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\cma_es.py, utils\algorithms\op_search\strategies\diff_ev.py, utils\algorithms\op_search\strategies\local.py, utils\algorithms\op_search\strategies\simulated_annealing.py
from abc import ABC
import math

_E3_NUMBERS = [1.0, 2.2, 4.7]
_E6_NUMBERS = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]
_E12_NUMBERS = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
_E24_NUMBERS = [
    1.0,
    1.1,
    1.2,
    1.3,
    1.5,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.7,
    3.0,
    3.3,
    3.6,
    3.9,
    4.3,
    4.7,
    5.1,
    5.6,
    6.2,
    6.8,
    7.5,
    8.2,
    9.1,
]
_E48_NUMBERS = [
    1.00,
    1.05,
    1.10,
    1.15,
    1.21,
    1.27,
    1.33,
    1.40,
    1.47,
    1.54,
    1.62,
    1.69,
    1.78,
    1.87,
    1.96,
    2.05,
    2.15,
    2.26,
    2.37,
    2.49,
    2.61,
    2.74,
    2.87,
    3.01,
    3.16,
    3.32,
    3.48,
    3.65,
    3.83,
    4.02,
    4.22,
    4.42,
    4.64,
    4.87,
    5.11,
    5.36,
    5.62,
    5.90,
    6.19,
    6.49,
    6.81,
    7.15,
    7.50,
    7.87,
    8.25,
    8.66,
    9.09,
    9.53,
]


class _E(ABC):

    _BASE_VALUES: list[float] = []

    def __init__(self, min_val: float, max_val: float) -> None:
        if min_val <= 0 or max_val <= 0:
            raise ValueError(
                "min_val and max_val must be positive (component values are positive)."
            )
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val}).")

        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self._values: list[float] = self._generate_values()

        if not self._values:
            raise ValueError(
                f"No {self.__class__.__name__} values found in range "
                f"[{min_val}, {max_val}]. Try widening the range."
            )

    def _generate_values(self) -> list[float]:

        tol = 1e-9

        exp_min = math.floor(math.log10(self.min_val))
        exp_max = math.floor(math.log10(self.max_val))

        seen: set[float] = set()
        values: list[float] = []

        for exp in range(exp_min - 1, exp_max + 2):
            decade = 10.0**exp
            for base in self._BASE_VALUES:
                v = round(base * decade, 12)
                if self.min_val * (1 - tol) <= v <= self.max_val * (1 + tol):
                    if v not in seen:
                        seen.add(v)
                        values.append(v)

        values.sort()
        return values

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int | slice) -> float | list[float]:
        if isinstance(index, slice):
            return self._values[index]
        return self._values[index]

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value: object) -> bool:
        return value in self._values

    def snap(self, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be positive.")
        log_v = math.log(value)
        return min(self._values, key=lambda x: abs(math.log(x) - log_v))

    def index_of(self, value: float) -> int:
        try:
            return self._values.index(value)
        except ValueError:
            raise ValueError(
                f"{value} is not a valid {self.__class__.__name__} value in this range."
            )

    def snap_to_index(self, value: float) -> int:
        return self.index_of(self.snap(value))

    @property
    def values(self) -> list[float]:
        return list(self._values)

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return (
            f"{name}(min_val={self.min_val}, max_val={self.max_val}, "
            f"n={len(self)}, first={self._values[0]}, last={self._values[-1]})"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self._values == other._values


class E3(_E):
    _BASE_VALUES = _E3_NUMBERS


class E6(_E):
    _BASE_VALUES = _E6_NUMBERS


class E12(_E):
    _BASE_VALUES = _E12_NUMBERS


class E24(_E):
    _BASE_VALUES = _E24_NUMBERS


class E48(_E):
    _BASE_VALUES = _E48_NUMBERS


class DiscreteSpace:

    def __init__(
        self,
        values: list[float] | None = None,
        *,
        min_val: float | None = None,
        max_val: float | None = None,
        n: int | None = None,
    ) -> None:
        if values is not None:
            if not values:
                raise ValueError("values must not be empty.")
            self._values = sorted(float(v) for v in values)
        elif min_val is not None and max_val is not None and n is not None:
            if min_val <= 0 or max_val <= 0:
                raise ValueError(
                    "min_val and max_val must be positive for log-spacing."
                )
            if min_val > max_val:
                raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val}).")
            if n < 1:
                raise ValueError("n must be at least 1.")
            log_min = math.log(min_val)
            log_max = math.log(max_val)
            self._values = (
                [
                    math.exp(log_min + i * (log_max - log_min) / (n - 1))
                    for i in range(n)
                ]
                if n > 1
                else [float(min_val)]
            )
        else:
            raise TypeError(
                "Provide either a 'values' list, "
                "or all three of min_val, max_val, and n."
            )

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, index: int | slice) -> float | list[float]:
        if isinstance(index, slice):
            return self._values[index]
        return self._values[index]

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value: object) -> bool:
        return value in self._values

    def snap(self, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be positive.")
        log_v = math.log(value)
        return min(self._values, key=lambda x: abs(math.log(x) - log_v))

    def index_of(self, value: float) -> int:
        try:
            return self._values.index(value)
        except ValueError:
            raise ValueError(f"{value} is not a value in this DiscreteSpace.")

    def snap_to_index(self, value: float) -> int:
        return self.index_of(self.snap(value))

    @property
    def values(self) -> list[float]:
        return list(self._values)

    def __repr__(self) -> str:
        return (
            f"DiscreteSpace(n={len(self)}, "
            f"first={self._values[0]}, last={self._values[-1]})"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DiscreteSpace) and self._values == other._values
