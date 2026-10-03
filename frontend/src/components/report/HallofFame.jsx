export default function HallOfFame({ arguments: args }) {
  if (!args?.length) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-lg">🏆</span>
        <p className="text-xs uppercase tracking-widest text-emerald-400/70 font-semibold">
          Hall of Fame — Survived Cross-Examination
        </p>
      </div>

      <div className="space-y-2">
        {args.map((a, i) => (
          <div
            key={i}
            className="flex items-start gap-4 px-5 py-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl hover:border-emerald-500/35 transition-all"
          >
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center mt-0.5">
              <span className="text-emerald-400 text-xs font-bold">✓</span>
            </div>
            <div className="space-y-1 flex-1">
              <p className="text-white/80 text-sm font-medium leading-snug">
                {a.argument_summary}
              </p>
              {a.reason && (
                <p className="text-emerald-400/50 text-xs leading-relaxed">
                  {a.reason}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}