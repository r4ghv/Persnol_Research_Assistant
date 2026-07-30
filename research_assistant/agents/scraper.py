import fitz
import requests
import os
import re
import tempfile
import logging
from typing import List, Dict, Optional, Tuple

from .ranker import search_all_sources

logger = logging.getLogger(__name__)

DEFAULT_SOURCES = ["arXiv", "PubMed", "Semantic Scholar"]


class Scraper:
    def __init__(self, config=None):
        self.cache_dir = ".paper_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.request_timeout = getattr(config, "REQUEST_TIMEOUT", 30)
        self.max_pdf_pages = getattr(config, "MAX_PDF_PAGES", 10)
        self.retry_attempts = getattr(config, "RETRY_ATTEMPTS", 3)
        self.retry_delay = getattr(config, "RETRY_DELAY", 2.0)

    def fetch_papers(
        self,
        query: str,
        max_results: int = 5,
        sources: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Fetch papers from selected sources, deduplicate, and rank."""
        sources = sources or DEFAULT_SOURCES
        try:
            papers = search_all_sources(
                query=query,
                sources=sources,
                max_results=max_results,
                timeout=self.request_timeout,
            )
            if not papers:
                logger.warning("No papers found from any source")
            return papers
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return []

    def extract_content(self, paper: Dict) -> Tuple[str, Optional[bytes]]:
        """Download PDF and extract text. Returns (text, pdf_bytes)."""
        pdf_url = paper.get("pdf_url")
        if not pdf_url:
            return paper.get("abstract", ""), None

        cache_key = paper.get("entry_id", paper.get("source_id", ""))
        safe_key = re.sub(r"[^\w\-]", "_", cache_key)
        cache_file = os.path.join(self.cache_dir, f"{safe_key}.txt")

        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read(), None

        try:
            resp = requests.get(pdf_url, timeout=self.request_timeout)
            resp.raise_for_status()
            pdf_data = resp.content

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_data)
                pdf_path = tmp.name

            text = []
            try:
                with fitz.open(pdf_path) as doc:
                    for page_num in range(min(self.max_pdf_pages, len(doc))):
                        text.append(doc[page_num].get_text())
            finally:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

            full_text = "\n".join(text)

            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(full_text)

            return full_text, pdf_data
        except Exception as e:
            logger.error(f"Error extracting content from '{paper.get('title', '')[:50]}': {e}")
            return paper.get("abstract", ""), None
