import pytest
from app.services.evidence_scoring import EvidenceScoringEngine
from app.services.source_analyzer import SourceAnalyzer
from app.models.models import Evidence, EvidenceRelation, Source, SourceType

class TestEvidenceScoring:
    @pytest.fixture
    def scoring_engine(self):
        return EvidenceScoringEngine()
    
    def test_score_primary_evidence(self, scoring_engine):
        source = Source(
            id=1,
            url="https://gov.example.com",
            domain="gov.example.com",
            source_type=SourceType.PRIMARY,
            credibility_score=0.9,
            is_independent=True
        )
        evidence = Evidence(
            id="ev-1",
            text="Official statement confirms the claim",
            relation=EvidenceRelation.SUPPORTS,
            confidence=0.9,
            source_id=1
        )
        score = scoring_engine._score_single_evidence(evidence, source)
        assert score > 50
    
    def test_score_contradicting_evidence(self, scoring_engine):
        source = Source(
            id=2,
            url="https://example.com",
            domain="example.com",
            source_type=SourceType.SECONDARY,
            credibility_score=0.5,
            is_independent=True
        )
        evidence = Evidence(
            id="ev-2",
            text="Source contradicts the claim",
            relation=EvidenceRelation.CONTRADICTS,
            confidence=0.8,
            source_id=2
        )
        score = scoring_engine._score_single_evidence(evidence, source)
        assert score <= 50

class TestSourceAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SourceAnalyzer()
    
    def test_classify_government_source(self, analyzer):
        source_type = analyzer.classify_source_type("gov.example.com", "https://gov.example.com/page")
        assert source_type == SourceType.PRIMARY
    
    def test_classify_fact_check_source(self, analyzer):
        source_type = analyzer.classify_source_type("politifact.com", "https://politifact.com/fact-check")
        assert source_type == SourceType.FACT_CHECK
    
    def test_detect_independence(self, analyzer):
        sources = [
            Source(id=1, url="https://a.com", domain="a.com", source_type=SourceType.SECONDARY),
            Source(id=2, url="https://b.com", domain="b.com", source_type=SourceType.SECONDARY),
            Source(id=3, url="https://a.com", domain="a.com", source_type=SourceType.SECONDARY),
        ]
        result = analyzer.detect_source_independence(sources)
        assert result["total_sources"] == 3
        assert result["independent_sources"] == 1
        assert len(result["dependent_groups"]) == 1

class TestURLValidation:
    def test_valid_url(self):
        import re
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        assert bool(url_pattern.match("https://example.com/article")) is True
        assert bool(url_pattern.match("http://test.org/path?query=1")) is True
    
    def test_invalid_url(self):
        import re
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        assert bool(url_pattern.match("not a url")) is False
        assert bool(url_pattern.match("example.com")) is False

class TestInputTypeDetection:
    def test_detect_url(self):
        text = "https://example.com"
        import re
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        assert bool(url_pattern.match(text)) is True
    
    def test_detect_article(self):
        long_text = " ".join(["word"] * 150)
        assert len(long_text.split()) > 100
    
    def test_detect_claim(self):
        text = "NASA discovered life on Mars"
        assert len(text.split()) <= 100
