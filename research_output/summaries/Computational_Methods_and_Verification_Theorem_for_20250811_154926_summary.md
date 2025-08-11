# Summary

- **Focus**: Optimal portfolio-consumption policies in a multi-asset market with n risky assets following Exponential Ornstein-Uhlenbeck processes and one risk-free bond.
  
- **Investor Preferences**: Utilizes Constant Relative Risk Aversion (CRRA) utility with state-dependent stochastic discounting for modeling investor behavior.

- **Problem Formulation**: Defines the optimization problem as a high-dimensional stochastic optimal control problem, with the value function satisfying a Hamilton-Jacobi-Bellman (HJB) equation.

- **Methodology**: 
  - Applies a variable separation technique to convert the HJB equation into a system of ordinary differential equations (ODEs).
  - Proposes hybrid numerical methods combining exponential Rosenbrock-type methods with Runge-Kutta methods for solving the ODE system.

- **Verification Theorem**: Establishes a rigorous verification theorem providing sufficient conditions for the existence of the value function and admissible optimal control, which can be verified numerically.

- **Performance Evaluation**: Conducts experiments showing that the proposed method outperforms conventional grid-based methods in terms of accuracy and computational efficiency.

- **Results**: The numerically derived optimal policy demonstrates superior performance compared to other admissible policies considered in the study.