from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import enum

from app.core.database import Base

class SourceType(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FACT_CHECK = "fact_check"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"

class EvidenceRelation(str, enum.Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    NEUTRAL = "neutral"
    PARTIALLY_SUPPORTS = "partially_supports"
    PARTIALLY_CONTRADICTS = "partially_contradicts"

class VerdictType(str, enum.Enum):
    VERIFIED = "verified"
    LIKELY_TRUE = "likely_true"
    PARTIALLY_TRUE = "partially_true"
    MISLEADING = "misleading"
    UNVERIFIED = "unverified"
    LIKELY_FALSE = "likely_false"
    FALSE = "false"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_requests: Mapped[List["VerificationRequest"]] = relationship(back_populates="user")

class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    input_type: Mapped[str] = mapped_column(String(50))
    original_text: Mapped[str] = mapped_column(Text)
    input_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="processing")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped[Optional["User"]] = relationship(back_populates="verification_requests")
    claims: Mapped[List["Claim"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")
    verdicts: Mapped[List["Verdict"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")
    evidence_items: Mapped[List["Evidence"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")
    sources: Mapped[List["Source"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")
    media_items: Mapped[List["MediaItem"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")
    fact_checks: Mapped[List["FactCheck"]] = relationship(back_populates="verification_request", cascade="all, delete-orphan")

class Claim(Base):
    __tablename__ = "claims"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    text: Mapped[str] = mapped_column(Text)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    object: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_time: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    numerical_values: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entities: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    certainty_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="claims")
    evidence_items: Mapped[List["Evidence"]] = relationship(back_populates="claim")

class Source(Base):
    __tablename__ = "sources"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), default=SourceType.UNKNOWN)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credibility_score: Mapped[Float] = mapped_column(Float, default=0.5)
    is_independent: Mapped[bool] = mapped_column(Boolean, default=False)
    original_source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="sources")
    evidence_items: Mapped[List["Evidence"]] = relationship(back_populates="source")

class Evidence(Base):
    __tablename__ = "evidence"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    claim_id: Mapped[Optional[str]] = mapped_column(ForeignKey("claims.id"), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    evidence_type: Mapped[str] = mapped_column(String(50), default="text")
    relation: Mapped[EvidenceRelation] = mapped_column(SQLEnum(EvidenceRelation), default=EvidenceRelation.NEUTRAL)
    confidence: Mapped[Float] = mapped_column(Float, default=0.0)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="evidence_items")
    claim: Mapped[Optional["Claim"]] = relationship(back_populates="evidence_items")
    source: Mapped[Optional["Source"]] = relationship(back_populates="evidence_items")

class FactCheck(Base):
    __tablename__ = "fact_checks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    claim_checked: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conclusion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="fact_checks")

class MediaItem(Base):
    __tablename__ = "media_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    media_type: Mapped[str] = mapped_column(String(50))
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reused: Mapped[bool] = mapped_column(Boolean, default=False)
    reuse_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="media_items")

class Verdict(Base):
    __tablename__ = "verdicts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    verification_request_id: Mapped[str] = mapped_column(ForeignKey("verification_requests.id"))
    verdict: Mapped[VerdictType] = mapped_column(SQLEnum(VerdictType))
    confidence: Mapped[Float] = mapped_column(Float)
    evidence_strength: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    contradicting_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    verification_request: Mapped[Optional["VerificationRequest"]] = relationship(back_populates="verdicts")
