export default function Graveyard({ arguments: args }) {
  if (!args?.length) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-lg">⚰️</span>
        <p className="text-xs uppercase tracking-widest text-red-400/60 font-semibold">
          Graveyard — Collapsed Under Pressure
        </p>
      </div>

      <div className="space-y-2">
        {args.map((a, i) => (
          <div
            key={i}
            className="flex items-start gap-4 px-5 py-4 bg-white/2 border border-white/6 rounded-xl opacity-55 hover:opacity-70 transition-all"
          >
            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500/15 flex items-center justify-center mt-0.5">
              <span className="text-red-400/70 text-xs font-bold">✕</span>
            </div>
            <div className="space-y-1 flex-1">
              <p className="text-white/50 text-sm font-medium leading-snug line-through decoration-red-500/30">
                {a.argument_summary}
              </p>
              {a.reason && (
                <p className="text-white/25 text-xs leading-relaxed" style={{ textDecoration: 'none' }}>
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