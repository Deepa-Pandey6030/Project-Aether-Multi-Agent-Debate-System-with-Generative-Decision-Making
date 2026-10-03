import { useState } from 'react'

export default function TopicInput({ value, onChange, onSubmit, disabled }) {
  const [focused, setFocused] = useState(false)

  return (
    <div className={`relative rounded-2xl border transition-all duration-300 ${
      focused ? 'border-blue-500/50 bg-white/5' : 'border-white/10 bg-white/3'
    }`}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onSubmit?.()
          }
        }}
        disabled={disabled}
        placeholder="Enter any topic, question, or decision to debate..."
        rows={3}
        className="w-full bg-transparent text-white text-base placeholder-white/20 focus:outline-none resize-none px-5 pt-4 pb-3 leading-relaxed"
      />
      <div className="flex items-center justify-between px-5 pb-4">
        <span className={`text-xs transition-colors ${
          value.length > 800 ? 'text-red-400' :
          value.length > 500 ? 'text-amber-400' : 'text-white/20'
        }`}>
          {value.length} / 1000
        </span>
        {value.length > 10 && (
          <span className="text-white/20 text-xs">Press Enter to launch</span>
        )}
      </div>

      {/* Glow effect when focused */}
      {focused && (
        <div className="absolute inset-0 rounded-2xl pointer-events-none"
          style={{ boxShadow: '0 0 0 1px rgba(59,130,246,0.3), 0 0 30px rgba(59,130,246,0.05)' }} />
      )}
    </div>
  )
}