# Summary

- **Objective**: Improve chart understanding capabilities in multimodal large language models (MLLMs) by synthesizing effective training data.
  
- **Problem Addressed**: Existing MLLMs show low performance (30%-50%) on chart understanding benchmarks due to inadequate similarity of synthetic charts to real-world data.

- **Proposed Solution**: A five-step data synthesis pipeline that:
  - Modularizes chart generation.
  - Diversifies visual details.
  - Separates data and function creation for single plots.
  - Conditions multi-subplot generation on earlier subplots.
  - Filters out low-quality data.
  - Generates question-answer (QA) pairs using GPT-4o.

- **Dataset Creation**: Introduced the Effective Chart Dataset (ECD) comprising:
  - 10,000+ chart images.
  - 300,000+ QA pairs.
  - Coverage of 25 topics and over 250 chart type combinations with high visual complexity.

- **Results**: ECD consistently improves MLLM performance across various real-world and synthetic test sets compared to existing datasets.

- **Availability**: Code, data, and models are publicly accessible at the provided GitHub link.

- **Collaborators**: Research conducted by a team from Australian National University, Ohio State University, Cisco, and Johns Hopkins University.