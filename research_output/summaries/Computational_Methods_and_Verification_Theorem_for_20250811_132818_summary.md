# Summary

- **Focus Area**: Optimal portfolio-consumption policies in a multi-asset financial market with n risky assets following Exponential Ornstein-Uhlenbeck processes and one risk-free bond.
- **Investor Preferences**: Modeled using Constant Relative Risk Aversion (CRRA) utility with state-dependent stochastic discounting.
- **Problem Formulation**: High-dimensional stochastic optimal control problem; value function satisfies Hamilton-Jacobi-Bellman (HJB) equation as a necessary optimality condition.
- **Methodology**: 
  - Applied variable separation technique to transform HJB equation into a system of ordinary differential equations (ODEs).
  - Developed hybrid numerical methods integrating exponential Rosenbrock-type methods with Runge-Kutta methods for solving the ODE system.
- **Verification Theorem**: Established a rigorous verification theorem providing sufficient conditions for the existence of the value function and admissible optimal control, enabling numerical verification.
- **Performance Evaluation**: Conducted experiments demonstrating that the proposed method outperforms conventional grid-based methods in accuracy and computational cost.
- **Results**: The numerically derived optimal policy showed superior performance compared to all other considered admissible policies.