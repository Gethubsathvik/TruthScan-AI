from typing import List, Dict, Any, Optional
from app.models.models import Evidence, Source, SourceType, EvidenceRelation

class EvidenceScoringEngine:
    def __init__(self):
        self.weights = {
            "primary_evidence": 30,
            "independent_confirmation": 20,
            "reputable_secondary": 10,
            "direct_documentation": 20,
            "strong_contradiction": -30,
            "unreliable_source": -10,
            "outdated_context": -20,
            "headline_exaggeration": -10,
            "no_supporting_evidence": -15,
        }
    
    def score_evidence_group(self, evidences: List[Evidence], sources: List[Source]) -> float:
        if not evidences:
            return 0.0
        
        source_map = {s.id: s for s in sources}
        total_score = 0.0
        
        for evidence in evidences:
            source = source_map.get(evidence.source_id) if evidence.source_id else None
            score = self._score_single_evidence(evidence, source)
            total_score += score * evidence.confidence
        
        return min(100.0, max(0.0, total_score))
    
    def _score_single_evidence(self, evidence: Evidence, source: Optional[Source]) -> float:
        score = 50.0
        
        if source:
            if source.source_type == SourceType.PRIMARY:
                score += self.weights["primary_evidence"]
            elif source.source_type == SourceType.SECONDARY:
                score += self.weights["reputable_secondary"]
            elif source.source_type == SourceType.FACT_CHECK:
                score += 15
            
            if source.is_independent:
                score += self.weights["independent_confirmation"]
            
            if source.credibility_score > 0.8:
                score += 10
            elif source.credibility_score < 0.4:
                score += self.weights["unreliable_source"]
        
        if evidence.relation == EvidenceRelation.CONTRADICTS:
            score += self.weights["strong_contradiction"]
        elif evidence.relation == EvidenceRelation.SUPPORTS:
            score += 10
        elif evidence.relation == EvidenceRelation.PARTIALLY_CONTRADICTS:
            score += self.weights["strong_contradiction"] // 2
        
        return min(100.0, max(0.0, score))
    
    def calculate_confidence(self, supporting: int, contradicting: int, neutral: int, total_sources: int) -> float:
        if total_sources == 0:
            return 0.3
        
        evidence_count = supporting + contradicting + neutral
        if evidence_count == 0:
            return 0.3
        
        base_confidence = 0.5
        evidence_factor = min(0.3, evidence_count * 0.03)
        source_factor = min(0.2, total_sources * 0.02)
        
        if contradicting > 0 and supporting > 0:
            conflict_penalty = min(0.15, abs(supporting - contradicting) * 0.01)
            base_confidence -= conflict_penalty
        
        confidence = base_confidence + evidence_factor + source_factor
        return min(0.99, max(0.1, confidence))
    
    def determine_evidence_strength(self, supporting: int, contradicting: int, primary_sources: int) -> str:
        if primary_sources >= 2 and supporting >= 3 and contradicting == 0:
            return "HIGH"
        elif primary_sources >= 1 and supporting >= 2:
            return "MEDIUM-HIGH"
        elif supporting >= 2:
            return "MEDIUM"
        elif supporting >= 1:
            return "LOW"
        else:
            return "VERY LOW"
