from openai import OpenAI
from typing import List, Optional
import time
import logging

class Summarizer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2  # Initial delay in seconds
    
    def summarize(self, title: str, abstract: str, content: str, 
                 style: str = "bullet_points") -> str:
        """Generate summary using OpenAI API with retry logic"""
        system_prompt = self._get_system_prompt(style)
        user_prompt = self._build_user_prompt(title, abstract, content)
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))
    
    def _get_system_prompt(self, style: str) -> str:
        """Generate system prompt based on summary style"""
        style_instructions = {
            "bullet_points": "Provide a concise bullet-point summary focusing on key contributions.",
            "paragraph": "Write a 150-word paragraph summarizing the paper's main points.",
            "technical": "Create a detailed technical summary including methodology."
        }
        return style_instructions.get(style, style_instructions["bullet_points"])
    
    def _build_user_prompt(self, title: str, abstract: str, content: str) -> str:
        """Build user prompt for summarization"""
        return f"""Title: {title}
Abstract: {abstract}

Content Excerpt:
{content[:8000]}... [truncated if too long]"""
