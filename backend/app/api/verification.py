from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.models import (
    VerificationRequest, Claim, Evidence, Source, FactCheck,
    MediaItem, Verdict, User
)
from app.schemas.schemas import (
    VerificationRequestCreate, VerificationRequestResponse,
    VerificationResultResponse, ErrorResponse, HealthResponse,
    ClaimSchema, EvidenceSchema, SourceSchema, FactCheckSchema,
    MediaItemSchema, VerdictSchema
)

router = APIRouter(prefix="/api/v1", tags=["verification"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="sqlite"
    )

@router.post("/verify", response_model=VerificationResultResponse)
async def verify_claim(
    request: VerificationRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    verification_id = str(uuid.uuid4())
    
    verification = VerificationRequest(
        id=verification_id,
        input_type=request.input_type.value,
        original_text=request.input_text,
        input_url=str(request.input_url) if request.input_url else None,
        status="processing"
    )
    db.add(verification)
    await db.commit()
    
    try:
        from app.services.verification_pipeline import VerificationPipeline
        pipeline = VerificationPipeline(db)
        result = await pipeline.run(verification_id, request.input_text, request.input_type.value)
        return result
    except Exception as e:
        verification.status = "failed"
        verification.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.get("/verification/{verification_id}", response_model=VerificationResultResponse)
async def get_verification_result(
    verification_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VerificationRequest).where(VerificationRequest.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    if verification.status != "completed":
        raise HTTPException(status_code=202, detail="Verification still processing")
    
    claims_result = await db.execute(
        select(Claim).where(Claim.verification_request_id == verification_id)
    )
    claims = claims_result.scalars().all()
    
    verdict_result = await db.execute(
        select(Verdict).where(Verdict.verification_request_id == verification_id)
    )
    verdict = verdict_result.scalar_one_or_none()
    
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.verification_request_id == verification_id)
    )
    evidence_items = evidence_result.scalars().all()
    
    source_ids = [e.source_id for e in evidence_items if e.source_id]
    sources_result = await db.execute(
        select(Source).where(Source.id.in_(source_ids))
    )
    sources = sources_result.scalars().all()
    
    source_map = {s.id: s for s in sources}
    
    fact_check_result = await db.execute(
        select(FactCheck).where(FactCheck.verification_request_id == verification_id)
    )
    fact_checks = fact_check_result.scalars().all()
    
    media_result = await db.execute(
        select(MediaItem).where(MediaItem.verification_request_id == verification_id)
    )
    media_items = media_result.scalars().all()
    
    supporting = [e for e in evidence_items if e.relation == "supports"]
    contradicting = [e for e in evidence_items if e.relation == "contradicts"]
    neutral = [e for e in evidence_items if e.relation == "neutral"]
    
    primary_sources = [s for s in sources if s.source_type == "primary"]
    
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
            relation=e.relation,
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
    
    def factcheck_to_schema(fc: FactCheck):
        return FactCheckSchema(
            id=fc.id,
            organization=fc.organization,
            claim_checked=fc.claim_checked,
            conclusion=fc.conclusion,
            summary=fc.summary,
            date=fc.date,
            url=fc.url
        )
    
    def media_to_schema(m: MediaItem):
        return MediaItemSchema(
            id=m.id,
            media_type=m.media_type,
            url=m.url,
            caption=m.caption,
            original_context=m.original_context,
            current_context=m.current_context,
            is_reused=m.is_reused,
            reuse_evidence=m.reuse_evidence
        )
    
    verdict_schema = None
    if verdict:
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
    
    return VerificationResultResponse(
        verification_id=verification.id,
        input_type=verification.input_type,
        original_claim=verification.original_text,
        claims=claim_schemas,
        verdict=verdict_schema.verdict if verdict_schema else "unverified",
        confidence=verdict_schema.confidence if verdict_schema else 0.0,
        evidence_strength=verdict_schema.evidence_strength if verdict_schema else "unknown",
        supporting_evidence=[evidence_to_schema(e) for e in supporting],
        contradicting_evidence=[evidence_to_schema(e) for e in contradicting],
        neutral_evidence=[evidence_to_schema(e) for e in neutral],
        primary_sources=[source_to_schema(s) for s in primary_sources],
        fact_checks=[factcheck_to_schema(fc) for fc in fact_checks],
        source_analysis=[source_to_schema(s) for s in sources],
        temporal_analysis={"is_outdated": False, "notes": "Temporal analysis pending"},
        headline_analysis={"clickbait_score": 0.0, "exaggeration_detected": False, "headline_body_contradiction": False, "notes": []},
        media_analysis={
            "images": [media_to_schema(m) for m in media_items if m.media_type == "image"],
            "videos": [media_to_schema(m) for m in media_items if m.media_type == "video"],
            "reused_media_count": sum(1 for m in media_items if m.is_reused),
            "unverified_media_count": sum(1 for m in media_items if not m.is_reused)
        },
        explanation=verdict_schema.explanation if verdict_schema else "Verification not completed.",
        limitations=[verdict_schema.limitations] if verdict_schema and verdict_schema.limitations else []
    )

@router.get("/history", response_model=List[VerificationRequestResponse])
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VerificationRequest)
        .order_by(VerificationRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    requests = result.scalars().all()
    
    return [
        VerificationRequestResponse(
            id=r.id,
            input_type=r.input_type,
            original_text=r.original_text[:200],
            input_url=r.input_url,
            status=r.status,
            created_at=r.created_at,
            completed_at=r.completed_at
        ) for r in requests
    ]

@router.delete("/history/{verification_id}")
async def delete_history_item(
    verification_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(VerificationRequest).where(VerificationRequest.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    await db.delete(verification)
    await db.commit()
    return {"message": "Deleted successfully"}

@router.get("/auto-scan/sources")
async def get_scan_sources():
    from app.services.auto_scan_service import AutoScanService
    service = AutoScanService()
    return {
        "news_sources": service.sources_config.get("news_sources", []),
        "article_sources": service.sources_config.get("article_sources", [])
    }

@router.get("/auto-scan/trending")
async def get_trending_news(limit: int = Query(20, ge=1, le=50)):
    from app.services.auto_scan_service import AutoScanService
    service = AutoScanService()
    trending = await service.get_trending_news(limit=limit)
    return {
        "trending": trending,
        "count": len(trending),
        "fetched_at": datetime.utcnow().isoformat()
    }

@router.get("/auto-scan/daily-updates")
async def get_daily_updates(limit: int = Query(20, ge=1, le=50)):
    from app.services.auto_scan_service import AutoScanService
    service = AutoScanService()
    updates = await service.get_daily_updates(limit=limit)
    return {
        "updates": updates,
        "count": len(updates),
        "fetched_at": datetime.utcnow().isoformat()
    }

@router.post("/auto-scan/run")
async def run_auto_scan():
    from app.services.auto_scan_service import AutoScanService
    service = AutoScanService()
    results = await service.scan_all_sources(max_per_category=5)
    return {
        "scanned_at": datetime.utcnow().isoformat(),
        "sources_scanned": len(results),
        "results": results
    }

@router.post("/auto-scan/verify-batch")
async def verify_batch_articles(articles: List[Dict[str, Any]]):
    from app.services.auto_scan_service import AutoScanService
    service = AutoScanService()
    results = await service.batch_verify_articles(articles[:10])
    return {
        "verified_at": datetime.utcnow().isoformat(),
        "total_articles": len(results),
        "results": [r if not isinstance(r, Exception) else {"error": str(r)} for r in results]
    }

@router.post("/auto-scan/scan-urls")
async def scan_urls(urls: List[str]):
    from app.services.auto_scan_service import AutoScanService
    from app.services.article_extraction_service import ArticleExtractionService
    from app.services.verification_pipeline import VerificationPipeline
    
    extraction_service = ArticleExtractionService()
    pipeline = VerificationPipeline(None)
    
    results = []
    for url in urls[:20]:
        try:
            article_data = await extraction_service.extract_from_url(url)
            if article_data.get("error"):
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": article_data.get("message", "Extraction failed"),
                    "verdict": "unverified"
                })
                continue
            
            text = article_data.get("text", "")
            title = article_data.get("title", "")
            
            if not text:
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": "No content extracted",
                    "verdict": "unverified"
                })
                continue
            
            verification_text = f"{title}. {text}" if title else text
            verification_id = str(uuid.uuid4())
            
            verification_result = await pipeline._run_pipeline(verification_id, verification_text, "url")
            
            results.append({
                "url": url,
                "status": "completed",
                "title": title,
                "verdict": verification_result.get("verdict", "unverified"),
                "confidence": verification_result.get("confidence", 0.0),
                "evidence_strength": verification_result.get("evidence_strength", "unknown"),
                "explanation": verification_result.get("explanation", ""),
                "supporting_evidence_count": len(verification_result.get("supporting_evidence", [])),
                "contradicting_evidence_count": len(verification_result.get("contradicting_evidence", [])),
                "limitations": verification_result.get("limitations", [])
            })
        except Exception as e:
            results.append({
                "url": url,
                "status": "error",
                "error": str(e),
                "verdict": "unverified"
            })
    
    return {
        "scanned_at": datetime.utcnow().isoformat(),
        "total_urls": len(urls),
        "processed_urls": len(results),
        "results": results
    }
