export interface Claim {
  id: string
  text: string
  subject?: string
  action?: string
  object?: string
  location?: string
  date_time?: string
  numerical_values?: string
  entities?: string
  category?: string
  certainty_level?: string
}

export interface Source {
  id: number
  url?: string
  title?: string
  domain?: string
  source_type: string
  publisher?: string
  author?: string
  publication_date?: string
  credibility_score: number
  is_independent: boolean
}

export interface Evidence {
  id: string
  text: string
  evidence_type: string
  relation: string
  confidence: number
  source?: Source
  claim?: Claim
}

export interface FactCheck {
  id: number
  organization?: string
  claim_checked?: string
  conclusion?: string
  summary?: string
  date?: string
  url?: string
}

export interface MediaItem {
  id: string
  media_type: string
  url?: string
  caption?: string
  original_context?: string
  current_context?: string
  is_reused: boolean
  reuse_evidence?: string
}

export interface Verdict {
  id: string
  verdict: string
  confidence: number
  evidence_strength?: string
  explanation: string
  limitations?: string
  supporting_evidence_count: number
  contradicting_evidence_count: number
  neutral_evidence_count: number
}

export interface TemporalAnalysis {
  is_outdated: boolean
  original_event_date?: string
  current_article_date?: string
  time_gap_years?: number
  notes?: string
}

export interface HeadlineAnalysis {
  clickbait_score: number
  exaggeration_detected: boolean
  headline_body_contradiction: boolean
  notes: string[]
}

export interface MediaAnalysis {
  images: MediaItem[]
  videos: MediaItem[]
  reused_media_count: number
  unverified_media_count: number
}

export interface VerificationResult {
  verification_id: string
  input_type: string
  original_claim: string
  claims: Claim[]
  verdict: string
  confidence: number
  evidence_strength: string
  supporting_evidence: Evidence[]
  contradicting_evidence: Evidence[]
  neutral_evidence: Evidence[]
  primary_sources: Source[]
  fact_checks: FactCheck[]
  source_analysis: Source[]
  temporal_analysis: TemporalAnalysis
  headline_analysis: HeadlineAnalysis
  media_analysis: MediaAnalysis
  explanation: string
  limitations: string[]
}

export interface VerificationRequest {
  id: string
  input_type: string
  original_text: string
  input_url?: string
  status: string
  created_at: string
  completed_at?: string
}

export type InputType = 'url' | 'headline' | 'article' | 'claim'

export type VerdictType = 'verified' | 'likely_true' | 'partially_true' | 'misleading' | 'unverified' | 'likely_false' | 'false'
