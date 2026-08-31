import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getVerificationResult } from '../services/api'
import type { VerificationResult } from '../types'

const VERDICT_COLORS: Record<string, string> = {
  verified: 'bg-green-100 text-green-800 border-green-300',
  likely_true: 'bg-blue-100 text-blue-800 border-blue-300',
  partially_true: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  misleading: 'bg-orange-100 text-orange-800 border-orange-300',
  unverified: 'bg-gray-100 text-gray-800 border-gray-300',
  likely_false: 'bg-red-100 text-red-800 border-red-300',
  false: 'bg-red-100 text-red-800 border-red-300',
}

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    
    const fetchResult = async () => {
      try {
        const data = await getVerificationResult(id)
        setResult(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load verification result')
      } finally {
        setLoading(false)
      }
    }
    
    fetchResult()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading verification result...</p>
        </div>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Result not found'}</p>
          <Link to="/" className="text-indigo-600 hover:underline">
            Go back home
          </Link>
        </div>
      </div>
    )
  }

  const verdictColor = VERDICT_COLORS[result.verdict] || VERDICT_COLORS.unverified

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <Link to="/" className="text-indigo-600 hover:underline text-sm">
              ← Back to Home
            </Link>
          </div>

          <div className={`border-2 rounded-lg p-8 mb-8 ${verdictColor}`}>
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-2">
                {result.verdict.replace(/_/g, ' ').toUpperCase()}
              </h1>
              <p className="text-lg">
                Evidence Confidence: {Math.round(result.confidence * 100)}%
              </p>
              {result.evidence_strength && (
                <p className="text-sm mt-1">
                  Evidence Strength: {result.evidence_strength}
                </p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Original Claim</h2>
            <p className="text-gray-700">{result.original_claim}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-green-700">
                Supporting Evidence ({result.supporting_evidence.length})
              </h3>
              {result.supporting_evidence.length === 0 ? (
                <p className="text-gray-500 text-sm">No supporting evidence found</p>
              ) : (
                <ul className="space-y-3">
                  {result.supporting_evidence.map((evidence) => (
                    <li key={evidence.id} className="border-l-4 border-green-500 pl-4">
                      <p className="text-sm text-gray-700">{evidence.text}</p>
                      {evidence.source && (
                        <p className="text-xs text-gray-500 mt-1">
                          Source: {evidence.source.title || evidence.source.domain}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 text-red-700">
                Contradicting Evidence ({result.contradicting_evidence.length})
              </h3>
              {result.contradicting_evidence.length === 0 ? (
                <p className="text-gray-500 text-sm">No contradicting evidence found</p>
              ) : (
                <ul className="space-y-3">
                  {result.contradicting_evidence.map((evidence) => (
                    <li key={evidence.id} className="border-l-4 border-red-500 pl-4">
                      <p className="text-sm text-gray-700">{evidence.text}</p>
                      {evidence.source && (
                        <p className="text-xs text-gray-500 mt-1">
                          Source: {evidence.source.title || evidence.source.domain}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold mb-2 text-yellow-800">Demo Mode</h3>
            <p className="text-yellow-700">
              This verification is running in demo mode because API keys are not configured. 
              Add <code className="bg-yellow-100 px-1 rounded">OPENAI_API_KEY</code> and a search API key to the backend <code className="bg-yellow-100 px-1 rounded">.env</code> file for real-time evidence verification.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Explanation</h3>
            <p className="text-gray-700">{result.explanation}</p>
          </div>

          {result.limitations.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold mb-2 text-yellow-800">Limitations</h3>
              <ul className="list-disc list-inside text-yellow-700">
                {result.limitations.map((limitation, index) => (
                  <li key={index}>{limitation}</li>
                ))}
              </ul>
            </div>
          )}

          {result.primary_sources.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Primary Sources</h3>
              <div className="space-y-3">
                {result.primary_sources.map((source) => (
                  <div key={source.id} className="border-l-4 border-indigo-500 pl-4">
                    <p className="font-medium text-gray-900">{source.title || source.domain}</p>
                    <p className="text-sm text-gray-600">{source.url}</p>
                    <span className="inline-block mt-1 px-2 py-1 bg-indigo-100 text-indigo-800 text-xs rounded">
                      {source.source_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
