import { useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useDebateStore from '../store/debateStore'
import usePolling from '../hooks/usePolling'
import PhaseProgress from '../components/debate/PhaseProgress'
import ConfidenceBar from '../components/debate/ConfidenceBar'
import AgentMessage from '../components/debate/AgentMessage'

export default function Theater() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { topic, status, phase, messages, roundNumber, timeElapsed, timeBudget } = useDebateStore()
  const bottomRef = useRef(null)
  const isActive = status !== 'completed'

  usePolling(id, isActive)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  useEffect(() => {
    if (status === 'completed') {
      setTimeout(() => navigate(`/debate/${id}/report`), 2000)
    }
  }, [status])

  const progress = timeBudget > 0 ? Math.min((timeElapsed / timeBudget) * 100, 100) : 0

  return (
    <div className="min-h-screen bg-black text-white pt-16">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.08),transparent)]" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-8">

        {/* Left sidebar */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {isActive && <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />}
              <span className="text-white/40 text-xs uppercase tracking-widest">
                {isActive ? 'Live Debate' : 'Completed'}
              </span>
            </div>
            <h2 className="text-white font-bold text-lg leading-tight">{topic}</h2>
          </div>

          {/* Time progress */}
          <div>
            <div className="flex justify-between text-xs text-white/30 mb-2">
              <span>Time Elapsed</span>
              <span>{Math.floor(timeElapsed / 60)}m {timeElapsed % 60}s</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full transition-all duration-1000"
                style={{ width: `${progress}%` }} />
            </div>
          </div>

          <ConfidenceBar score={0.5} />

          <div className="border-t border-white/5 pt-6">
            <p className="text-white/30 text-xs uppercase tracking-widest mb-4">Progress</p>
            <PhaseProgress phase={phase} roundNumber={roundNumber} />
          </div>

          {status === 'completed' && (
            <div className="px-4 py-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm text-center animate-pulse">
              ✓ Debate complete — loading report...
            </div>
          )}
        </div>

        {/* Main theater */}
        <div className="flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-white/40 text-xs uppercase tracking-widest">Live Debate Feed</h3>
            <span className="text-white/20 text-xs">{messages.length} events</span>
          </div>

          <div className="space-y-4 flex-1">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="flex gap-2 mb-4">
                  {[0, 1, 2].map((i) => (
                    <div key={i} className="w-3 h-3 rounded-full bg-blue-500/50 animate-bounce"
                      style={{ animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
                <p className="text-white/20 text-sm">Agents initializing...</p>
              </div>
            ) : (
              messages.map((msg, i) => (
                <AgentMessage key={i} event={msg} isNew={i === messages.length - 1} />
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </div>
      </div>
    </div>
  )
}