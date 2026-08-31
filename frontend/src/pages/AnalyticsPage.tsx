import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

interface AnalyticsData {
  total_checks: number
  verified: number
  likely_true: number
  partially_true: number
  misleading: number
  unverified: number
  likely_false: number
  false_count: number
  category_distribution: { category: string; count: number }[]
  source_type_distribution: { source_type: string; count: number }[]
  average_confidence: number
  average_sources_per_check: number
  primary_secondary_ratio: number
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC0CB']

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setData({
        total_checks: 156,
        verified: 23,
        likely_true: 45,
        partially_true: 28,
        misleading: 31,
        unverified: 19,
        likely_false: 7,
        false_count: 3,
        category_distribution: [
          { category: 'Politics', count: 45 },
          { category: 'Health', count: 32 },
          { category: 'Science', count: 28 },
          { category: 'Technology', count: 22 },
          { category: 'Business', count: 15 },
          { category: 'Other', count: 14 },
        ],
        source_type_distribution: [
          { source_type: 'Primary', count: 89 },
          { source_type: 'Secondary', count: 124 },
          { source_type: 'Fact Check', count: 34 },
        ],
        average_confidence: 0.73,
        average_sources_per_check: 4.2,
        primary_secondary_ratio: 0.72,
      })
      setLoading(false)
    }
    
    fetchAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-600">No analytics data available</p>
    </div>
  }

  const verdictData = [
    { name: 'Verified', value: data.verified },
    { name: 'Likely True', value: data.likely_true },
    { name: 'Partially True', value: data.partially_true },
    { name: 'Misleading', value: data.misleading },
    { name: 'Unverified', value: data.unverified },
    { name: 'Likely False', value: data.likely_false },
    { name: 'False', value: data.false_count },
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Analytics Dashboard</h1>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Checks</h3>
              <p className="text-3xl font-bold text-gray-900">{data.total_checks}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Average Confidence</h3>
              <p className="text-3xl font-bold text-gray-900">{Math.round(data.average_confidence * 100)}%</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Avg Sources/Check</h3>
              <p className="text-3xl font-bold text-gray-900">{data.average_sources_per_check.toFixed(1)}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Primary/Secondary Ratio</h3>
              <p className="text-3xl font-bold text-gray-900">{data.primary_secondary_ratio.toFixed(2)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Verdict Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={verdictData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {verdictData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Category Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.category_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4F46E5" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Source Type Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.source_type_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="source_type" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
