import uuid
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.search_service import SearchService
from app.services.article_extraction_service import ArticleExtractionService
from app.services.llm_service import LLMService
from app.models.models import (
    VerificationRequest, Claim, Source, Evidence, FactCheck,
    MediaItem, Verdict, SourceType, EvidenceRelation, VerdictType
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

class VerificationPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_service = SearchService()
        self.extraction_service = ArticleExtractionService()
        self.llm_service = LLMService()
    
    async def run(self, verification_id: str, input_text: str, input_type: str) -> Dict[str, Any]:
        try:
            return await self._run_pipeline(verification_id, input_text, input_type)
        except Exception as e:
            return {
                "verification_id": verification_id,
                "input_type": input_type,
                "original_claim": input_text,
                "claims": [{"id": str(uuid.uuid4()), "text": input_text, "subject": "", "action": "", "object": "", "location": "", "date_time": "", "numerical_values": "", "entities": "", "category": "Other", "certainty_level": "medium"}],
                "verdict": "unverified",
                "confidence": 0.3,
                "evidence_strength": "UNKNOWN",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "neutral_evidence": [],
                "primary_sources": [],
                "fact_checks": [],
                "source_analysis": [],
                "temporal_analysis": {"is_outdated": False, "notes": f"Demo mode: {str(e)}"},
                "headline_analysis": {"clickbait_score": 0.0, "exaggeration_detected": False, "headline_body_contradiction": False, "notes": ["Demo mode - configure API keys for full analysis"]},
                "media_analysis": {"images": [], "videos": [], "reused_media_count": 0, "unverified_media_count": 0},
                "explanation": f"System is running in demo mode. Configure OPENAI_API_KEY and a search API key (TAVILY_API_KEY, BRAVE_SEARCH_API_KEY, or SERPAPI_KEY) for real-time evidence verification. Error: {str(e)}",
                "limitations": ["Demo mode - limited functionality without API keys", "No real-time search performed", "LLM analysis simulated"]
            }
    
    async def _run_pipeline(self, verification_id: str, input_text: str, input_type: str) -> Dict[str, Any]:
        article_data = {}
        if input_type == "url":
            article_data = await self.extraction_service.extract_from_url(input_text)
            if article_data.get("error"):
                return {
                    "verification_id": verification_id,
                    "input_type": input_type,
                    "original_claim": input_text,
                    "claims": [],
                    "verdict": "unverified",
                    "confidence": 0.0,
                    "evidence_strength": "unknown",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "neutral_evidence": [],
                    "primary_sources": [],
                    "fact_checks": [],
                    "source_analysis": [],
                    "temporal_analysis": {"is_outdated": False, "notes": article_data.get("message", "Extraction failed")},
                    "headline_analysis": {"clickbait_score": 0.0, "exaggeration_detected": False, "headline_body_contradiction": False, "notes": [article_data.get("message", "Extraction failed")]},
                    "media_analysis": {"images": [], "videos": [], "reused_media_count": 0, "unverified_media_count": 0},
                    "explanation": "Article extraction failed. Please provide the article text manually.",
                    "limitations": ["URL extraction failed"]
                }
            text_for_claims = article_data.get("text", input_text)
        else:
            text_for_claims = input_text
        
        claims = await self.llm_service.extract_claims(text_for_claims)
        if not claims:
            claims = [{"text": text_for_claims, "subject": "", "action": "", "object": "", "certainty_level": "medium"}]
        
        category = await self.llm_service.classify_category(text_for_claims)
        
        db_claims = []
        for claim_data in claims:
            claim_id = str(uuid.uuid4())
            claim = Claim(
                id=claim_id,
                verification_request_id=verification_id,
                text=claim_data.get("text", ""),
                subject=claim_data.get("subject"),
                action=claim_data.get("action"),
                object=claim_data.get("object"),
                location=claim_data.get("location"),
                date_time=claim_data.get("date_time"),
                numerical_values=claim_data.get("numerical_values"),
                entities=claim_data.get("entities"),
                category=category,
                certainty_level=claim_data.get("certainty_level")
            )
            self.db.add(claim)
            db_claims.append(claim)
        
        all_search_results = []
        all_sources = []
        all_evidence = []
        all_fact_checks = []
        
        for claim in db_claims:
            claim_text = claim.text
            search_queries = self._generate_search_queries(claim_text)
            
            search_results = await self.search_service.multi_search(search_queries, max_results_per_query=5)
            all_search_results.extend(search_results)
            
            for result in search_results:
                source = await self._process_source(result, verification_id)
                if source:
                    all_sources.append(source)
            
            for result in search_results:
                evidence = await self._extract_evidence(result, claim, verification_id)
                if evidence:
                    all_evidence.append(evidence)
            
            fact_check_results = await self._search_fact_checks(claim_text)
            for fc in fact_check_results:
                fact_check = FactCheck(
                    verification_request_id=verification_id,
                    organization=fc.get("organization"),
                    claim_checked=fc.get("claim_checked"),
                    conclusion=fc.get("conclusion"),
                    summary=fc.get("summary"),
                    date=fc.get("date"),
                    url=fc.get("url")
                )
                self.db.add(fact_check)
                all_fact_checks.append(fact_check)
        
        unique_sources = self._deduplicate_sources(all_sources)
        for source in unique_sources:
            self.db.add(source)
        
        for evidence in all_evidence:
            self.db.add(evidence)
        
        supporting = [e for e in all_evidence if e.relation == EvidenceRelation.SUPPORTS]
        contradicting = [e for e in all_evidence if e.relation == EvidenceRelation.CONTRADICTS]
        neutral = [e for e in all_evidence if e.relation == EvidenceRelation.NEUTRAL]
        
        primary_sources = [s for s in unique_sources if s.source_type == SourceType.PRIMARY]
        
        headline_analysis = {}
        if input_type == "url" and article_data.get("title") and article_data.get("text"):
            headline_analysis = await self.llm_service.analyze_headline(
                article_data.get("title", ""),
                article_data.get("text", "")
            )
        else:
            headline_analysis = {
                "clickbait_score": 0.0,
                "exaggeration_detected": False,
                "headline_body_contradiction": False,
                "notes": []
            }
        
        evidence_summary = f"Analyzed {len(unique_sources)} sources including {len(primary_sources)} primary sources. Found {len(supporting)} supporting, {len(contradicting)} contradicting, and {len(neutral)} neutral evidence items."
        factors = []
        if primary_sources:
            factors.append(f"{len(primary_sources)} primary source(s) analyzed")
        if contradicting:
            factors.append(f"{len(contradicting)} contradicting evidence item(s)")
        if supporting:
            factors.append(f"{len(supporting)} supporting evidence item(s)")
        if headline_analysis.get("exaggeration_detected"):
            factors.append("headline exaggeration detected")
        
        verdict_data = self._calculate_verdict(
            supporting, contradicting, neutral, primary_sources, unique_sources, headline_analysis
        )
        
        explanation = await self.llm_service.generate_explanation(
            verdict_data["verdict"],
            verdict_data["confidence"],
            evidence_summary,
            factors
        )
        
        verdict = Verdict(
            id=str(uuid.uuid4()),
            verification_request_id=verification_id,
            verdict=verdict_data["verdict"],
            confidence=verdict_data["confidence"],
            evidence_strength=verdict_data["evidence_strength"],
            explanation=explanation,
            limitations="; ".join(verdict_data.get("limitations", [])),
            supporting_evidence_count=len(supporting),
            contradicting_evidence_count=len(contradicting),
            neutral_evidence_count=len(neutral)
        )
        self.db.add(verdict)
        
        await self.db.commit()
        
        return self._build_response(
            verification_id, input_type, input_text, db_claims,
            verdict, supporting, contradicting, neutral,
            unique_sources, primary_sources, all_fact_checks,
            headline_analysis, article_data, explanation
        )
    
    def _generate_search_queries(self, claim_text: str) -> List[str]:
        queries = []
        queries.append(claim_text)
        
        words = claim_text.split()
        if len(words) > 5:
            queries.append(" ".join(words[:5]))
            queries.append(" ".join(words[-5:]))
        
        queries.append(f"{claim_text} official")
        queries.append(f"{claim_text} fact check")
        queries.append(f"{claim_text} government")
        
        return queries[:7]
    
    async def _process_source(self, result: Dict[str, Any], verification_id: str) -> Optional[Source]:
        url = result.get("url", "")
        if not url:
            return None
        
        domain = ""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
        except Exception:
            pass
        
        source_type = SourceType.UNKNOWN
        if any(gov in domain for gov in [".gov", ".mil", "govt", "government"]):
            source_type = SourceType.PRIMARY
        elif any(fc in domain for fc in ["factcheck", "politifact", "snopes", "reuters", "ap.org"]):
            source_type = SourceType.FACT_CHECK
        elif any(edu in domain for edu in [".edu", ".ac.uk", "university", "institute"]):
            source_type = SourceType.PRIMARY
        elif any(news in domain for news in ["news", "bbc", "cnn", "reuters", "associated-press", "theguardian", "nytimes", "washingtonpost"]):
            source_type = SourceType.SECONDARY
        
        credibility_score = 0.5
        if source_type == SourceType.PRIMARY:
            credibility_score = 0.85
        elif source_type == SourceType.SECONDARY:
            credibility_score = 0.7
        elif source_type == SourceType.FACT_CHECK:
            credibility_score = 0.8
        
        return Source(
            verification_request_id=verification_id,
            url=url,
            title=result.get("title", ""),
            domain=domain,
            source_type=source_type,
            publisher=domain,
            publication_date=result.get("published_date"),
            credibility_score=credibility_score,
            is_independent=True
        )
    
    async def _extract_evidence(self, result: Dict[str, Any], claim: Claim, verification_id: str) -> Optional[Evidence]:
        snippet = result.get("snippet", "")
        if not snippet or len(snippet) < 20:
            return None
        
        title = result.get("title", "").lower()
        claim_lower = claim.text.lower()
        
        relation = EvidenceRelation.NEUTRAL
        confidence = 0.5
        
        if any(word in title for word in ["deny", "denies", "false", "fake", "myth", "not true", "incorrect"]):
            relation = EvidenceRelation.CONTRADICTS
            confidence = 0.6
        elif any(word in title for word in ["confirm", "confirms", "true", "real", "official", "announcement"]):
            relation = EvidenceRelation.SUPPORTS
            confidence = 0.6
        
        return Evidence(
            id=str(uuid.uuid4()),
            verification_request_id=verification_id,
            claim_id=claim.id,
            text=snippet[:500],
            evidence_type="search_snippet",
            relation=relation,
            confidence=confidence,
            extraction_method="search_snippet",
            metadata=json.dumps({"url": result.get("url", ""), "title": result.get("title", "")})
        )
    
    async def _search_fact_checks(self, claim_text: str) -> List[Dict[str, Any]]:
        queries = [
            f"{claim_text} fact check",
            f"{claim_text} politifact",
            f"{claim_text} snopes"
        ]
        
        fact_checks = []
        for query in queries[:2]:
            results = await self.search_service.search(query, max_results=3)
            for result in results:
                title = result.get("title", "").lower()
                if any(fc in title for fc in ["fact check", "politifact", "snopes", "factcheck"]):
                    fact_checks.append({
                        "organization": result.get("title", "").split()[0] if result.get("title") else "Unknown",
                        "claim_checked": claim_text[:200],
                        "conclusion": "See source for details",
                        "summary": result.get("snippet", "")[:300],
                        "date": result.get("published_date"),
                        "url": result.get("url")
                    })
        
        return fact_checks[:3]
    
    def _deduplicate_sources(self, sources: List[Source]) -> List[Source]:
        seen_urls = set()
        unique = []
        for source in sources:
            if source.url and source.url not in seen_urls:
                seen_urls.add(source.url)
                unique.append(source)
        return unique
    
    def _calculate_verdict(
        self, supporting: List[Evidence], contradicting: List[Evidence],
        neutral: List[Evidence], primary_sources: List[Source],
        all_sources: List[Source], headline_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        score = 50
        score += len(supporting) * 5
        score += len(primary_sources) * 10
        score -= len(contradicting) * 8
        score -= len(neutral) * 2
        
        if headline_analysis.get("exaggeration_detected"):
            score -= 10
        if headline_analysis.get("headline_body_contradiction"):
            score -= 15
        
        score = max(0, min(100, score))
        
        if score >= 80:
            verdict = VerdictType.VERIFIED
            evidence_strength = "HIGH"
        elif score >= 65:
            verdict = VerdictType.LIKELY_TRUE
            evidence_strength = "MEDIUM-HIGH"
        elif score >= 50:
            verdict = VerdictType.PARTIALLY_TRUE
            evidence_strength = "MEDIUM"
        elif score >= 35:
            verdict = VerdictType.MISLEADING
            evidence_strength = "MEDIUM-LOW"
        elif score >= 20:
            verdict = VerdictType.UNVERIFIED
            evidence_strength = "LOW"
        elif score >= 10:
            verdict = VerdictType.LIKELY_FALSE
            evidence_strength = "LOW"
        else:
            verdict = VerdictType.FALSE
            evidence_strength = "VERY LOW"
        
        if len(supporting) == 0 and len(contradicting) == 0:
            verdict = VerdictType.UNVERIFIED
            evidence_strength = "UNKNOWN"
        
        confidence = min(0.99, 0.5 + (len(supporting) + len(contradicting)) * 0.05)
        if len(supporting) == 0 and len(contradicting) == 0:
            confidence = 0.3
        
        limitations = []
        if len(all_sources) < 3:
            limitations.append("Limited number of sources analyzed")
        if not primary_sources:
            limitations.append("No primary sources found")
        if headline_analysis.get("exaggeration_detected"):
            limitations.append("Headline exaggeration detected")
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "evidence_strength": evidence_strength,
            "limitations": limitations
        }
    
    def _build_response(
        self, verification_id: str, input_type: str, original_text: str,
        claims: List[Claim], verdict: Verdict, supporting: List[Evidence],
        contradicting: List[Evidence], neutral: List[Evidence],
        all_sources: List[Source], primary_sources: List[Source],
        fact_checks: List[FactCheck], headline_analysis: Dict[str, Any],
        article_data: Dict[str, Any], explanation: str
    ) -> Dict[str, Any]:
        from app.schemas.schemas import (
            ClaimSchema, EvidenceSchema, SourceSchema, FactCheckSchema,
            MediaItemSchema, VerdictSchema, TemporalAnalysisSchema,
            HeadlineAnalysisSchema, MediaAnalysisSchema
        )
        
        claim_schemas = [
            ClaimSchema(
                id=c.id,
                text=c.text,
                subject=c.subject,
                action=c.action,
                object=c.object,
                location=c.location,
                date_time=c.date_time,
                numerical_values=c.numerical_values,
                entities=c.entities,
                category=c.category,
                certainty_level=c.certainty_level
            ) for c in claims
        ]
        
        source_map = {s.id: s for s in all_sources}
        
        def evidence_to_schema(e: Evidence):
            source_schema = None
            if e.source_id and e.source_id in source_map:
                s = source_map[e.source_id]
                source_schema = SourceSchema(
                    id=s.id,
                    url=s.url,
                    title=s.title,
                    domain=s.domain,
                    source_type=s.source_type.value,
                    publisher=s.publisher,
                    author=s.author,
                    publication_date=s.publication_date,
                    credibility_score=s.credibility_score,
                    is_independent=s.is_independent
                )
            return EvidenceSchema(
                id=e.id,
                text=e.text,
                evidence_type=e.evidence_type,
                relation=e.relation.value,
                confidence=e.confidence,
                source=source_schema
            )
        
        def source_to_schema(s: Source):
            return SourceSchema(
                id=s.id,
                url=s.url,
                title=s.title,
                domain=s.domain,
                source_type=s.source_type.value,
                publisher=s.publisher,
                author=s.author,
                publication_date=s.publication_date,
                credibility_score=s.credibility_score,
                is_independent=s.is_independent
            )
        
        factcheck_schemas = [
            FactCheckSchema(
                id=fc.id,
                organization=fc.organization,
                claim_checked=fc.claim_checked,
                conclusion=fc.conclusion,
                summary=fc.summary,
                date=fc.date,
                url=fc.url
            ) for fc in fact_checks
        ]
        
        media_items = []
        if article_data.get("images"):
            for img_url in article_data.get("images", [])[:5]:
                media_items.append(MediaItemSchema(
                    id=str(uuid.uuid4()),
                    media_type="image",
                    url=img_url,
                    caption=None,
                    original_context=None,
                    current_context=None,
                    is_reused=False,
                    reuse_evidence=None
                ))
        
        verdict_schema = VerdictSchema(
            id=verdict.id,
            verdict=verdict.verdict.value,
            confidence=verdict.confidence,
            evidence_strength=verdict.evidence_strength,
            explanation=verdict.explanation,
            limitations=verdict.limitations,
            supporting_evidence_count=verdict.supporting_evidence_count,
            contradicting_evidence_count=verdict.contradicting_evidence_count,
            neutral_evidence_count=verdict.neutral_evidence_count
        )
        
        return {
            "verification_id": verification_id,
            "input_type": input_type,
            "original_claim": original_text,
            "claims": claim_schemas,
            "verdict": verdict.verdict.value,
            "confidence": verdict.confidence,
            "evidence_strength": verdict.evidence_strength,
            "supporting_evidence": [evidence_to_schema(e) for e in supporting],
            "contradicting_evidence": [evidence_to_schema(e) for e in contradicting],
            "neutral_evidence": [evidence_to_schema(e) for e in neutral],
            "primary_sources": [source_to_schema(s) for s in primary_sources],
            "fact_checks": factcheck_schemas,
            "source_analysis": [source_to_schema(s) for s in all_sources],
            "temporal_analysis": TemporalAnalysisSchema(
                is_outdated=False,
                original_event_date=article_data.get("date"),
                current_article_date=article_data.get("date"),
                notes=""
            ),
            "headline_analysis": HeadlineAnalysisSchema(
                clickbait_score=headline_analysis.get("clickbait_score", 0.0),
                exaggeration_detected=headline_analysis.get("exaggeration_detected", False),
                headline_body_contradiction=headline_analysis.get("headline_body_contradiction", False),
                notes=headline_analysis.get("notes", [])
            ),
            "media_analysis": MediaAnalysisSchema(
                images=[m for m in media_items if m.media_type == "image"],
                videos=[m for m in media_items if m.media_type == "video"],
                reused_media_count=0,
                unverified_media_count=len(media_items)
            ),
            "explanation": explanation,
            "limitations": verdict.limitations.split("; ") if verdict.limitations else []
        }
