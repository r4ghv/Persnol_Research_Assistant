# Summary

- **Objective**: Enhance chart understanding capabilities in multimodal large language models (MLLMs) through effective training data synthesis.
  
- **Problem Addressed**: Existing MLLMs struggle with a 30%-50% success rate on chart understanding benchmarks, largely due to inadequate synthetic chart data.

- **Innovative Approach**: Developed a five-step data synthesis pipeline that:
  - Modularizes chart generation.
  - Conditions multi-subplot generation on earlier plots.
  - Diversifies visual details in generated charts.
  - Filters out low-quality data.
  - Generates question-answer (QA) pairs using GPT-4o.

- **Dataset Creation**: Introduced the Effective Chart Dataset (ECD) comprising:
  - Over 10,000 chart images.
  - More than 300,000 QA pairs.
  - Coverage of 25 topics and 250+ chart type combinations with high visual complexity.

- **Performance Improvement**: Demonstrated that fine-tuning MLLMs with ECD significantly enhances their performance on real-world and synthetic test sets compared to existing datasets.

- **Availability**: Code, data, and models are publicly accessible at [GitHub](https://github.com/yuweiyang-anu/ECD).

- **Collaborative Effort**: Research conducted by a team from Australian National University, Ohio State University, Cisco, and Johns Hopkins University, supported by various research grants.