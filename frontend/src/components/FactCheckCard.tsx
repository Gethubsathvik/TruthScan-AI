import type { FactCheck } from '../types'

interface FactCheckCardProps {
  factCheck: FactCheck
}

export default function FactCheckCard({ factCheck }: FactCheckCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-gray-900">{factCheck.organization}</h4>
        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
          {factCheck.conclusion}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-2">{factCheck.summary}</p>
      {factCheck.date && (
        <p className="text-xs text-gray-500 mb-2">
          Date: {new Date(factCheck.date).toLocaleDateString()}
        </p>
      )}
      {factCheck.url && (
        <a
          href={factCheck.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-indigo-600 hover:underline"
        >
          View Fact Check →
        </a>
      )}
    </div>
  )
}
