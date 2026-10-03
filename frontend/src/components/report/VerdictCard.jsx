import ConfidenceBar from '../debate/ConfidenceBar'
import QualityBadge from '../shared/QualityBadge'

export default function VerdictCard({ topic, verdict, confidenceScore, confidenceReason, debateQuality, roundsCompleted, factorsDebated, timeUsed }) {
  const winner = confidenceScore > 0.55 ? 'PRO'
    : confidenceScore < 0.45 ? 'CON'
    : 'BALANCED'

  const winnerColor = winner === 'PRO' ? 'text-blue-400'
    : winner === 'CON' ? 'text-red-400'
    : 'text-amber-400'

  return (
    <div className="relative overflow-hidden bg-white/3 border border-white/10 rounded-2xl p-8">
      {/* Background glow */}
      <div className={`absolute top-0 left-0 right-0 h-px ${
        winner === 'PRO' ? 'bg-gradient-to-r from-transparent via-blue-500/50 to-transparent' :
        winner === 'CON' ? 'bg-gradient-to-r from-transparent via-red-500/50 to-transparent' :
        'bg-gradient-to-r from-transparent via-amber-500/50 to-transparent'
      }`} />

      <div className="space-y-6">
        {/* Topic + quality */}
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-white/70 text-lg font-medium leading-snug flex-1">
            "{topic}"
          </h2>
          <QualityBadge quality={debateQuality} />
        </div>

        {/* Winner */}
        <div className="text-center py-4 border-y border-white/5">
          <p className="text-white/25 text-xs uppercase tracking-widest mb-2">Result</p>
          <span className={`text-4xl font-black tracking-tight ${winnerColor}`}>
            {winner}
          </span>
          {winner !== 'BALANCED' && (
            <p className="text-white/30 text-sm mt-1">made the stronger case</p>
          )}
        </div>

        {/* Verdict text */}
        {verdict && (
          <div className="px-4 py-3 bg-white/3 rounded-xl border border-white/8">
            <p className="text-white/60 text-sm leading-relaxed">{verdict}</p>
          </div>
        )}

        {/* Confidence bar */}
        <ConfidenceBar score={confidenceScore} />
        {confidenceReason && (
          <p className="text-white/25 text-xs text-center -mt-2">{confidenceReason}</p>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 pt-2 border-t border-white/5">
          {[
            { label: 'Rounds', value: roundsCompleted },
            { label: 'Factors', value: factorsDebated },
            { label: 'Duration', value: `${Math.floor(timeUsed / 60)}m ${timeUsed % 60}s` },
          ].map(({ label, value }) => (
            <div key={label} className="text-center">
              <p className="text-white font-semibold text-sm">{value}</p>
              <p className="text-white/25 text-xs uppercase tracking-widest mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}