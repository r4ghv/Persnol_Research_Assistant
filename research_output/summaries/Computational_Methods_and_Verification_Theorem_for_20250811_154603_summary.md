# Summary

- **Focus Area**: Optimal portfolio-consumption policies in a multi-asset financial market with n risky assets following Exponential Ornstein-Uhlenbeck processes and one risk-free bond.
  
- **Investor Preferences**: Utilizes Constant Relative Risk Aversion (CRRA) utility with state-dependent stochastic discounting, providing a realistic modeling of investor behavior.

- **Problem Formulation**: The problem is framed as a high-dimensional stochastic optimal control problem, leading to a Hamilton-Jacobi-Bellman (HJB) equation.

- **Mathematical Techniques**: 
  - Applied variable separation technique to convert the HJB equation into a system of ordinary differential equations (ODEs).
  - Developed hybrid numerical methods combining exponential Rosenbrock-type methods with Runge-Kutta methods for solving the ODE system.

- **Verification Theorem**: Established a rigorous verification theorem that offers sufficient conditions for the existence of the value function and admissible optimal control, which can be verified numerically.

- **Performance Evaluation**: Conducted experiments demonstrating that the proposed method surpasses conventional grid-based methods in both accuracy and computational efficiency.

- **Optimal Policy**: The numerically derived optimal policy outperformed all other considered admissible policies, showcasing the effectiveness of the proposed approach.