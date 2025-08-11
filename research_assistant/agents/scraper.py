import arxiv
import requests
import fitz  # PyMuPDF
import os
import re
from typing import List, Dict
from datetime import datetime

class Scraper:
    def __init__(self):
        self.cache_dir = ".paper_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def fetch_papers(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch research papers from arXiv"""
        try:
            # Clean and format the query
            clean_query = self._clean_query(query)
            
            # Try different search strategies
            papers = self._search_with_strategy(clean_query, max_results)
            
            if not papers:
                # Fallback: try with broader search
                papers = self._search_with_strategy(clean_query.split()[0], max_results)
            
            if not papers:
                # Final fallback: try with common research terms
                papers = self._search_with_strategy("computer science", max_results)
            
            return papers
            
        except Exception as e:
            print(f"Error fetching papers: {str(e)}")
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
            print(f"Searching arXiv for: '{query}'")
            
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
            
            print(f"Found {len(papers)} papers for '{query}'")
            return papers
            
        except Exception as e:
            print(f"Error with search strategy '{query}': {str(e)}")
            return []
    
    def extract_content(self, paper: Dict, max_pages: int = 10) -> str:
        """Extract text content from PDF"""
        cache_file = os.path.join(self.cache_dir, f"{paper['entry_id'].split('/')[-1]}.txt")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
                
        try:
            response = requests.get(paper['pdf_url'], timeout=30)
            response.raise_for_status()
            
            pdf_path = os.path.join(self.cache_dir, "temp.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            text = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(min(max_pages, len(doc))):
                    text.append(doc[page_num].get_text())
            
            full_text = "\n".join(text)
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # Clean up temp file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            return full_text
        except Exception as e:
            print(f"Error extracting content: {str(e)}")
            return paper.get('abstract', '')
