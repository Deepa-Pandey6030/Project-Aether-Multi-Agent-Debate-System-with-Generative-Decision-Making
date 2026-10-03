const OPTIONS = [
  { value: 300,  label: 'Quick',    sub: '~5 min',  desc: '1 factor',   icon: '⚡' },
  { value: 600,  label: 'Standard', sub: '~10 min', desc: '2 factors',  icon: '◎' },
  { value: 900,  label: 'Deep',     sub: '~15 min', desc: '3 factors',  icon: '◈' },
  { value: 1200, label: 'Full',     sub: '~20 min', desc: '4 factors',  icon: '◆' },
]

export default function TimeBudgetSlider({ value, onChange }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-white/30 text-xs uppercase tracking-widest">Debate Depth</p>
        <p className="text-white/20 text-xs">{OPTIONS.find(o => o.value === value)?.desc}</p>
      </div>

      <div className="grid grid-cols-4 gap-2">
        {OPTIONS.map((opt) => {
          const active = value === opt.value
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className={`relative flex flex-col items-center py-3 px-2 rounded-xl border transition-all duration-200 ${
                active
                  ? 'bg-blue-500/15 border-blue-500/40 text-white'
                  : 'bg-white/3 border-white/8 text-white/40 hover:border-white/15 hover:text-white/60'
              }`}
            >
              <span className={`text-base mb-1 ${active ? 'text-blue-400' : 'text-white/20'}`}>
                {opt.icon}
              </span>
              <span className="text-xs font-semibold">{opt.label}</span>
              <span className={`text-xs mt-0.5 ${active ? 'text-blue-300/60' : 'text-white/20'}`}>
                {opt.sub}
              </span>

              {active && (
                <div className="absolute -bottom-px left-1/2 -translate-x-1/2 w-8 h-0.5 bg-blue-400 rounded-full" />
              )}
            </button>
          )
        })}
      </div>

      {/* Visual depth indicator */}
      <div className="flex gap-1 mt-1">
        {OPTIONS.map((opt) => (
          <div
            key={opt.value}
            className={`h-0.5 flex-1 rounded-full transition-all duration-300 ${
              opt.value <= value ? 'bg-blue-500/60' : 'bg-white/5'
            }`}
          />
        ))}
      </div>
    </div>
  )
}