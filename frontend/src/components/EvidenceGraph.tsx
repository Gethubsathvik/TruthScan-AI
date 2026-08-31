import { useState } from 'react'
import type { Evidence, Source } from '../types'

interface EvidenceGraphProps {
  claim: string
  supporting: Evidence[]
  contradicting: Evidence[]
  neutral: Evidence[]
  primarySources: Source[]
}

export default function EvidenceGraph({
  claim,
  supporting,
  contradicting,
  neutral,
  primarySources
}: EvidenceGraphProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'claim': return '#4F46E5'
      case 'primary': return '#10B981'
      case 'support': return '#3B82F6'
      case 'contradict': return '#EF4444'
      case 'neutral': return '#6B7280'
      default: return '#9CA3AF'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Evidence Graph</h3>
      
      <div className="flex flex-col items-center">
        <div
          className="px-4 py-2 rounded-lg text-white font-medium cursor-pointer"
          style={{ backgroundColor: getNodeColor('claim') }}
          onClick={() => setSelectedNode('claim')}
        >
          CLAIM
        </div>
        
        <div className="w-px h-8 bg-gray-300"></div>
        
        <div className="flex gap-8">
          <div className="flex flex-col items-center">
            <div
              className="px-4 py-2 rounded-lg text-white font-medium cursor-pointer"
              style={{ backgroundColor: getNodeColor('primary') }}
              onClick={() => setSelectedNode('primary')}
            >
              PRIMARY SOURCES ({primarySources.length})
            </div>
            <div className="w-px h-8 bg-gray-300"></div>
            <div className="flex gap-4">
              <div
                className="px-3 py-1 rounded text-white text-sm cursor-pointer"
                style={{ backgroundColor: getNodeColor('support') }}
                onClick={() => setSelectedNode('support')}
              >
                SUPPORT ({supporting.length})
              </div>
              <div
                className="px-3 py-1 rounded text-white text-sm cursor-pointer"
                style={{ backgroundColor: getNodeColor('contradict') }}
                onClick={() => setSelectedNode('contradict')}
              >
                CONTRADICT ({contradicting.length})
              </div>
            </div>
          </div>
          
          <div className="flex flex-col items-center">
            <div
              className="px-4 py-2 rounded-lg text-white font-medium cursor-pointer"
              style={{ backgroundColor: getNodeColor('neutral') }}
              onClick={() => setSelectedNode('neutral')}
            >
              NEUTRAL ({neutral.length})
            </div>
          </div>
        </div>
        
        <div className="w-px h-8 bg-gray-300"></div>
        
        <div
          className="px-4 py-2 rounded-lg text-white font-medium"
          style={{ backgroundColor: getNodeColor('verdict') }}
        >
          VERDICT
        </div>
      </div>

      {selectedNode && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">
            {selectedNode === 'claim' && 'Original Claim'}
            {selectedNode === 'primary' && 'Primary Sources'}
            {selectedNode === 'support' && 'Supporting Evidence'}
            {selectedNode === 'contradict' && 'Contradicting Evidence'}
            {selectedNode === 'neutral' && 'Neutral Evidence'}
          </h4>
          
          {selectedNode === 'claim' && (
            <p className="text-gray-700">{claim}</p>
          )}
          
          {selectedNode === 'primary' && (
            <ul className="space-y-2">
              {primarySources.map((source) => (
                <li key={source.id} className="text-sm">
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                    {source.title || source.domain}
                  </a>
                  <span className="text-gray-500 text-xs ml-2">({source.source_type})</span>
                </li>
              ))}
              {primarySources.length === 0 && (
                <li className="text-gray-500 text-sm">No primary sources found</li>
              )}
            </ul>
          )}
          
          {selectedNode === 'support' && (
            <ul className="space-y-2">
              {supporting.slice(0, 5).map((evidence) => (
                <li key={evidence.id} className="text-sm text-gray-700">
                  {evidence.text}
                </li>
              ))}
            </ul>
          )}
          
          {selectedNode === 'contradict' && (
            <ul className="space-y-2">
              {contradicting.slice(0, 5).map((evidence) => (
                <li key={evidence.id} className="text-sm text-gray-700">
                  {evidence.text}
                </li>
              ))}
            </ul>
          )}
          
          {selectedNode === 'neutral' && (
            <ul className="space-y-2">
              {neutral.slice(0, 5).map((evidence) => (
                <li key={evidence.id} className="text-sm text-gray-700">
                  {evidence.text}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
