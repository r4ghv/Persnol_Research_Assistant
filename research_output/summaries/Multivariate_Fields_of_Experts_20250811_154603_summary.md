# Summary

- **Introduction of Multivariate Fields of Experts (MFoE)**: A new framework for learning image priors that generalizes existing fields of experts methods.
  
- **Incorporation of Multivariate Potential Functions**: Utilizes Moreau envelopes of the ℓ∞-norm to construct multivariate potentials, enhancing the expressiveness of the model.

- **Performance Across Inverse Problems**: Demonstrated effectiveness in various applications including image denoising, deblurring, compressed-sensing MRI, and computed tomography.

- **Comparison with Existing Models**: Outperforms univariate models and approaches the performance of deep learning-based regularizers while being faster, requiring fewer parameters, and needing less training data.

- **High Interpretability**: Maintains a structured design that allows for a relatively high level of interpretability compared to more complex models.

- **Extension of Weakly Convex Ridge Regularizer (WCRR)**: Introduces parametric potentials that closely replicate spline-based potentials from WCRR and extends it to the multivariate context.

- **Innovative Use of Moreau Envelopes**: Employs Moreau envelopes to define regularizers that enhance the reconstruction quality in inverse problems.

- **Computational Efficiency**: Achieves significant computational advantages in both training and inference compared to deep learning methods, making it suitable for practical applications.