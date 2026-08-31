import type { MediaAnalysis } from '../types'

interface MediaAnalysisProps {
  analysis: MediaAnalysis
}

export default function MediaAnalysis({ analysis }: MediaAnalysisProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Media Analysis</h3>
      
      {analysis.images.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-900 mb-3">Images ({analysis.images.length})</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {analysis.images.map((image) => (
              <div key={image.id} className="border border-gray-200 rounded-lg overflow-hidden">
                <img
                  src={image.url}
                  alt={image.caption || 'Article image'}
                  className="w-full h-32 object-cover"
                />
                <div className="p-2">
                  {image.caption && (
                    <p className="text-xs text-gray-600 truncate">{image.caption}</p>
                  )}
                  {image.is_reused && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">
                      Reused Media
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {analysis.videos.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Videos ({analysis.videos.length})</h4>
          <div className="space-y-3">
            {analysis.videos.map((video) => (
              <div key={video.id} className="border border-gray-200 rounded-lg p-3">
                <p className="text-sm text-gray-700">{video.caption || 'Video'}</p>
                {video.is_reused && (
                  <span className="inline-block mt-1 px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">
                    Reused Media
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {analysis.images.length === 0 && analysis.videos.length === 0 && (
        <p className="text-gray-500 text-sm">No media items found in this article.</p>
      )}
      
      <div className="mt-4 flex gap-4 text-sm">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
          <span>Reused: {analysis.reused_media_count}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-gray-400 rounded-full"></span>
          <span>Unverified: {analysis.unverified_media_count}</span>
        </div>
      </div>
    </div>
  )
}
