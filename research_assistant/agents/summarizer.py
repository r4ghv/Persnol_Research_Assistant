from openai import OpenAI
from typing import List
import time
import logging

from .preprocessor import preprocess_and_chunk

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2

    def summarize(
        self, title: str, abstract: str, content: str,
        style: str = "bullet_points",
    ) -> str:
        """Preprocess + chunk the PDF text, then summarize via OpenAI."""
        chunks = preprocess_and_chunk(content)
        user_prompt = self._build_chunked_prompt(title, abstract, chunks)
        system_prompt = self._get_system_prompt(style)

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))

    def _get_system_prompt(self, style: str) -> str:
        prompts = {
            "bullet_points": "Provide a concise bullet-point summary focusing on key contributions, methods, and results. Base your summary on ALL sections provided, not just the abstract.",
            "paragraph": "Write a 150-word paragraph summarizing the paper's main points. Incorporate details from the full paper content, not just the abstract.",
            "technical": "Create a detailed technical summary including methodology, architecture, experimental setup, and key results. Use the full paper content provided.",
        }
        return prompts.get(style, prompts["bullet_points"])

    def _build_chunked_prompt(
        self, title: str, abstract: str, chunks: List[str],
    ) -> str:
        header = f"Title: {title}\nAbstract: {abstract}\n\nPaper Contents:\n"

        if not chunks:
            return header + "[No extractable content beyond abstract]"

        body = "\n\n".join(chunks)
        # Truncate to ~8000 chars total keeping full chunks
        max_body = 7800
        if len(body) > max_body:
            truncated = []
            current = 0
            for c in chunks:
                if current + len(c) + 2 > max_body:
                    break
                truncated.append(c)
                current += len(c) + 2
            body = "\n\n".join(truncated)

        return header + body
