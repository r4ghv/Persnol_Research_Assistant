import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


SOURCE_QUALITY = {
    "PubMed": 20,
    "Semantic Scholar": 15,
    "arXiv": 10,
}


def _parse_year(published: Optional[str]) -> Optional[int]:
    if not published:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(published[:10], fmt).year
        except (ValueError, IndexError):
            continue
    # Handle PubMed dates like "2025 Jan" or "2025 Jan-Dec"
    m = re.match(r"(\d{4})", published)
    return int(m.group(1)) if m else None


def _keyword_overlap(query: str, title: str, abstract: str) -> float:
    """Return a score 0-40 for keyword overlap."""
    keywords = set(re.sub(r"[^\w\s]", " ", query.lower()).split())
    if not keywords:
        return 0

    title_words = set(re.sub(r"[^\w\s]", " ", title.lower()).split())
    abstract_words = set(re.sub(r"[^\w\s]", " ", abstract.lower()).split())

    title_matches = len(keywords & title_words)
    abstract_matches = len(keywords & abstract_words)

    weighted = title_matches * 2 + abstract_matches
    total_possible = len(keywords) * 3
    return 40.0 * (weighted / total_possible) if total_possible else 0


def _recency_score(published: Optional[str]) -> float:
    year = _parse_year(published)
    if year is None:
        return 0
    current = datetime.now(timezone.utc).year
    age = current - year
    if age <= 0:
        return 30
    if age <= 2:
        return 25
    if age <= 5:
        return 15
    if age <= 10:
        return 5
    return 0


def _citation_score(citation_count: Optional[int]) -> float:
    if citation_count is None or citation_count <= 0:
        return 0
    if citation_count >= 1000:
        return 10
    if citation_count >= 100:
        return 8
    if citation_count >= 10:
        return 5
    if citation_count >= 1:
        return 2
    return 0


def score_paper(paper: Dict, query: str) -> float:
    relevance = _keyword_overlap(query, paper.get("title", ""), paper.get("abstract", ""))
    recency = _recency_score(paper.get("published"))
    source_q = SOURCE_QUALITY.get(paper.get("source", ""), 5)
    citations = _citation_score(paper.get("citation_count"))
    total = relevance + recency + source_q + citations
    return round(total, 1)


def rank_papers(papers: List[Dict], query: str) -> List[Dict]:
    scored = []
    for p in papers:
        p["_rank_score"] = score_paper(p, query)
        scored.append(p)
    scored.sort(key=lambda p: p["_rank_score"], reverse=True)
    for i, p in enumerate(scored, 1):
        p["_rank"] = i
    return scored


DEFAULT_MAX_PAPERS_PER_SOURCE = {
    "arXiv": 5,
    "PubMed": 3,
    "Semantic Scholar": 5,
}


def _deduplicate(all_papers: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for p in all_papers:
        key = p.get("doi") or p.get("title", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def search_all_sources(
    query: str,
    sources: List[str],
    max_results: int = 5,
    timeout: int = 30,
) -> List[Dict]:
    from .sources import ArxivSource, PubMedSource, SemanticScholarSource

    source_map = {
        "arXiv": ArxivSource,
        "PubMed": PubMedSource,
        "Semantic Scholar": SemanticScholarSource,
    }

    per_source = max(1, max_results // max(len(sources), 1))

    all_papers = []
    for name in sources:
        cls = source_map.get(name)
        if cls is None:
            continue
        instance = cls(timeout=timeout) if name != "arXiv" else cls()
        try:
            results = instance.search(query, per_source)
            all_papers.extend(results)
        except Exception as e:
            logger.error(f"{name} search failed: {e}")

    deduped = _deduplicate(all_papers)
    ranked = rank_papers(deduped, query)
    return ranked[:max_results]
