import type { Evidence } from '../types'

interface EvidenceCardProps {
  evidence: Evidence
  type: 'supporting' | 'contradicting' | 'neutral'
}

const typeStyles = {
  supporting: 'border-green-500 bg-green-50',
  contradicting: 'border-red-500 bg-red-50',
  neutral: 'border-gray-500 bg-gray-50',
}

export default function EvidenceCard({ evidence, type }: EvidenceCardProps) {
  return (
    <div className={`border-l-4 rounded-r-lg p-4 ${typeStyles[type]}`}>
      <p className="text-sm text-gray-700 mb-2">{evidence.text}</p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">
          Confidence: {Math.round(evidence.confidence * 100)}%
        </span>
        <span className="text-xs px-2 py-1 bg-white rounded text-gray-600">
          {evidence.evidence_type}
        </span>
      </div>
      {evidence.source && (
        <div className="mt-2 text-xs text-gray-500">
          Source: {evidence.source.title || evidence.source.domain}
        </div>
      )}
    </div>
  )
}
