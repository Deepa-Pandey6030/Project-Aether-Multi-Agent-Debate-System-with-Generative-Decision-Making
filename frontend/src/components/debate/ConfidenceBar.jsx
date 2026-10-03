import { useState, useEffect } from 'react'

export default function ConfidenceBar({ score = 0.5 }) {
  const [display, setDisplay] = useState(0.5)

  useEffect(() => {
    const t = setTimeout(() => setDisplay(score), 100)
    return () => clearTimeout(t)
  }, [score])

  const proWidth = Math.round(display * 100)
  const conWidth = 100 - proWidth

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs font-semibold tracking-widest uppercase">
        <span className="text-blue-400">PRO</span>
        <span className="text-white/30 text-xs">Confidence</span>
        <span className="text-red-400">CON</span>
      </div>
      <div className="relative h-3 rounded-full overflow-hidden bg-white/5 border border-white/10">
        <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-1000 ease-in-out rounded-full"
          style={{ width: `${proWidth}%` }} />
        <div className="absolute inset-y-0 right-0 bg-gradient-to-l from-red-600 to-red-400 transition-all duration-1000 ease-in-out rounded-full"
          style={{ width: `${conWidth}%` }} />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-0.5 h-full bg-black/50" />
        </div>
      </div>
      <div className="flex justify-between text-xs text-white/30">
        <span>{proWidth}%</span>
        <span>{conWidth}%</span>
      </div>
    </div>
  )
}