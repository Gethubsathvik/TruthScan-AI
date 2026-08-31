from typing import List, Dict, Any, Optional
from app.services.search_service import SearchService

class FactCheckService:
    def __init__(self):
        self.search_service = SearchService()
        self.fact_check_organizations = [
            "factcheck.org", "politifact.com", "snopes.com", "reuters.com/fact-check",
            "ap.org/fact-check", "bbc.com/reality_check", "npr.org/sections/factcheck"
        ]
    
    async def search_fact_checks(self, claim_text: str) -> List[Dict[str, Any]]:
        queries = [
            f"{claim_text} fact check",
            f"{claim_text} politifact",
            f"{claim_text} snopes",
            f"{claim_text} factcheck.org"
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in queries:
            try:
                results = await self.search_service.search(query, max_results=5)
                for result in results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        if self._is_fact_check_source(url, result.get("title", "")):
                            seen_urls.add(url)
                            all_results.append({
                                "organization": self._extract_organization(url, result.get("title", "")),
                                "claim_checked": claim_text[:300],
                                "conclusion": self._extract_conclusion(result.get("title", "") + " " + result.get("snippet", "")),
                                "summary": result.get("snippet", "")[:500],
                                "date": result.get("published_date"),
                                "url": url,
                                "title": result.get("title", "")
                            })
            except Exception:
                continue
        
        return all_results[:5]
    
    def _is_fact_check_source(self, url: str, title: str) -> bool:
        url_lower = url.lower()
        title_lower = title.lower()
        
        for org in self.fact_check_organizations:
            if org in url_lower:
                return True
        
        fact_check_keywords = ["fact check", "fact-check", "verification", "true or false", "myth", "debunk"]
        return any(kw in title_lower for kw in fact_check_keywords)
    
    def _extract_organization(self, url: str, title: str) -> str:
        url_lower = url.lower()
        
        if "politifact" in url_lower:
            return "PolitiFact"
        elif "snopes" in url_lower:
            return "Snopes"
        elif "factcheck.org" in url_lower:
            return "FactCheck.org"
        elif "reuters" in url_lower:
            return "Reuters Fact Check"
        elif "ap.org" in url_lower or "apnews" in url_lower:
            return "Associated Press"
        elif "bbc" in url_lower:
            return "BBC Reality Check"
        elif "npr" in url_lower:
            return "NPR Fact Check"
        else:
            return "Unknown Fact-Checking Organization"
    
    def _extract_conclusion(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ["true", "accurate", "correct", "confirmed"]):
            if any(kw in text_lower for kw in ["partially", "mostly", "mostly true"]):
                return "Mostly True"
            return "True"
        elif any(kw in text_lower for kw in ["false", "incorrect", "wrong", "debunked", "myth"]):
            if any(kw in text_lower for kw in ["partially", "mostly", "mostly false"]):
                return "Mostly False"
            return "False"
        elif any(kw in text_lower for kw in ["misleading", "out of context", "lacks context"]):
            return "Misleading"
        elif any(kw in text_lower for kw in ["unproven", "unverified", "no evidence"]):
            return "Unverified"
        else:
            return "See source for details"
