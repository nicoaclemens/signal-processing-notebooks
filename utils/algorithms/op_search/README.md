# op_search: Circuit Optimization Solver

Auto-selects best search strategy based on problem structure.
All strategies respect discrete, continuous, and log-continuous parameters.

## Strategy Selection (auto mode)

| Problem Type                          | Selected Strategy      |
| ------------------------------------- | ---------------------- |
| All discrete, small space             | brute_force            |
| All continuous, <= 6 params           | nelder_mead            |
| Mixed, continuous-heavy, <= 15 params | bayesian_optimization  |
| Mixed, discrete-heavy, <= 30 params   | simulated_annealing    |
| Continuous, <= 30 params              | differential_evolution |
| Any, > 30 params                      | cma_es                 |

## Configuration

```python
from utils.algorithms.op_search import Problem, Parameter, Solver, SolverConfig

problem = Problem(parameters=[...], objectives=[...])

# Auto strategy selection
solver = Solver(problem)
result = solver.solve()

# Override strategy
config = SolverConfig(
    strategy="bayesian_optimization",
    max_evaluations=50,
    verbose=True
)
solver = Solver(problem, config)
result = solver.solve()
```

## Visualization

```python
config = SolverConfig(verbose=True)
solver = Solver(problem, config)
result = solver.solve()
```

### Progress Bar

Use solve_with_progress() for tqdm-based progress tracking (requires tqdm):

```python
config = SolverConfig(max_evaluations=1000)
solver = Solver(problem, config)
result = solver.solve_with_progress(desc="Circuit optimization")
```

### Plotting Results

requires mpl

```python
from utils.algorithms.op_search import SolverVisualizer

config = SolverConfig(verbose=True)
solver = Solver(problem, config)
result = solver.solve()

viz = SolverVisualizer(problem, verbose=False)
viz.plot_result(result, show=True)  # bar chart of final parameter values
viz.plot_convergence(result.n_evaluations, result.fx, show=True)  # convergence summary
```

### Manual Visualization

```python
viz = SolverVisualizer(problem, verbose=True)
viz.print_analysis(strategy_name, options_dict)
viz.print_result(result)
viz.plot_result(result, save_path="optimization_result.png")
```
