import type { Verdict } from '../types'

interface VerdictCardProps {
  verdict: Verdict
}

const VERDICT_COLORS: Record<string, string> = {
  verified: 'bg-green-100 text-green-800 border-green-300',
  likely_true: 'bg-blue-100 text-blue-800 border-blue-300',
  partially_true: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  misleading: 'bg-orange-100 text-orange-800 border-orange-300',
  unverified: 'bg-gray-100 text-gray-800 border-gray-300',
  likely_false: 'bg-red-100 text-red-800 border-red-300',
  false: 'bg-red-100 text-red-800 border-red-300',
}

export default function VerdictCard({ verdict }: VerdictCardProps) {
  const colorClass = VERDICT_COLORS[verdict.verdict] || VERDICT_COLORS.unverified

  return (
    <div className={`border-2 rounded-lg p-8 mb-8 ${colorClass}`}>
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-2">
          {verdict.verdict.replace(/_/g, ' ').toUpperCase()}
        </h1>
        <p className="text-lg">
          Evidence Confidence: {Math.round(verdict.confidence * 100)}%
        </p>
        {verdict.evidence_strength && (
          <p className="text-sm mt-1">
            Evidence Strength: {verdict.evidence_strength}
          </p>
        )}
      </div>
    </div>
  )
}
