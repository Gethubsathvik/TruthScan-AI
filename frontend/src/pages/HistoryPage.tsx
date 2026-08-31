import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getHistory, deleteHistoryItem } from '../services/api'
import type { VerificationRequest } from '../types'

export default function HistoryPage() {
  const [history, setHistory] = useState<VerificationRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getHistory()
        setHistory(data)
      } catch (err: any) {
        setError('Failed to load history')
      } finally {
        setLoading(false)
      }
    }
    
    fetchHistory()
  }, [])

  const handleDelete = async (id: string) => {
    try {
      await deleteHistoryItem(id)
      setHistory(history.filter(item => item.id !== id))
    } catch (err) {
      alert('Failed to delete item')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Verification History</h1>
            <Link to="/" className="text-indigo-600 hover:underline">
              New Verification
            </Link>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {history.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500 mb-4">No verification history yet</p>
              <Link to="/" className="text-indigo-600 hover:underline">
                Start your first verification
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="text-gray-900 font-medium mb-1 line-clamp-2">
                        {item.original_text}
                      </p>
                      <div className="flex gap-2 text-sm text-gray-500">
                        <span className="px-2 py-1 bg-gray-100 rounded">
                          {item.input_type}
                        </span>
                        <span>{new Date(item.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Link
                        to={`/result/${item.id}`}
                        className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
