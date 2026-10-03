import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getReport } from '../api/debate'
import useDebateStore from '../store/debateStore'
import QualityBadge from '../components/shared/QualityBadge'
import ConfidenceBar from '../components/debate/ConfidenceBar'

export default function Report() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const { userBet } = useDebateStore()

  useEffect(() => {
    getReport(id).then(({ data }) => { setReport(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="flex gap-2">
        {[0,1,2].map(i => <div key={i} className="w-3 h-3 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: `${i*0.2}s` }} />)}
      </div>
    </div>
  )

  if (!report) return (
    <div className="min-h-screen bg-black flex items-center justify-center text-white/40">
      Report not found
    </div>
  )

  const betCorrect = userBet === 'pro' && report.confidence_score > 0.5
    ? true : userBet === 'con' && report.confidence_score < 0.5
    ? true : userBet === 'balanced' && Math.abs(report.confidence_score - 0.5) < 0.1
    ? true : userBet ? false : null

  return (
    <div className="min-h-screen bg-black text-white pt-20 pb-16">
      <div className="fixed inset-0 pointer-events-none bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.08),transparent)]" />
      <div className="relative z-10 max-w-4xl mx-auto px-4 space-y-8">

        {/* Header */}
        <div className="text-center space-y-4">
          <QualityBadge quality={report.debate_quality} />
          <h1 className="text-2xl font-bold text-white/80 max-w-2xl mx-auto leading-tight">
            "{report.topic}"
          </h1>
          {report.verdict && (
            <div className="px-6 py-4 bg-white/3 border border-white/10 rounded-2xl max-w-2xl mx-auto">
              <p className="text-xs uppercase tracking-widest text-white/30 mb-2">Verdict</p>
              <p className="text-lg font-semibold text-white">{report.verdict}</p>
            </div>
          )}
          <div className="max-w-md mx-auto">
            <ConfidenceBar score={report.confidence_score} />
            <p className="text-white/30 text-xs text-center mt-2">{report.confidence_reason}</p>
          </div>
          <div className="flex items-center justify-center gap-6 text-white/30 text-sm">
            <span>⟳ {report.rounds_completed} rounds</span>
            <span>◈ {report.factors_debated} factors</span>
            <span>⏱ {Math.floor(report.time_used / 60)}m used</span>
          </div>
        </div>

        {/* Bet result */}
        {betCorrect !== null && (
          <div className={`px-6 py-4 rounded-2xl border text-center ${betCorrect ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
            {betCorrect ? '🎯 Your prediction was correct!' : '❌ The AI surprised you this time.'}
            <span className="ml-2 text-white/40 text-sm">You bet: {userBet?.toUpperCase()}</span>
          </div>
        )}

        {/* Strongest arguments */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: '🔵 PRO — Strongest Arguments', args: report.pro_strongest_arguments, color: 'blue' },
            { label: '🔴 CON — Strongest Arguments', args: report.con_strongest_arguments, color: 'red' },
          ].map(({ label, args, color }) => (
            <div key={label} className={`bg-${color}-500/5 border border-${color}-500/20 rounded-2xl p-5`}>
              <p className="text-xs uppercase tracking-widest text-white/30 mb-4">{label}</p>
              <ul className="space-y-2">
                {args?.map((a, i) => (
                  <li key={i} className={`flex gap-2 text-sm text-white/70`}>
                    <span className={`text-${color}-400 mt-0.5`}>→</span>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Hall of Fame */}
        {report.arguments_that_held_up?.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-widest text-white/30 mb-4">🏆 Hall of Fame — Survived scrutiny</p>
            <div className="grid gap-3">
              {report.arguments_that_held_up.map((a, i) => (
                <div key={i} className="flex items-start gap-4 px-5 py-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                  <span className="text-emerald-400 text-lg mt-0.5">✓</span>
                  <div>
                    <p className="text-white/80 text-sm font-medium">{a.argument_summary}</p>
                    <p className="text-white/30 text-xs mt-1">{a.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Graveyard */}
        {report.arguments_that_collapsed?.length > 0 && (
          <div>
            <p className="text-xs uppercase tracking-widest text-white/30 mb-4">⚰️ Graveyard — Collapsed under pressure</p>
            <div className="grid gap-3">
              {report.arguments_that_collapsed.map((a, i) => (
                <div key={i} className="flex items-start gap-4 px-5 py-4 bg-white/2 border border-white/8 rounded-xl opacity-60">
                  <span className="text-red-400/70 text-lg mt-0.5">✕</span>
                  <div>
                    <p className="text-white/50 text-sm font-medium line-through">{a.argument_summary}</p>
                    <p className="text-white/30 text-xs mt-1 no-underline" style={{textDecoration:'none'}}>{a.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: '✓ What Worked', items: report.what_worked, color: 'emerald' },
            { label: '✕ What Failed', items: report.what_failed, color: 'red' },
            { label: '↑ How to Improve', items: report.how_to_improve, color: 'blue' },
          ].map(({ label, items, color }) => (
            <div key={label} className="bg-white/3 border border-white/10 rounded-xl p-4">
              <p className={`text-xs uppercase tracking-widest text-${color}-400/70 mb-3`}>{label}</p>
              <ul className="space-y-2">
                {items?.map((item, i) => (
                  <li key={i} className="text-white/50 text-xs leading-relaxed">{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-center pt-4">
          <button onClick={() => navigate(`/debate/${id}/trace`)}
            className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/60 text-sm transition-all">
            ⟳ Replay Debate
          </button>
          <button onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl text-white font-semibold text-sm transition-all">
            ⚡ New Debate
          </button>
        </div>
      </div>
    </div>
  )
}