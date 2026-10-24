# Summary

**Summary of SocietyBench: Forecasting Counterfactual Social-World Evolution**

**Key Contributions:**
- Introduction of **SocietyBench**, an innovative benchmark aimed at evaluating the forecasting capabilities of large language models (LLMs) in understanding the evolution of real social events.
- Development of an automated pipeline that collects web news and social media posts from five platforms, creating a **date-indexed timeline** that separates factual events from public opinion, addressing the limitations of existing benchmarks.
- Implementation of a **three-phase anonymization procedure** that alters named entities and shifts dates to construct a counterfactual social world, ensuring that models cannot rely on pre-training memory and must focus on genuine forecasting.
- Establishment of a dual-axis scoring system measuring **probability calibration** and **temporal accuracy** on a 100-point scale, allowing for a nuanced evaluation of model performance.
- Evaluation of six frontier LLMs, three agent frameworks, and two model-free heuristics across 125 prediction points in both Chinese and English editions, covering diverse events such as public controversy, geopolitics, technology policy, financial markets, and trade policy.

**Methods:**
- **Data Collection:** Aggregation of news articles and social media posts to create comprehensive timelines for each event, ensuring a real-world distribution of data.
- **Anonymization Process:** The timeline's entities and dates are modified to prevent models from recognizing original events, thus focusing on their forecasting capabilities rather than mere recall.
- **Scoring Metrics:** Questions derived from the timelines are evaluated on two orthogonal axes:
  - **Probability Calibration:** The alignment of predicted probabilities with actual outcomes.
  - **Temporal Accuracy:** The correctness of the predicted timing of events.

**Results:**
- The strongest LLM achieved a score of **75.0 out of 100**, significantly above a trivial anchor of 50, indicating some forecasting ability while also highlighting inherent limitations.
- The two scoring axes (calibration and accuracy) often dissociated, with models demonstrating strengths in one area but weaknesses in another.
- Notable gaps of up to **21.4 points** on a single axis for specific events underscore the necessity of evaluating models across multiple events for a reliable assessment.
- All anonymized timelines, question banks, ground truth data, and scoring code have been made publicly available to foster further research and benchmarking.

**Conclusion:**
SocietyBench offers a novel framework for assessing the forecasting capabilities of LLMs in social contexts, emphasizing the critical need to understand both factual and opinion-based dynamics in social events.

###