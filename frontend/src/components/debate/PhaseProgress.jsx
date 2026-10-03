const PHASES = [
  { key: 'factor_extraction', label: 'Factor Extraction', icon: '◈' },
  { key: 'opening_statements', label: 'Opening Statements', icon: '◉' },
  { key: 'rebuttal_rounds', label: 'Rebuttal Rounds', icon: '⟳' },
  { key: 'cross_examination', label: 'Cross Examination', icon: '✕' },
  { key: 'closing_statements', label: 'Closing Statements', icon: '◎' },
  { key: 'synthesis', label: 'Synthesis', icon: '◆' },
]

const ORDER = PHASES.map((p) => p.key)

export default function PhaseProgress({ phase, roundNumber }) {
  const currentIndex = ORDER.indexOf(phase)

  return (
    <div className="flex flex-col gap-2">
      {PHASES.map((p, i) => {
        const done = i < currentIndex
        const active = i === currentIndex
        return (
          <div key={p.key} className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-500 ${
            active ? 'bg-blue-500/20 border border-blue-500/40' :
            done ? 'opacity-50' : 'opacity-20'
          }`}>
            <span className={`text-lg ${active ? 'text-blue-400 animate-pulse' : done ? 'text-emerald-400' : 'text-white/30'}`}>
              {done ? '✓' : p.icon}
            </span>
            <span className={`text-sm font-medium ${active ? 'text-blue-300' : done ? 'text-white/60' : 'text-white/30'}`}>
              {p.label}
              {active && p.key === 'rebuttal_rounds' && roundNumber > 0 && (
                <span className="ml-2 text-blue-400">Round {roundNumber}</span>
              )}
            </span>
            {active && (
              <div className="ml-auto flex gap-1">
                {[0, 1, 2].map((d) => (
                  <div key={d} className="w-1 h-1 rounded-full bg-blue-400 animate-bounce"
                    style={{ animationDelay: `${d * 0.15}s` }} />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}