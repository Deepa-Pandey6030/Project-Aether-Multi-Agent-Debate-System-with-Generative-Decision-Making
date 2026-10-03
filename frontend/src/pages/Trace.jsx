import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTrace } from '../api/debate'

const AGENT_CONFIG = {
  pro: { label: 'PRO', color: 'text-blue-400', dot: 'bg-blue-500', line: 'bg-blue-500/20' },
  con: { label: 'CON', color: 'text-red-400', dot: 'bg-red-500', line: 'bg-red-500/20' },
  round_evaluator: { label: 'Evaluator', color: 'text-amber-400', dot: 'bg-amber-500', line: 'bg-amber-500/20' },
  cross_examiner: { label: 'Cross Examiner', color: 'text-violet-400', dot: 'bg-violet-500', line: 'bg-violet-500/20' },
  synthesizer: { label: 'Synthesizer', color: 'text-emerald-400', dot: 'bg-emerald-500', line: 'bg-emerald-500/20' },
  factor_extraction: { label: 'Factor Agent', color: 'text-cyan-400', dot: 'bg-cyan-500', line: 'bg-cyan-500/20' },
  moderator: { label: 'Moderator', color: 'text-white/40', dot: 'bg-white/20', line: 'bg-white/5' },
}

const PHASE_LABELS = {
  debate_started: 'Debate Started',
  factor_extraction_result: 'Factor Extraction',
  pro_opening: 'Pro Opening',
  con_opening: 'Con Opening',
  pro_rebuttal: 'Pro Rebuttal',
  con_rebuttal: 'Con Rebuttal',
  round_evaluation: 'Round Evaluation',
  cross_exam_questions_pro: 'Cross-Exam Questions → Pro',
  cross_exam_answers_pro: 'Pro Answers Cross-Exam',
  cross_exam_questions_con: 'Cross-Exam Questions → Con',
  cross_exam_answers_con: 'Con Answers Cross-Exam',
  pro_closing: 'Pro Closing',
  con_closing: 'Con Closing',
  synthesis_report: 'Final Synthesis',
  error: 'Error',
}

function extractPreview(event) {
  const c = event.content || {}
  const et = event.event_type || ''
  if (et === 'pro_opening' || et === 'con_opening') return c.overall_position?.slice(0, 200)
  if (et.includes('rebuttal')) return c.content?.slice(0, 200)
  if (et.includes('closing')) return c.final_position?.slice(0, 200)
  if (et === 'round_evaluation') return c.reason
  if (et === 'factor_extraction_result') return c.factors?.map(f => f.name).join(' · ')
  if (et.includes('cross_exam_questions')) return `${c.questions?.length || 0} questions generated`
  if (et.includes('cross_exam_answers')) return `${c.answers?.length || 0} answers provided`
  if (et === 'synthesis_report') return `Quality: ${c.debate_quality} · Confidence: ${c.confidence_score}`
  if (et === 'debate_started') return `Topic: "${c.topic}"`
  return null
}

function isRoundStart(event, prevEvent) {
  if (!prevEvent) return false
  const cur = event.meta?.round
  const prev = prevEvent.meta?.round
  return cur && cur !== prev
}

export default function Trace() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [trace, setTrace] = useState([])
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(new Set())

  useEffect(() => {
    getTrace(id).then(({ data }) => {
      setTrace(data.trace || [])
      setTopic(data.topic || '')
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  const toggle = (i) => {
    const next = new Set(expanded)
    next.has(i) ? next.delete(i) : next.add(i)
    setExpanded(next)
  }

  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="flex gap-2">
        {[0,1,2].map(i => <div key={i} className="w-3 h-3 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: `${i * 0.2}s` }} />)}
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-black text-white pt-20 pb-20">
      <div className="max-w-3xl mx-auto px-4">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <button onClick={() => navigate(`/debate/${id}/report`)}
              className="text-white/30 hover:text-white/60 text-sm transition-colors">
              ← Report
            </button>
            <span className="text-white/10">/</span>
            <span className="text-white/30 text-sm">Replay</span>
          </div>
          <h1 className="text-xl font-bold text-white/80 leading-snug">"{topic}"</h1>
          <p className="text-white/25 text-sm mt-1">{trace.length} events</p>
        </div>

        {/* Agent legend */}
        <div className="flex flex-wrap gap-3 mb-8">
          {Object.entries(AGENT_CONFIG).filter(([k]) => k !== 'moderator').map(([key, cfg]) => (
            <div key={key} className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
              <span className={`text-xs ${cfg.color}`}>{cfg.label}</span>
            </div>
          ))}
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-white/5" />

          <div className="space-y-1">
            {trace.map((event, i) => {
              const agent = event.agent || 'moderator'
              const cfg = AGENT_CONFIG[agent] || AGENT_CONFIG.moderator
              const preview = extractPreview(event)
              const isExpanded = expanded.has(i)
              const showRoundDivider = isRoundStart(event, trace[i - 1])
              const ts = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''

              return (
                <div key={i}>
                  {/* Round divider */}
                  {showRoundDivider && (
                    <div className="flex items-center gap-3 py-3 pl-12">
                      <div className="h-px flex-1 bg-white/5" />
                      <span className="text-white/20 text-xs uppercase tracking-widest px-3 py-1 border border-white/8 rounded-full">
                        Round {event.meta?.round}
                      </span>
                      <div className="h-px flex-1 bg-white/5" />
                    </div>
                  )}

                  <div
                    className={`relative pl-12 pr-4 py-3 rounded-xl cursor-pointer transition-all ${
                      isExpanded ? 'bg-white/3' : 'hover:bg-white/2'
                    }`}
                    onClick={() => toggle(i)}
                  >
                    {/* Dot on timeline */}
                    <div className={`absolute left-3 top-4 w-2.5 h-2.5 rounded-full border-2 border-black ${cfg.dot}`} />

                    {/* Event header */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs font-bold uppercase tracking-widest ${cfg.color}`}>
                            {cfg.label}
                          </span>
                          <span className="text-white/15 text-xs">·</span>
                          <span className="text-white/30 text-xs">
                            {PHASE_LABELS[event.event_type] || event.event_type}
                          </span>
                        </div>
                        {preview && !isExpanded && (
                          <p className="text-white/40 text-xs leading-relaxed truncate">{preview}</p>
                        )}
                        {isExpanded && preview && (
                          <p className="text-white/60 text-sm leading-relaxed mt-1">{preview}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-white/15 text-xs">{ts}</span>
                        <span className={`text-white/20 text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                          ↓
                        </span>
                      </div>
                    </div>

                    {/* Expanded content */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <pre className="text-white/30 text-xs leading-relaxed whitespace-pre-wrap overflow-auto max-h-64 font-mono">
                          {JSON.stringify(event.content, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Bottom actions */}
        <div className="flex gap-4 justify-center mt-12">
          <button onClick={() => navigate(`/debate/${id}/report`)}
            className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white/60 text-sm transition-all">
            ← Back to Report
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