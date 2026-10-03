export default function BetResult({ userBet, confidenceScore }) {
  if (!userBet) return null

  const actualWinner = confidenceScore > 0.55 ? 'pro'
    : confidenceScore < 0.45 ? 'con'
    : 'balanced'

  const correct = userBet === actualWinner

  const betLabels = { pro: '🔵 PRO', con: '🔴 CON', balanced: '⚖️ Balanced' }
  const actualLabels = { pro: '🔵 PRO', con: '🔴 CON', balanced: '⚖️ Balanced' }

  return (
    <div className={`relative overflow-hidden px-6 py-5 rounded-2xl border transition-all ${
      correct
        ? 'bg-emerald-500/8 border-emerald-500/25'
        : 'bg-red-500/8 border-red-500/25'
    }`}>
      {/* Top accent line */}
      <div className={`absolute top-0 left-0 right-0 h-px ${
        correct
          ? 'bg-gradient-to-r from-transparent via-emerald-500/60 to-transparent'
          : 'bg-gradient-to-r from-transparent via-red-500/60 to-transparent'
      }`} />

      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-white/30 text-xs uppercase tracking-widest">Your Prediction</p>
          <p className="text-white font-semibold">{betLabels[userBet]}</p>
        </div>

        <div className="text-center">
          <div className={`text-3xl mb-1 ${correct ? '' : 'grayscale'}`}>
            {correct ? '🎯' : '❌'}
          </div>
          <p className={`text-xs font-bold uppercase tracking-widest ${
            correct ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {correct ? 'Correct!' : 'Wrong'}
          </p>
        </div>

        <div className="space-y-1 text-right">
          <p className="text-white/30 text-xs uppercase tracking-widest">Actual Result</p>
          <p className="text-white font-semibold">{actualLabels[actualWinner]}</p>
        </div>
      </div>

      {correct && (
        <p className="text-emerald-400/50 text-xs text-center mt-3">
          You called it before the debate even started
        </p>
      )}
      {!correct && (
        <p className="text-red-400/40 text-xs text-center mt-3">
          The AI agents had a different take
        </p>
      )}
    </div>
  )
}