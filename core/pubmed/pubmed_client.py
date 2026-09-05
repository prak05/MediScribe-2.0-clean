"""NCBI PubMed E-Utilities Client for MediScribe.
External Literature Retrieval for Hybrid Verification and Live Medical Research.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import requests

@dataclass
class PubMedArticle:
    """Represents a peer-reviewed article indexed on NCBI PubMed."""
    pmid: str
    title: str
    pubdate: str
    journal: str
    authors: List[str] = field(default_factory=list)
    url: str = ""

    @property
    def authors_formatted(self) -> str:
        if not self.authors:
            return "Unknown Authors"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{', '.join(self.authors[:3])} et al."

    @property
    def citation_line(self) -> str:
        parts = [self.title]
        if self.journal:
            parts.append(self.journal)
        if self.pubdate:
            parts.append(self.pubdate)
        return " | ".join(parts)

class PubMedClient:
    """Decoupled client interface for querying NCBI PubMed databases."""

    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, timeout_s: int = 15):
        self.timeout_s = timeout_s

    def search(self, term: str, retmax: int = 5) -> List[PubMedArticle]:
        """Search PubMed database by clinical term and fetch detailed metadata."""
        clean_term = (term or "").strip()
        if not clean_term:
            return []

        search_params = {
            "db": "pubmed",
            "term": clean_term,
            "retmode": "xml",
            "retmax": str(retmax),
            "sort": "relevance",
        }

        try:
            r = requests.get(self.ESEARCH_URL, params=search_params, timeout=self.timeout_s)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            id_list = [elem.text for elem in root.findall(".//IdList/Id") if elem.text]
            if not id_list:
                return []

            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
            }
            s = requests.get(self.ESUMMARY_URL, params=summary_params, timeout=self.timeout_s)
            s.raise_for_status()
            data = s.json()

            results: List[PubMedArticle] = []
            result_dict = data.get("result", {})
            uids = result_dict.get("uids", [])

            for uid in uids:
                rec = result_dict.get(uid, {})
                title = rec.get("title") or "Untitled Paper"
                pubdate = rec.get("pubdate") or ""
                source = rec.get("source") or ""
                raw_authors = rec.get("authors") or []
                author_names = [a.get("name") for a in raw_authors if isinstance(a, dict) and a.get("name")]

                results.append(
                    PubMedArticle(
                        pmid=uid,
                        title=title,
                        pubdate=pubdate,
                        journal=source,
                        authors=author_names,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                    )
                )
            return results

        except Exception as e:
            # Return empty list on failure, gracefully handled by callers
            return []
