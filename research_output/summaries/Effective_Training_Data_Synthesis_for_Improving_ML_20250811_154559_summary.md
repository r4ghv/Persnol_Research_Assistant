# Summary

- **Objective**: Enhance chart understanding in multimodal large language models (MLLMs) through effective training data synthesis.
- **Problem Identification**: Existing MLLMs exhibit low success rates (30%-50%) on benchmarks due to inadequate training data similarity to real charts.
- **Innovative Approach**: Developed a five-step data synthesis pipeline:
  - Modularized chart generation.
  - Conditioned multi-subplot generation on previous subplots.
  - Diversified visual details in generated charts.
  - Filtered out low-quality data.
  - Generated question-answer (QA) pairs using GPT-4o.
- **Dataset Creation**: Introduced the Effective Chart Dataset (ECD) with:
  - 10,000+ chart images.
  - 300,000+ QA pairs.
  - Coverage of 25 topics and 250+ chart type combinations with high visual complexity.
- **Results**: ECD significantly improved MLLM performance on various real-world and synthetic test sets compared to existing datasets.
- **Availability**: Code, data, and models are publicly accessible at GitHub.
- **Collaborative Support**: Research supported by the Australian Research Council and the National Science Foundation.