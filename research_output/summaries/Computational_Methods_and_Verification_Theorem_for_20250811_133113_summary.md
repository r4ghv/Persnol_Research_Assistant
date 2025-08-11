# Summary

- **Focus of Study**: Optimal portfolio-consumption policies in a multi-asset financial market with n risky assets following Exponential Ornstein-Uhlenbeck processes and one risk-free bond.
  
- **Investor Preferences**: Modeled using Constant Relative Risk Aversion (CRRA) utility with state-dependent stochastic discounting.

- **Formulation**: The problem is framed as a high-dimensional stochastic optimal control problem, with the value function satisfying a Hamilton-Jacobi-Bellman (HJB) equation.

- **Methodology**:
  - Applied variable separation technique to convert the HJB equation into a system of ordinary differential equations (ODEs).
  - Developed hybrid numerical methods combining exponential Rosenbrock-type methods with Runge-Kutta methods for solving the ODE system.

- **Verification Theorem**: Established a rigorous verification theorem providing sufficient conditions for the existence of the value function and admissible optimal control, which can be verified numerically.

- **Performance Evaluation**: Conducted experiments showing that the proposed method surpasses conventional grid-based methods in accuracy and computational efficiency.

- **Optimal Policy**: The numerically derived optimal policy demonstrated superior performance compared to other admissible policies considered.