# Summary

- **Objective**: Improve chart understanding in multimodal large language models (MLLMs) through effective training data synthesis.
  
- **Problem Identification**: Existing MLLMs show low success rates (30%-50%) on benchmarks due to inadequate training data that lacks similarity to real-world charts.

- **Proposed Solution**: 
  - Developed a five-step data synthesis pipeline:
    1. Separate data and function creation for single plot generation.
    2. Condition multi-subplot generation on prior subplots.
    3. Diversify visual details in generated figures.
    4. Filter out low-quality data.
    5. Generate question-answer (QA) pairs using GPT-4o.
  
- **Dataset Creation**: Introduced the Effective Chart Dataset (ECD) with:
  - 10,000+ chart images.
  - 300,000+ QA pairs.
  - Coverage of 25 topics and over 250 chart type combinations with high visual complexity.

- **Performance Improvement**: ECD consistently enhances the performance of various MLLMs across real-world and synthetic test sets.

- **Availability**: Code, data, and models are publicly accessible at the provided GitHub link.

- **Research Support**: Acknowledged funding from the Australian Research Council and the National Science Foundation.