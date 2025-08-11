# Summary

- **Introduction of Multivariate Fields of Experts (MFoE)**: A new framework for learning image priors that generalizes existing fields of experts methods.
- **Incorporation of Multivariate Potential Functions**: Utilizes Moreau envelopes of the ℓ∞-norm to construct multivariate potentials.
- **Performance Across Inverse Problems**: Demonstrated effectiveness in various applications including image denoising, deblurring, compressed-sensing MRI, and computed tomography.
- **Comparison with Existing Models**: Outperforms univariate models and achieves performance comparable to deep-learning-based regularizers, while being faster, requiring fewer parameters, and needing less training data.
- **High Interpretability**: Maintains a structured design that allows for a relatively high level of interpretability in the model.
- **Extension of Weakly Convex Ridge Regularizer (WCRR)**: Introduces parametric potentials that closely replicate spline-based potentials from WCRR and extends it to a multivariate context.
- **Mathematical Foundations**: Establishes a connection between the proposed model and established mathematical concepts such as the Moreau envelope and proximal operators.