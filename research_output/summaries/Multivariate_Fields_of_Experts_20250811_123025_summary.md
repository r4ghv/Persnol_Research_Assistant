# Summary

**Key Contributions of the Multivariate Fields of Experts Framework:**

- **Introduction of Multivariate Fields of Experts (MFoE):** A novel framework for learning image priors that extends traditional fields of experts methods by using multivariate potential functions.

- **Utilization of Moreau Envelopes:** Incorporates Moreau envelopes of the ℓ∞-norm to construct multivariate potentials, enhancing the expressiveness of the model.

- **Performance Across Inverse Problems:** Demonstrates effectiveness in various applications including:
  - Image denoising
  - Image deblurring
  - Compressed-sensing magnetic-resonance imaging (CS-MRI)
  - Computed tomography (CT)

- **Comparison with Existing Models:** Outperforms univariate models and achieves performance comparable to deep-learning-based regularizers while being:
  - Significantly faster
  - Requiring fewer parameters
  - Needing less training data

- **High Interpretability:** Maintains a structured design that allows for a relatively high level of interpretability compared to other complex models.

- **Extension of Weakly Convex Ridge Regularizer (WCRR):** Generalizes WCRR to the multivariate setting, effectively approximating spline-based potentials with a simpler parametric form.

- **Bilevel Optimization Framework:** Adopts a bilevel optimization approach for training, enhancing the learning of regularizers in the context of image reconstruction.