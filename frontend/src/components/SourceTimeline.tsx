import type { VerificationResult } from '../types'

interface SourceTimelineProps {
  result: VerificationResult
}

export default function SourceTimeline({ result }: SourceTimelineProps) {

  const timelineEvents = [
    {
      year: result.temporal_analysis.original_event_date
        ? new Date(result.temporal_analysis.original_event_date).getFullYear()
        : 2024,
      label: 'Original Event / Source Publication',
      description: 'When the evidence was originally published or the event occurred.',
      type: 'source'
    },
    {
      year: new Date().getFullYear(),
      label: 'Current Verification',
      description: 'This verification was performed using current web evidence.',
      type: 'verification'
    }
  ]

  if (result.headline_analysis.exaggeration_detected) {
    timelineEvents.push({
      year: new Date().getFullYear(),
      label: 'Headline Exaggeration Detected',
      description: 'The headline significantly exaggerates the article content.',
      type: 'warning'
    })
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Source Timeline</h3>
      
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
        
        <div className="space-y-6">
          {timelineEvents.map((event, index) => (
            <div key={index} className="relative flex items-start">
              <div
                className={`absolute left-4 w-3 h-3 rounded-full transform -translate-x-1.5 ${
                  event.type === 'warning'
                    ? 'bg-red-500'
                    : event.type === 'source'
                    ? 'bg-blue-500'
                    : 'bg-green-500'
                }`}
              ></div>
              
              <div className="ml-8 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-500">
                    {event.year}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                    {event.type}
                  </span>
                </div>
                <h4 className="font-medium text-gray-900 mt-1">{event.label}</h4>
                <p className="text-sm text-gray-600 mt-1">{event.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {result.temporal_analysis.is_outdated && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            Warning: This article may contain outdated information.
          </p>
        </div>
      )}
    </div>
  )
}
