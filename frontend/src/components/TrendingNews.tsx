import { useState, useEffect } from 'react'
import { getTrendingNews, getDailyUpdates } from '../services/api'

interface NewsItem {
  id: string
  title: string
  url: string
  snippet: string
  source_name: string
  source_url: string
  source_country: string
  language: string
  credibility: string
  published_date: string
}

export default function TrendingNews() {
  const [trending, setTrending] = useState<NewsItem[]>([])
  const [dailyUpdates, setDailyUpdates] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'trending' | 'daily'>('trending')

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const [trendingData, updatesData] = await Promise.all([
          getTrendingNews(15),
          getDailyUpdates(15)
        ])
        setTrending(trendingData.trending || [])
        setDailyUpdates(updatesData.updates || [])
      } catch (error) {
        console.error('Failed to fetch news:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchNews()
  }, [])

  const currentNews = activeTab === 'trending' ? trending : dailyUpdates

  const getCredibilityColor = (credibility: string) => {
    switch (credibility) {
      case 'high': return 'bg-green-100 text-green-800'
      case 'medium-high': return 'bg-blue-100 text-blue-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getLanguageFlag = (language: string) => {
    switch (language) {
      case 'en': return '🇬🇧'
      case 'hi': return '🇮🇳'
      case 'te': return '🇮🇳'
      default: return '🌐'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('trending')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'trending'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            🔥 Trending News
          </button>
          <button
            onClick={() => setActiveTab('daily')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'daily'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            📰 Daily Updates
          </button>
        </div>
      </div>

      <div className="p-6">
        {currentNews.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No news available at the moment.</p>
            <p className="text-sm text-gray-400 mt-1">
              Configure a search API key to fetch real-time news.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {currentNews.map((item, index) => (
              <div
                key={`${item.url}-${index}`}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{getLanguageFlag(item.language)}</span>
                      <span className="text-sm font-medium text-gray-700">
                        {item.source_name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {item.source_country}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCredibilityColor(item.credibility)}`}>
                        {item.credibility}
                      </span>
                    </div>
                    
                    <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                      {item.title}
                    </h3>
                    
                    <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                      {item.snippet}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        Read full article →
                      </a>
                      <span className="text-xs text-gray-400">
                        {new Date(item.published_date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
