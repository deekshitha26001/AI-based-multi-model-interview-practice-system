function ScoreCard({ label, score, maxScore = 100 }) {
  const percentage = Math.min((score / maxScore) * 100, 100)

  return (
    <div className="app-card">
      <p className="text-sm text-brown-dark font-medium mb-1">{label}</p>
      <p className="text-3xl font-bold text-brown mb-3">{score}</p>

      <div className="w-full h-2 bg-offwhite rounded-full overflow-hidden">
        <div
          className="h-full bg-brown rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export default ScoreCard
