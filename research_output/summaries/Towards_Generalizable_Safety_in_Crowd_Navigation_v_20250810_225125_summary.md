# Summary

- **Problem Addressed**: Mobile robots trained with reinforcement learning often struggle in out-of-distribution (OOD) scenarios, leading to performance degradation in crowd navigation.

- **Proposed Solution**: Introduced a method that incorporates prediction uncertainty estimates from adaptive conformal inference to enhance robot navigation policies, making them robust to distribution shifts.

- **Key Innovations**:
  - **Adaptive Conformal Inference**: Utilizes this technique to quantify uncertainties in human trajectory predictions, allowing the robot to adapt to dynamic crowd behaviors.
  - **Constrained Reinforcement Learning (CRL)**: Guides the agent's behavior using uncertainty estimates, improving decision-making under uncertainty.

- **Performance Metrics**:
  - Achieved a **96.93% success rate** in in-distribution settings, surpassing previous state-of-the-art by **8.80%**.
  - Demonstrated **3.72 times fewer collisions** and **2.43 times fewer intrusions** into human trajectories compared to prior methods.

- **Robustness in OOD Scenarios**: Showed significant resilience against distribution shifts in velocity, policy changes, and transitions from individual to group dynamics, outperforming competing approaches.

- **Real-World Deployment**: Successfully implemented the method on a real robot, demonstrating safe navigation capabilities in both sparse and dense crowds.

- **Availability**: Code and demonstration videos are publicly accessible at https://gen-safe-nav.github.io/.