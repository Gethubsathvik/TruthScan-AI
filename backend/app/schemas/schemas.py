from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InputType(str, Enum):
    URL = "url"
    HEADLINE = "headline"
    ARTICLE = "article"
    CLAIM = "claim"

class VerificationRequestCreate(BaseModel):
    input_type: InputType
    input_text: str
    input_url: Optional[HttpUrl] = None

class VerificationRequestResponse(BaseModel):
    id: str
    input_type: str
    original_text: str
    input_url: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class ClaimSchema(BaseModel):
    id: str
    text: str
    subject: Optional[str] = None
    action: Optional[str] = None
    object: Optional[str] = None
    location: Optional[str] = None
    date_time: Optional[str] = None
    numerical_values: Optional[str] = None
    entities: Optional[str] = None
    category: Optional[str] = None
    certainty_level: Optional[str] = None

class SourceSchema(BaseModel):
    id: int
    url: Optional[str] = None
    title: Optional[str] = None
    domain: Optional[str] = None
    source_type: str
    publisher: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[str] = None
    credibility_score: float
    is_independent: bool

class EvidenceSchema(BaseModel):
    id: str
    text: str
    evidence_type: str
    relation: str
    confidence: float
    source: Optional[SourceSchema] = None
    claim: Optional[ClaimSchema] = None

class FactCheckSchema(BaseModel):
    id: int
    organization: Optional[str] = None
    claim_checked: Optional[str] = None
    conclusion: Optional[str] = None
    summary: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None

class MediaItemSchema(BaseModel):
    id: str
    media_type: str
    url: Optional[str] = None
    caption: Optional[str] = None
    original_context: Optional[str] = None
    current_context: Optional[str] = None
    is_reused: bool
    reuse_evidence: Optional[str] = None

class VerdictSchema(BaseModel):
    id: str
    verdict: str
    confidence: float
    evidence_strength: Optional[str] = None
    explanation: str
    limitations: Optional[str] = None
    supporting_evidence_count: int
    contradicting_evidence_count: int
    neutral_evidence_count: int

class TemporalAnalysisSchema(BaseModel):
    is_outdated: bool
    original_event_date: Optional[str] = None
    current_article_date: Optional[str] = None
    time_gap_years: Optional[int] = None
    notes: Optional[str] = None

class HeadlineAnalysisSchema(BaseModel):
    clickbait_score: float
    exaggeration_detected: bool
    headline_body_contradiction: bool
    notes: List[str]

class MediaAnalysisSchema(BaseModel):
    images: List[MediaItemSchema]
    videos: List[MediaItemSchema]
    reused_media_count: int
    unverified_media_count: int

class VerificationResultResponse(BaseModel):
    verification_id: str
    input_type: str
    original_claim: str
    claims: List[ClaimSchema]
    verdict: str
    confidence: float
    evidence_strength: str
    supporting_evidence: List[EvidenceSchema]
    contradicting_evidence: List[EvidenceSchema]
    neutral_evidence: List[EvidenceSchema]
    primary_sources: List[SourceSchema]
    fact_checks: List[FactCheckSchema]
    source_analysis: List[SourceSchema]
    temporal_analysis: TemporalAnalysisSchema
    headline_analysis: HeadlineAnalysisSchema
    media_analysis: MediaAnalysisSchema
    explanation: str
    limitations: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: str
    suggestion: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
