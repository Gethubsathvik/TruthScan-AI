import type { Source } from '../types'

interface SourceCardProps {
  source: Source
}

export default function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="border-l-4 border-indigo-500 pl-4 py-2">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">
            {source.title || source.domain}
          </h4>
          <p className="text-sm text-gray-600">{source.url}</p>
          <div className="flex gap-2 mt-2">
            <span className="px-2 py-1 bg-indigo-100 text-indigo-800 text-xs rounded">
              {source.source_type}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
              Credibility: {Math.round(source.credibility_score * 100)}%
            </span>
            {source.is_independent && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                Independent
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
