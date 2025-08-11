# Summary

- **Objective**: Improve chart understanding in multimodal large language models (MLLMs) for scientific plots.
  
- **Problem Identification**: Existing MLLMs achieve only 30%-50% success on benchmarks due to inadequate training data similarity to real charts.

- **Innovative Approach**: Developed a five-step data synthesis pipeline:
  - Modularized chart generation.
  - Conditioned multi-subplot generation on previous subplots.
  - Diversified visual details of generated charts.
  - Filtered low-quality data.
  - Generated question-answer (QA) pairs using GPT-4o.

- **Dataset Creation**: Introduced the Effective Chart Dataset (ECD):
  - Contains over 10,000 chart images and 300,000 QA pairs.
  - Covers 25 topics and includes 250+ chart type combinations with high visual complexity.

- **Performance Improvement**: ECD consistently enhances MLLM performance across various real-world and synthetic test sets.

- **Availability**: Code, data, and models are publicly accessible on GitHub.

- **Collaborative Effort**: Involvement of researchers from multiple institutions, including Australian National University, Ohio State University, Cisco, and Johns Hopkins University. 

- **Funding Acknowledgment**: Supported by the Australian Research Council and the National Science Foundation.