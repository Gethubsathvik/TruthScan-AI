interface ConfidenceMeterProps {
  confidence: number
}

export default function ConfidenceMeter({ confidence }: ConfidenceMeterProps) {
  const percentage = Math.round(confidence * 100)
  
  let color = 'bg-green-500'
  if (percentage < 30) color = 'bg-red-500'
  else if (percentage < 60) color = 'bg-yellow-500'
  else if (percentage < 80) color = 'bg-blue-500'

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm text-gray-600 mb-1">
        <span>Confidence</span>
        <span>{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  )
}
