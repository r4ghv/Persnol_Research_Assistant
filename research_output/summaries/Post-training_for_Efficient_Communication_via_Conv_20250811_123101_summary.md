# Summary

- **Objective**: Develop a post-training process to enhance large language models (LLMs) in forming ad-hoc communication conventions, mimicking human efficiency in multi-turn interactions.

- **Methodology**:
  - Targeted fine-tuning on identified examples of convention formation from human interactions.
  - Introduction of reference planning tokens to improve model reasoning regarding re-mentions.
  - Utilization of preference pairs for DPO-style policy optimization.

- **Evaluation**:
  - Creation of two new benchmarks:
    - A cognitively-motivated interaction benchmark designed to elicit convention formation trends.
    - A document-grounded reference completion task reflecting real-world convention formation.
  
- **Findings**:
  - Post-trained LLMs demonstrated significant improvements in convention formation abilities.
  - Models shortened messages by up to 26% in reference games and improved listener accuracy.
  - Outperformed off-the-shelf models in the document-grounded task.

- **Contributions**:
  - Introduction of new evaluation tasks to assess LLM communicative efficiency without visual stimuli.
  - Evidence that contemporary LLMs lack efficient communication capabilities and a framework to enhance this ability.
  - Establishment of a foundation for future research on improving LLMs' communication efficiency. 

- **Publication**: Presented at COLM 2025, with code available for further research.