import httpx
import trafilatura
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup

from app.core.config import settings

class ArticleExtractionService:
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_length = settings.MAX_ARTICLE_LENGTH
    
    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text
                
                if len(content) > self.max_length * 10:
                    content = content[:self.max_length * 10]
                
                return self._extract_content(content, url)
        except httpx.TimeoutException:
            return {"error": "timeout", "message": "The page took too long to load."}
        except httpx.HTTPError as e:
            return {"error": "http_error", "message": f"Failed to fetch page: {str(e)}"}
        except Exception as e:
            return {"error": "unknown", "message": f"Extraction failed: {str(e)}"}
    
    def _extract_content(self, html: str, url: str) -> Dict[str, Any]:
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            output_format="json"
        )
        
        if extracted:
            import json
            data = json.loads(extracted)
            return {
                "title": data.get("title", ""),
                "author": data.get("author", ""),
                "date": data.get("date", ""),
                "text": data.get("text", "")[:self.max_length],
                "url": url,
                "success": True
            }
        
        soup = BeautifulSoup(html, "lxml")
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", title)
        
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:
                paragraphs.append(text)
        
        text = "\n\n".join(paragraphs)[:self.max_length]
        
        author = ""
        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag:
            author = author_tag.get("content", "")
        
        date = ""
        date_tag = soup.find("meta", property="article:published_time")
        if date_tag:
            date = date_tag.get("content", "")
        
        return {
            "title": title,
            "author": author,
            "date": date,
            "text": text,
            "url": url,
            "success": True
        }
    
    def detect_input_type(self, text: str, url: Optional[str] = None) -> str:
        if url:
            if self._is_url(url):
                return "url"
        
        text = text.strip()
        
        if len(text.split()) > 100:
            return "article"
        elif len(text.split()) > 5:
            return "claim"
        elif self._is_url(text):
            return "url"
        else:
            return "claim"
    
    def _is_url(self, text: str) -> bool:
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(text))
