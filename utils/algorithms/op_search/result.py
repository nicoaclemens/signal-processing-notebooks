# used by: utils\algorithms\op_search\solver.py, utils\algorithms\op_search\strategies\base.py, utils\algorithms\op_search\strategies\brute_force.py, utils\algorithms\op_search\strategies\cma_es.py, utils\algorithms\op_search\strategies\diff_ev.py, utils\algorithms\op_search\strategies\local.py
from dataclasses import dataclass, field


@dataclass
class OptimizationResult:
    x: dict[str, float]
    fx: float
    strategy_used: str
    n_evaluations: int
    converged: bool
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        lines = [
            f"OptimizationResult:",
            f"  strategy : {self.strategy_used}",
            f"  fx       : {self.fx:.6g}",
            f"  evals    : {self.n_evaluations}",
            f"  converged: {self.converged}",
            f"  x        : {self.x}",
        ]
        return "\n".join(lines)
