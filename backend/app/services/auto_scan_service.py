import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.services.search_service import SearchService
from app.services.llm_service import LLMService
from app.services.evidence_scoring import EvidenceScoringEngine
from app.services.source_analyzer import SourceAnalyzer

class AutoScanService:
    def __init__(self):
        self.search_service = SearchService()
        self.llm_service = LLMService()
        self.scoring_engine = EvidenceScoringEngine()
        self.source_analyzer = SourceAnalyzer()
        self.sources_path = Path(__file__).parent.parent.parent / "app" / "data" / "news_sources.json"
        self.sources_config = self._load_sources()
    
    def _load_sources(self) -> Dict[str, Any]:
        if self.sources_path.exists():
            with open(self.sources_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"news_sources": [], "article_sources": []}
    
    async def scan_all_sources(self, max_per_category: int = 10) -> List[Dict[str, Any]]:
        news_sources = self.sources_config.get("news_sources", [])[:max_per_category]
        article_sources = self.sources_config.get("article_sources", [])[:max_per_category]
        
        results = []
        
        news_tasks = [self._scan_source(source) for source in news_sources]
        article_tasks = [self._scan_source(source) for source in article_sources]
        
        news_results = await asyncio.gather(*news_tasks, return_exceptions=True)
        article_results = await asyncio.gather(*article_tasks, return_exceptions=True)
        
        for result in news_results + article_results:
            if isinstance(result, dict) and result.get("success"):
                results.append(result)
        
        return results
    
    async def _scan_source(self, source: Dict[str, str]) -> Dict[str, Any]:
        try:
            search_query = f"site:{source['url']} latest news"
            search_results = await self.search_service.search(search_query, max_results=3)
            
            if not search_results:
                return {"success": False, "url": source["url"], "error": "No results found"}
            
            articles = []
            for result in search_results:
                article_data = {
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "snippet": result.get("snippet"),
                    "source_name": source["name"],
                    "source_url": source["url"],
                    "source_country": source.get("country", "Unknown"),
                    "category": source.get("category", "news"),
                    "language": source.get("language", "en"),
                    "credibility": source.get("credibility", "medium"),
                    "scanned_at": datetime.utcnow().isoformat()
                }
                articles.append(article_data)
            
            return {
                "success": True,
                "url": source["url"],
                "name": source["name"],
                "articles": articles,
                "scanned_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"success": False, "url": source["url"], "error": str(e)}
    
    async def verify_scanned_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        title = article.get("title", "")
        snippet = article.get("snippet", "")
        
        if not title and not snippet:
            return {"verdict": "unverified", "confidence": 0.0, "reason": "No content to verify"}
        
        text = f"{title}. {snippet}"
        
        claims = await self.llm_service.extract_claims(text)
        if not claims:
            claims = [{"text": text, "certainty_level": "medium"}]
        
        search_tasks = []
        for claim in claims:
            claim_text = claim.get("text", "")
            queries = [
                claim_text,
                f"{claim_text} fact check",
                f"{claim_text} official"
            ]
            for query in queries[:2]:
                search_tasks.append(self.search_service.search(query, max_results=3))
        
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        evidence_count = 0
        supporting = 0
        contradicting = 0
        
        for result_set in all_results:
            if isinstance(result_set, list):
                evidence_count += len(result_set)
                for r in result_set:
                    title_lower = r.get("title", "").lower()
                    if any(word in title_lower for word in ["false", "fake", "myth", "deny"]):
                        contradicting += 1
                    elif any(word in title_lower for word in ["true", "confirm", "real"]):
                        supporting += 1
        
        score = 50
        score += supporting * 5
        score -= contradicting * 8
        score = max(0, min(100, score))
        
        if score >= 80:
            verdict = "verified"
        elif score >= 65:
            verdict = "likely_true"
        elif score >= 50:
            verdict = "partially_true"
        elif score >= 35:
            verdict = "misleading"
        elif score >= 20:
            verdict = "unverified"
        elif score >= 10:
            verdict = "likely_false"
        else:
            verdict = "false"
        
        if evidence_count == 0:
            verdict = "unverified"
        
        confidence = min(0.95, 0.3 + evidence_count * 0.05)
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "evidence_count": evidence_count,
            "supporting": supporting,
            "contradicting": contradicting,
            "claims_checked": len(claims),
            "article_title": title,
            "article_url": article.get("url"),
            "source_name": article.get("source_name"),
            "verified_at": datetime.utcnow().isoformat()
        }
    
    async def get_trending_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        all_sources = self.sources_config.get("news_sources", [])
        
        trending = []
        for source in all_sources[:15]:
            try:
                search_query = f"site:{source['url']} latest news today"
                search_results = await self.search_service.search(search_query, max_results=3)
                
                for result in search_results[:2]:
                    article = {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "source_name": source["name"],
                        "source_url": source["url"],
                        "source_country": source.get("country", "Unknown"),
                        "language": source.get("language", "en"),
                        "credibility": source.get("credibility", "medium"),
                        "published_date": result.get("published_date", datetime.utcnow().isoformat()),
                        "fetched_at": datetime.utcnow().isoformat()
                    }
                    trending.append(article)
            except Exception:
                continue
        
        seen_urls = set()
        unique_trending = []
        for item in trending:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_trending.append(item)
        
        return unique_trending[:limit]
    
    async def get_daily_updates(self, limit: int = 20) -> List[Dict[str, Any]]:
        all_sources = self.sources_config.get("news_sources", []) + self.sources_config.get("article_sources", [])
        
        updates = []
        for source in all_sources[:20]:
            try:
                search_query = f"site:{source['url']} new update today"
                search_results = await self.search_service.search(search_query, max_results=2)
                
                for result in search_results[:1]:
                    article = {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "source_name": source["name"],
                        "source_url": source["url"],
                        "source_country": source.get("country", "Unknown"),
                        "language": source.get("language", "en"),
                        "credibility": source.get("credibility", "medium"),
                        "published_date": result.get("published_date", datetime.utcnow().isoformat()),
                        "fetched_at": datetime.utcnow().isoformat()
                    }
                    updates.append(article)
            except Exception:
                continue
        
        seen_urls = set()
        unique_updates = []
        for item in updates:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_updates.append(item)
        
        return unique_updates[:limit]
    
    async def batch_verify_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tasks = [self.verify_scanned_article(article) for article in articles]
        return await asyncio.gather(*tasks, return_exceptions=True)
