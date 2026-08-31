import json
import uuid
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        self.fallback_model = "gpt-4o-mini"
    
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = False) -> str:
        if not self.client:
            return self._demo_response(prompt, json_mode)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"} if json_mode else None
            )
            return response.choices[0].message.content or ""
        except Exception:
            if self.model != self.fallback_model:
                response = await self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"} if json_mode else None
                )
                return response.choices[0].message.content or ""
            return self._demo_response(prompt, json_mode)
    
    def _demo_response(self, prompt: str, json_mode: bool = False) -> str:
        if json_mode:
            return json.dumps([{"text": "Demo claim extraction - configure OPENAI_API_KEY for real analysis", "subject": "Unknown", "action": "unknown", "object": "unknown", "certainty_level": "low"}])
        return "Demo mode: configure OPENAI_API_KEY for real LLM analysis."
    
    async def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        system_prompt = """You are a claim extraction system. Extract all factual claims from the provided text.
For each claim, provide:
- text: the exact claim text
- subject: who/what is performing the action
- action: what is being done
- object: what is being acted upon
- location: where it happened (if mentioned)
- date_time: when it happened (if mentioned)
- numerical_values: any numbers, percentages, dates
- entities: people, organizations, countries mentioned
- certainty_level: high/medium/low based on language used

Return a JSON array of claims. Never invent claims not present in the text."""
        
        prompt = f"""Extract all factual claims from this text:

{text[:4000]}

Return JSON array:
[
  {{
    "text": "claim text here",
    "subject": "...",
    "action": "...",
    "object": "...",
    "location": "...",
    "date_time": "...",
    "numerical_values": "...",
    "entities": "...",
    "certainty_level": "high|medium|low"
  }}
]

Return ONLY the JSON array."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        
        try:
            claims = json.loads(response)
            if isinstance(claims, dict):
                claims = claims.get("claims", [])
            return claims if isinstance(claims, list) else []
        except json.JSONDecodeError:
            return []
    
    async def classify_category(self, text: str) -> str:
        categories = ["Politics", "Science", "Health", "Technology", "Business", "Sports", "Entertainment", "Environment", "Education", "Crime", "International Affairs", "Local News", "Other"]
        
        prompt = f"""Classify this text into one of these categories: {', '.join(categories)}

Text: {text[:500]}

Return ONLY the category name."""
        
        response = await self._call_llm(prompt)
        for cat in categories:
            if cat.lower() in response.lower():
                return cat
        return "Other"
    
    async def detect_opinion_vs_fact(self, text: str) -> Dict[str, Any]:
        system_prompt = """Determine if the text contains factual claims, opinions, or both.
Return JSON with:
- is_factual: boolean
- is_opinion: boolean
- factual_claims: array of claim texts
- opinion_parts: array of opinion texts
- reasoning: brief explanation"""
        
        prompt = f"""Analyze this text:

{text[:2000]}

Return JSON with is_factual, is_opinion, factual_claims, opinion_parts, reasoning."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_factual": True, "is_opinion": False, "reasoning": "Default assumption"}
    
    async def compare_evidence(self, claim: str, supporting: List[str], contradicting: List[str]) -> Dict[str, Any]:
        system_prompt = """Compare supporting and contradicting evidence for a claim.
Return JSON with:
- assessment: "supports"|"contradicts"|"neutral"|"partially_supports"|"partially_contradicts"
- confidence: 0.0 to 1.0
- reasoning: detailed explanation
- key_factors: array of important factors"""
        
        prompt = f"""Claim: {claim}

Supporting evidence:
{chr(10).join(['- ' + e for e in supporting[:5]])}

Contradicting evidence:
{chr(10).join(['- ' + e for e in contradicting[:5]])}

Return JSON with assessment, confidence, reasoning, key_factors."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "assessment": "neutral",
                "confidence": 0.5,
                "reasoning": "Unable to compare evidence automatically.",
                "key_factors": []
            }
    
    async def analyze_headline(self, headline: str, article: str) -> Dict[str, Any]:
        system_prompt = """Analyze whether the headline accurately represents the article content.
Return JSON with:
- clickbait_score: 0.0 to 1.0
- exaggeration_detected: boolean
- headline_body_contradiction: boolean
- notes: array of specific issues found"""
        
        prompt = f"""Headline: {headline}

Article: {article[:3000]}

Analyze the relationship between headline and article. Return JSON."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "clickbait_score": 0.0,
                "exaggeration_detected": False,
                "headline_body_contradiction": False,
                "notes": ["Analysis could not be completed."]
            }
    
    async def analyze_temporal_context(self, claim_date: Optional[str], source_date: Optional[str]) -> Dict[str, Any]:
        system_prompt = """Analyze temporal context of a claim vs source.
Return JSON with:
- is_outdated: boolean
- is_future_dated: boolean
- notes: explanation"""
        
        prompt = f"""Claim date: {claim_date or "not specified"}
Source date: {source_date or "not specified"}

Analyze if the source is outdated or if there are date issues. Return JSON."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_outdated": False, "is_future_dated": False, "notes": "Date analysis could not be completed."}
    
    async def generate_explanation(self, verdict: str, confidence: float, evidence_summary: str, factors: List[str]) -> str:
        system_prompt = """Generate a clear, concise explanation for a verification verdict.
Be transparent about confidence levels and evidence quality.
Never invent information. Reference the evidence factors provided."""
        
        prompt = f"""Verdict: {verdict}
Confidence: {confidence}
Evidence summary: {evidence_summary}
Factors: {', '.join(factors)}

Generate a brief, clear explanation of why this verdict was reached."""
        
        response = await self._call_llm(prompt, system_prompt)
        return response.strip()
    
    async def analyze_media_reuse(self, caption: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = """Determine if media appears to be reused from an older context.
Return JSON with:
- is_reused: boolean
- original_context: what the media originally showed
- current_context: what the current article claims it shows
- confidence: 0.0 to 1.0"""
        
        results_text = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" for r in search_results[:3]])
        prompt = f"""Current caption: {caption}

Search results about this media:
{results_text}

Determine if this media is reused. Return JSON."""
        
        response = await self._call_llm(prompt, system_prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"is_reused": False, "original_context": "", "current_context": caption, "confidence": 0.0}
