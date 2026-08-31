from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Source, Evidence, SourceType

class SourceAnalyzer:
    def __init__(self):
        self.primary_domains = {
            ".gov": ["usa.gov", "gov.uk", "europa.eu"],
            ".edu": [],
            "international": ["un.org", "who.int", "imf.org", "worldbank.org"]
        }
        self.fact_check_domains = [
            "factcheck.org", "politifact.com", "snopes.com", "reuters.com",
            "ap.org", "bbc.com", "npr.org", "apnews.com"
        ]
        self.news_domains = [
            "cnn.com", "foxnews.com", "nytimes.com", "washingtonpost.com",
            "theguardian.com", "bbc.com", "reuters.com", "ap.org"
        ]
    
    async def analyze_sources(self, sources: List[Source], db: AsyncSession) -> List[Dict[str, Any]]:
        analyses = []
        for source in sources:
            analysis = await self._analyze_single_source(source, db)
            analyses.append(analysis)
        return analyses
    
    async def _analyze_single_source(self, source: Source, db: AsyncSession) -> Dict[str, Any]:
        analysis = {
            "source_id": source.id,
            "url": source.url,
            "domain": source.domain,
            "source_type": source.source_type.value,
            "credibility_score": source.credibility_score,
            "is_independent": source.is_independent,
            "factors": [],
            "warnings": [],
            "strengths": []
        }
        
        if source.source_type == SourceType.PRIMARY:
            analysis["strengths"].append("Primary source - direct from original publisher")
            analysis["factors"].append("High trust weight")
        elif source.source_type == SourceType.FACT_CHECK:
            analysis["strengths"].append("Reputable fact-checking organization")
            analysis["factors"].append("Specialized verification")
        elif source.source_type == SourceType.SECONDARY:
            analysis["factors"].append("Established news organization")
        
        if source.is_independent:
            analysis["strengths"].append("Independent source")
        
        if source.credibility_score >= 0.8:
            analysis["strengths"].append("High credibility score")
        elif source.credibility_score <= 0.4:
            analysis["warnings"].append("Low credibility score")
        
        evidence_result = await db.execute(
            select(Evidence).where(Evidence.source_id == source.id)
        )
        evidence_items = evidence_result.scalars().all()
        
        supporting = sum(1 for e in evidence_items if e.relation == "supports")
        contradicting = sum(1 for e in evidence_items if e.relation == "contradicts")
        
        analysis["supporting_evidence_count"] = supporting
        analysis["contradicting_evidence_count"] = contradicting
        
        if contradicting > 0 and supporting > 0:
            analysis["warnings"].append("Source provides both supporting and contradicting evidence")
        
        return analysis
    
    def detect_source_independence(self, sources: List[Source]) -> Dict[str, Any]:
        domain_groups = {}
        for source in sources:
            domain = source.domain or ""
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(source)
        
        independent_count = 0
        dependent_groups = []
        
        for domain, group in domain_groups.items():
            if len(group) > 1:
                dependent_groups.append({
                    "domain": domain,
                    "count": len(group),
                    "sources": [s.url for s in group]
                })
            else:
                independent_count += 1
        
        return {
            "total_sources": len(sources),
            "independent_sources": independent_count,
            "dependent_groups": dependent_groups,
            "true_independence_ratio": independent_count / len(sources) if sources else 0
        }
    
    def classify_source_type(self, domain: str, url: str) -> SourceType:
        domain_lower = domain.lower()
        
        for suffix in [".gov", ".mil", "gov.", "government"]:
            if suffix in domain_lower:
                return SourceType.PRIMARY
        
        for edu_suffix in [".edu", ".ac.uk", ".ac.jp", ".edu.au"]:
            if edu_suffix in domain_lower:
                return SourceType.PRIMARY
        
        for fc_domain in self.fact_check_domains:
            if fc_domain in domain_lower:
                return SourceType.FACT_CHECK
        
        for org in ["who.int", "un.org", "imf.org", "worldbank.org", "nasa.gov", "nih.gov"]:
            if org in domain_lower:
                return SourceType.PRIMARY
        
        return SourceType.SECONDARY
