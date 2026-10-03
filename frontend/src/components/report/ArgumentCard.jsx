export default function ArgumentCard({ argument, side, index }) {
  const isProSide = side === 'pro'

  return (
    <div className={`flex gap-3 px-4 py-3 rounded-xl border transition-all hover:border-opacity-40 ${
      isProSide
        ? 'bg-blue-500/5 border-blue-500/15 hover:border-blue-500/30'
        : 'bg-red-500/5 border-red-500/15 hover:border-red-500/30'
    }`}>
      <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${
        isProSide ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/20 text-red-400'
      }`}>
        {index + 1}
      </div>
      <p className="text-white/70 text-sm leading-relaxed">{argument}</p>
    </div>
  )
}