import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { startDebate } from '../api/debate'
import useDebateStore from '../store/debateStore'
import useAuthStore from '../store/authStore'

const SUGGESTIONS = [
  { topic: 'Is AI taking our jobs?', heat: 92 },
  { topic: 'Should voting be mandatory?', heat: 87 },
  { topic: 'Is social media net positive for society?', heat: 81 },
  { topic: 'Should remote work be the default?', heat: 76 },
  { topic: 'Is nuclear energy the future?', heat: 71 },
]

const TIME_OPTIONS = [
  { value: 300, label: 'Quick', sub: '~5 min' },
  { value: 600, label: 'Standard', sub: '~10 min' },
  { value: 900, label: 'Deep', sub: '~15 min' },
  { value: 1200, label: 'Full', sub: '~20 min' },
]

export default function Landing() {
  const [topic, setTopic] = useState('')
  const [timeBudget, setTimeBudget] = useState(600)
  const [bet, setBet] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setDebate, setUserBet } = useDebateStore()
  const { isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const handleStart = async () => {
    if (!topic.trim()) return
    if (!isAuthenticated) { navigate('/login'); return }
    setError('')
    setLoading(true)
    try {
      const { data } = await startDebate(topic.trim(), timeBudget)
      setDebate(data.debate_id, topic.trim(), timeBudget)
      if (bet) setUserBet(bet)
      navigate(`/debate/${data.debate_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start debate')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.15),transparent)]" />
        <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-600/5 rounded-full blur-3xl" />
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '48px 48px'
        }} />
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 pt-20">
        {/* Hero */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs uppercase tracking-widest font-semibold mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            Multi-Agent Decision Intelligence
          </div>
          <h1 className="text-6xl md:text-7xl font-black tracking-tight leading-none mb-6">
            <span className="text-white">What's the</span>
            <br />
            <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-blue-400 bg-clip-text text-transparent">
              truth?
            </span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-xl mx-auto">
            AETHER deploys 7 AI agents to debate both sides of any question.
            Watch the arguments unfold in real time.
          </p>
        </div>

        {/* Input card */}
        <div className="w-full max-w-2xl">
          <div className="bg-white/3 border border-white/10 rounded-2xl p-6 backdrop-blur-sm space-y-6">
            {/* Topic input */}
            <div>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleStart() } }}
                placeholder="Enter any topic, question, or debate..."
                rows={2}
                className="w-full bg-transparent text-white text-lg placeholder-white/20 focus:outline-none resize-none"
              />
            </div>

            {/* Time budget */}
            <div>
              <p className="text-white/30 text-xs uppercase tracking-widest mb-3">Debate Depth</p>
              <div className="grid grid-cols-4 gap-2">
                {TIME_OPTIONS.map((opt) => (
                  <button key={opt.value} onClick={() => setTimeBudget(opt.value)}
                    className={`py-3 rounded-xl border text-center transition-all ${
                      timeBudget === opt.value
                        ? 'bg-blue-500/20 border-blue-500/50 text-blue-300'
                        : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'
                    }`}>
                    <div className="text-sm font-semibold">{opt.label}</div>
                    <div className="text-xs opacity-60">{opt.sub}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Bet */}
            {topic.trim().length > 10 && (
              <div className="border-t border-white/5 pt-5">
                <p className="text-white/30 text-xs uppercase tracking-widest mb-3">Who do you think wins?</p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { key: 'pro', label: '🔵 PRO', color: 'blue' },
                    { key: 'con', label: '🔴 CON', color: 'red' },
                    { key: 'balanced', label: '⚖️ Balanced', color: 'amber' },
                  ].map(({ key, label, color }) => (
                    <button key={key} onClick={() => setBet(key)}
                      className={`py-2.5 rounded-xl border text-sm font-medium transition-all ${
                        bet === key
                          ? `bg-${color}-500/20 border-${color}-500/50 text-${color}-300`
                          : 'bg-white/3 border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button onClick={handleStart} disabled={loading || !topic.trim()}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 disabled:opacity-30 text-white font-bold rounded-xl transition-all text-sm uppercase tracking-widest">
              {loading ? 'Launching Debate...' : '⚡ Launch Debate'}
            </button>
          </div>

          {/* Suggestions */}
          <div className="mt-8">
            <p className="text-white/20 text-xs uppercase tracking-widest text-center mb-4">Hot Topics</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s) => (
                <button key={s.topic} onClick={() => setTopic(s.topic)}
                  className="px-4 py-2 bg-white/3 hover:bg-white/8 border border-white/10 hover:border-white/20 rounded-full text-white/50 hover:text-white/80 text-sm transition-all">
                  {s.topic}
                  <span className="ml-2 text-orange-400/60 text-xs">{s.heat}%</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}