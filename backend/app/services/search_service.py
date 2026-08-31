import httpx
import trafilatura
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import re
from datetime import datetime
import hashlib

from app.core.config import settings

class SearchService:
    def __init__(self):
        self.provider = self._get_search_provider()
        self.demo_mode = False
    
    def _get_search_provider(self):
        if settings.TAVILY_API_KEY:
            return TavilySearchProvider(settings.TAVILY_API_KEY)
        elif settings.BRAVE_SEARCH_API_KEY:
            return BraveSearchProvider(settings.BRAVE_SEARCH_API_KEY)
        elif settings.SERPAPI_KEY:
            return SerpApiProvider(settings.SERPAPI_KEY)
        else:
            self.demo_mode = True
            return DemoSearchProvider()
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        return await self.provider.search(query, max_results)
    
    async def multi_search(self, queries: List[str], max_results_per_query: int = 5) -> List[Dict[str, Any]]:
        all_results = []
        seen_urls = set()
        
        for query in queries:
            try:
                results = await self.search(query, max_results_per_query)
                for result in results:
                    url = result.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
            except Exception as e:
                continue
        
        return all_results[:max_results_per_query * len(queries)]

class DemoSearchProvider:
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        base_domain = "example.com"
        
        results = []
        for i in range(min(max_results, 5)):
            seed = int(query_hash, 16) + i
            url = f"https://{base_domain}/article/{seed}"
            title = f"Search result for: {query[:50]}..."
            snippet = f"This is a demo search result for the query '{query}'. In production, this would be real web evidence from actual sources."
            
            results.append({
                "url": url,
                "title": title,
                "snippet": snippet,
                "source": url,
                "score": 0.7 - (i * 0.1),
                "published_date": datetime.utcnow().isoformat()
            })
        
        return results

class TavilySearchProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
            response = await client.post(
                self.base_url,
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": True,
                    "include_raw_content": False
                }
            )
            response.raise_for_status()
            data = response.json()
            results = []
            
            for item in data.get("results", []):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "source": item.get("url", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date", None)
                })
            
            return results

class BraveSearchProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
            response = await client.get(
                self.base_url,
                params={"q": query, "count": max_results},
                headers={"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            results = []
            
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("description", ""),
                    "source": item.get("url", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("page_age", None)
                })
            
            return results

class SerpApiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
            response = await client.get(
                self.base_url,
                params={"q": query, "api_key": self.api_key, "num": max_results}
            )
            response.raise_for_status()
            data = response.json()
            results = []
            
            for item in data.get("organic_results", []):
                results.append({
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("link", ""),
                    "score": 1.0,
                    "published_date": item.get("date", None)
                })
            
            return results
