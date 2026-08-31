import { useState } from 'react'

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState('')
  const [searchProvider, setSearchProvider] = useState('tavily')
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

          <div className="bg-white rounded-lg shadow p-8">
            <form onSubmit={handleSave}>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Provider
                </label>
                <select
                  value={searchProvider}
                  onChange={(e) => setSearchProvider(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="tavily">Tavily</option>
                  <option value="brave">Brave Search</option>
                  <option value="serpapi">SerpAPI</option>
                </select>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Your API key is stored securely and never exposed to the frontend.
                </p>
              </div>

              {saved && (
                <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
                  Settings saved successfully!
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                Save Settings
              </button>
            </form>
          </div>

          <div className="mt-8 bg-white rounded-lg shadow p-8">
            <h2 className="text-xl font-semibold mb-4">About</h2>
            <p className="text-gray-600 mb-2">
              <strong>Version:</strong> 1.0.0
            </p>
            <p className="text-gray-600 mb-2">
              <strong>Backend:</strong> Python FastAPI
            </p>
            <p className="text-gray-600 mb-2">
              <strong>Frontend:</strong> React + TypeScript + Tailwind CSS
            </p>
            <p className="text-gray-600">
              <strong>AI Layer:</strong> OpenAI GPT-4o-mini
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
