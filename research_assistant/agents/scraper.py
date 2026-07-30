import arxiv
import requests
import fitz  # PyMuPDF
import os
import re
import tempfile
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self, config=None):
        self.cache_dir = ".paper_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Use config values or sensible defaults
        self.request_timeout = getattr(config, 'REQUEST_TIMEOUT', 30)
        self.max_pdf_pages = getattr(config, 'MAX_PDF_PAGES', 10)
        self.retry_attempts = getattr(config, 'RETRY_ATTEMPTS', 3)
        self.retry_delay = getattr(config, 'RETRY_DELAY', 2.0)
    
    def fetch_papers(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch research papers from arXiv"""
        try:
            clean_query = self._clean_query(query)
            
            # Try progressively broader search strategies
            papers = self._search_with_strategy(clean_query, max_results)
            
            if not papers:
                first_word = clean_query.split()[0] if clean_query.split() else query
                papers = self._search_with_strategy(first_word, max_results)
            
            if not papers:
                papers = self._search_with_strategy("computer science", max_results)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return []
    
    def _clean_query(self, query: str) -> str:
        """Clean and format search query for arXiv"""
        # Remove special characters and extra whitespace
        clean = re.sub(r'[^\w\s]', ' ', query)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # If query is too long, take first few words
        words = clean.split()
        if len(words) > 4:
            clean = ' '.join(words[:4])
        
        return clean
    
    def _search_with_strategy(self, query: str, max_results: int) -> List[Dict]:
        """Search with a specific strategy"""
        try:
            logger.info(f"Searching arXiv for: '{query}'")
            
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            papers = []
            client = arxiv.Client()
            
            for result in client.results(search):
                papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "abstract": result.summary,
                    "published": str(result.published),
                    "pdf_url": result.pdf_url,
                    "doi": result.doi or "N/A",
                    "entry_id": result.entry_id,
                    "primary_category": result.primary_category
                })
                
                if len(papers) >= max_results:
                    break
            
            logger.info(f"Found {len(papers)} papers for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"Error with search strategy '{query}': {e}")
            return []
    
    def extract_content(self, paper: Dict) -> Tuple[str, Optional[bytes]]:
        """Extract text content from PDF using a safe temp file.
        
        Returns: (extracted_text, pdf_bytes_or_None)
        """
        cache_file = os.path.join(self.cache_dir, f"{paper['entry_id'].split('/')[-1]}.txt")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read(), None
                
        try:
            response = requests.get(paper['pdf_url'], timeout=self.request_timeout)
            response.raise_for_status()
            pdf_data = response.content
            
            # Use a unique temp file to avoid race conditions
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
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
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            return full_text, pdf_data
        except Exception as e:
            logger.error(f"Error extracting content from '{paper['title'][:50]}': {e}")
            return paper.get('abstract', ''), None
