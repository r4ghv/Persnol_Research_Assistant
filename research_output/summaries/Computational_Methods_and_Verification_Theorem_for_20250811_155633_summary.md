# Summary

- **Focus**: Investigates optimal portfolio-consumption policies in a multi-asset market with risky assets modeled by Exponential Ornstein-Uhlenbeck processes and one risk-free bond.

- **Investor Preferences**: Utilizes Constant Relative Risk Aversion (CRRA) utility with state-dependent stochastic discounting to model investor behavior.

- **Problem Formulation**: Formulates the optimization problem as a high-dimensional stochastic optimal control problem, leading to a Hamilton-Jacobi-Bellman (HJB) equation.

- **Methodology**: 
  - Applies a variable separation technique to convert the HJB equation into a system of ordinary differential equations (ODEs).
  - Proposes hybrid numerical methods combining exponential Rosenbrock-type methods with Runge-Kutta methods for solving the ODE system.

- **Verification Theorem**: Establishes a rigorous verification theorem that provides sufficient conditions for the existence of the value function and admissible optimal control, allowing for numerical verification.

- **Performance Evaluation**: Conducts experiments demonstrating that the proposed method surpasses conventional grid-based methods in terms of accuracy and computational efficiency.

- **Results**: The numerically derived optimal policy outperforms all other considered admissible policies, showcasing the effectiveness of the proposed approach in real-world financial optimization problems.