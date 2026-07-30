import arxiv as arxiv_client
import requests
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

PAPER_SCHEMA = [
    "title", "authors", "abstract", "published", "pdf_url",
    "doi", "source", "source_id", "citation_count", "url", "entry_id",
]

def _clean_query(query: str) -> str:
    clean = re.sub(r'[^\w\s]', ' ', query)
    clean = re.sub(r'\s+', ' ', clean).strip()
    words = clean.split()
    if len(words) > 4:
        clean = ' '.join(words[:4])
    return clean


class PaperSource(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int) -> List[Dict]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class ArxivSource(PaperSource):
    name = "arXiv"

    def search(self, query: str, max_results: int) -> List[Dict]:
        try:
            clean = _clean_query(query)
            logger.info(f"Searching arXiv for: '{clean}'")
            search = arxiv_client.Search(
                query=clean,
                max_results=max_results,
                sort_by=arxiv_client.SortCriterion.SubmittedDate,
            )
            papers = []
            for r in arxiv_client.Client().results(search):
                papers.append({
                    "title": r.title,
                    "authors": [a.name for a in r.authors],
                    "abstract": r.summary,
                    "published": str(r.published),
                    "pdf_url": r.pdf_url,
                    "doi": r.doi or None,
                    "source": self.name,
                    "source_id": r.entry_id.split("/")[-1],
                    "citation_count": None,
                    "url": r.entry_id,
                    "entry_id": r.entry_id,
                })
                if len(papers) >= max_results:
                    break
            logger.info(f"arXiv found {len(papers)} papers")
            return papers
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []


class PubMedSource(PaperSource):
    name = "PubMed"

    BASE_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    BASE_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def search(self, query: str, max_results: int) -> List[Dict]:
        try:
            clean = _clean_query(query)
            logger.info(f"Searching PubMed for: '{clean}'")

            search_params = {
                "db": "pubmed",
                "term": clean,
                "retmax": max_results,
                "retmode": "json",
                "sort": "date",
            }
            resp = requests.get(self.BASE_SEARCH, params=search_params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            ids = (data.get("esearchresult") or {}).get("idlist", [])
            if not ids:
                return []

            summary_params = {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
            }
            sresp = requests.get(self.BASE_SUMMARY, params=summary_params, timeout=self.timeout)
            sresp.raise_for_status()
            summary_data = sresp.json()
            results = (summary_data.get("result") or {})

            papers = []
            for uid in ids:
                uinfo = results.get(uid, {})
                papers.append({
                    "title": uinfo.get("title", ""),
                    "authors": [a.get("name", "") for a in (uinfo.get("authors") or [])],
                    "abstract": "",
                    "published": uinfo.get("pubdate", ""),
                    "pdf_url": None,
                    "doi": None,
                    "source": self.name,
                    "source_id": uid,
                    "citation_count": None,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    "entry_id": f"pubmed:{uid}",
                })
                if len(papers) >= max_results:
                    break

            # Fetch abstracts in batch
            if papers:
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                }
                fresp = requests.get(self.BASE_FETCH, params=fetch_params, timeout=self.timeout)
                if fresp.ok:
                    for paper in papers:
                        pid = paper["source_id"]
                        if f"<PubMedId>{pid}</PubMedId>" in fresp.text:
                            m = re.search(
                                rf"<AbstractText[^>]*>(.*?)</AbstractText>",
                                fresp.text[fresp.text.index(f"<PubMedId>{pid}</PubMedId>"):],
                                re.DOTALL,
                            )
                            if m:
                                paper["abstract"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

            logger.info(f"PubMed found {len(papers)} papers")
            return papers
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []


class SemanticScholarSource(PaperSource):
    name = "Semantic Scholar"

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def search(self, query: str, max_results: int) -> List[Dict]:
        try:
            clean = _clean_query(query)
            logger.info(f"Searching Semantic Scholar for: '{clean}'")
            params = {
                "query": clean,
                "limit": max_results,
                "fields": "title,authors,publicationDate,externalIds,openAccessPdf,citationCount,url,abstract",
            }
            resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("data", [])
            papers = []
            for p in raw:
                papers.append({
                    "title": p.get("title", ""),
                    "authors": [a.get("name", "") for a in (p.get("authors") or [])],
                    "abstract": p.get("abstract") or "",
                    "published": (p.get("publicationDate") or "")[:10],
                    "pdf_url": (p.get("openAccessPdf") or {}).get("url"),
                    "doi": (p.get("externalIds") or {}).get("DOI"),
                    "source": self.name,
                    "source_id": p.get("paperId", ""),
                    "citation_count": p.get("citationCount"),
                    "url": p.get("url", ""),
                    "entry_id": f"s2:{p.get('paperId', '')}",
                })
                if len(papers) >= max_results:
                    break
            logger.info(f"Semantic Scholar found {len(papers)} papers")
            return papers
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return []
