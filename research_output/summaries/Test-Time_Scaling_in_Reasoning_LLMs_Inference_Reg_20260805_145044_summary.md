# Summary

- **Key Contributions**:
  - Formalization of test-time scaling as budgeted inference over the implicit prefix tree of autoregressive models, emphasizing the diversity of inference algorithms.
  - Identification of three structural regimes of inference: single-trajectory sequential scaling, leaf-level scaling with terminal reduction, and prefix-level scaling, each with distinct implications for performance and failure modes.
  - Development of evaluation principles that clearly differentiate between end-to-end system performance and candidate-bank diagnostics, including the need for precise definitions and measurements.
  - Introduction of an evaluation profile designed to recover or bound common repeated-sampling metrics, enhancing the rigor of performance assessment.
  - Specification of reproducibility requirements for inference protocols, distinguishing between exact replay and distributional reproducibility, and detailing the necessary artifacts for each.
  - Organization of the open-weight reasoning ecosystem by model-side and interface mechanisms, facilitating a clearer understanding of the landscape.

- **Methods**:
  - A systematic account of test-time scaling along three axes: structural regimes, evaluation principles, and reproducibility requirements, with a focus on their implications for LLM performance.
  - Application of these principles to a variety of benchmarks, including broad-knowledge, symbolic-reasoning, and competition-mathematics, to illustrate their practical relevance.
  - Assembly and release of over 2 billion full reasoning traces, enriched with verifier and token-level signals, to support further research and validation.

- **Results**:
  - Enhanced understanding of the statistical structure, compute accounting, and failure modes of different inference algorithms, highlighting their impact on LLM performance.
  - Clear guidelines for reporting compute and uncertainty in relation to specific inference protocols, addressing the variability and biases in evaluation metrics.
  - Improved comparability of results across studies by clarifying the implications of treating inference procedures as interchangeable under a single scalar budget.
  - Establishment of a comprehensive framework for evaluating reasoning capabilities in large language models, which facilitates future research and enhances reproducibility.