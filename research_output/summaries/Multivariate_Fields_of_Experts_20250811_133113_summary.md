# Summary

- **Introduction of Multivariate Fields of Experts (MFoE)**: A new framework for learning image priors that generalizes existing fields of experts methods.
- **Incorporation of Multivariate Potential Functions**: Utilizes Moreau envelopes of the ℓ∞-norm to construct these functions.
- **Performance Across Inverse Problems**: Demonstrated effectiveness in various applications including image denoising, deblurring, compressed-sensing MRI, and computed tomography.
- **Comparison with Univariate Models**: MFoE outperforms comparable univariate models while being faster, requiring fewer parameters, and needing less training data.
- **Interpretability**: Maintains a high level of interpretability due to its structured design.
- **Extension of Weakly Convex Ridge Regularizer (WCRR)**: Introduces parametric potentials that closely replicate spline-based potentials from WCRR and extends it to a multivariate context.
- **Parametric Framework**: Provides a simple parametric form for potential functions, enhancing the expressivity of the model.
- **Computational Efficiency**: Achieves performance comparable to deep learning-based regularizers with significantly reduced computational overhead.