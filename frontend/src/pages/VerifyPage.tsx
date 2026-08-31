import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { verifyClaim } from '../services/api'
import type { InputType } from '../types'

export default function VerifyPage() {
  const [inputType, setInputType] = useState<InputType>('claim')
  const [inputText, setInputText] = useState('')
  const [inputUrl, setInputUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!inputText.trim() && !inputUrl.trim()) {
      setError('Please provide input text or URL')
      return
    }
    
    setLoading(true)
    try {
      const result = await verifyClaim(
        inputType,
        inputType === 'url' ? inputUrl : inputText,
        inputType === 'url' ? inputUrl : undefined
      )
      navigate(`/result/${result.verification_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Verification failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Verify News</h1>
          
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="flex flex-wrap gap-2 mb-6">
              {[
                { value: 'claim', label: 'Enter Claim' },
                { value: 'url', label: 'News URL' },
                { value: 'headline', label: 'Headline' },
                { value: 'article', label: 'Article Text' },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setInputType(option.value as InputType)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    inputType === option.value
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit}>
              {inputType === 'url' ? (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    News URL
                  </label>
                  <input
                    type="url"
                    value={inputUrl}
                    onChange={(e) => setInputUrl(e.target.value)}
                    placeholder="https://example.com/news/article"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  />
                </div>
              ) : (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {inputType === 'claim' && 'Enter Claim'}
                    {inputType === 'headline' && 'Enter Headline'}
                    {inputType === 'article' && 'Paste Article Text'}
                  </label>
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={
                      inputType === 'claim'
                        ? 'e.g., NASA discovered life on Mars in 2026.'
                        : inputType === 'headline'
                        ? 'e.g., Government announces free smartphones for every citizen'
                        : 'Paste the full article text here...'
                    }
                    rows={inputType === 'article' ? 10 : 4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    required
                  />
                </div>
              )}

              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold text-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Verifying...' : 'VERIFY NOW'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
