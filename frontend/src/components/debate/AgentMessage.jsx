import { useState, useEffect } from 'react'

const AGENT_CONFIG = {
  pro: { label: 'PRO Agent', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', dot: 'bg-blue-500', align: 'items-start' },
  con: { label: 'CON Agent', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20', dot: 'bg-red-500', align: 'items-end' },
  round_evaluator: { label: 'Evaluator', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20', dot: 'bg-amber-500', align: 'items-center' },
  cross_examiner: { label: 'Cross Examiner', color: 'text-violet-400', bg: 'bg-violet-500/10 border-violet-500/20', dot: 'bg-violet-500', align: 'items-start' },
  synthesizer: { label: 'Synthesizer', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20', dot: 'bg-emerald-500', align: 'items-center' },
  factor_extraction: { label: 'Factor Agent', color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20', dot: 'bg-cyan-500', align: 'items-start' },
  moderator: { label: 'Moderator', color: 'text-white/50', bg: 'bg-white/5 border-white/10', dot: 'bg-white/30', align: 'items-center' },
}

function extractText(event) {
  const c = event.content || {}
  const et = event.event_type || ''
  if (et === 'pro_opening' || et === 'con_opening') return c.overall_position?.slice(0, 300) + '...'
  if (et.includes('rebuttal')) return c.content?.slice(0, 250) + '...'
  if (et.includes('closing')) return c.final_position?.slice(0, 250) + '...'
  if (et === 'round_evaluation') return c.reason || 'Round evaluated.'
  if (et === 'factor_extraction_result') return `Extracted ${c.factors?.length || 0} factors: ${c.factors?.map(f => f.name).join(', ')}`
  if (et.includes('cross_exam_questions')) return `Generated ${c.questions?.length || 0} questions`
  if (et.includes('cross_exam_answers')) return `Answered ${c.answers?.length || 0} questions`
  if (et === 'synthesis_report') return `Debate Quality: ${c.debate_quality} | Confidence: ${c.confidence_score}`
  if (et === 'debate_started') return `Starting debate: "${c.topic}"`
  return JSON.stringify(c).slice(0, 200)
}

function TypewriterText({ text, speed = 18 }) {
  const [displayed, setDisplayed] = useState('')

  useEffect(() => {
    setDisplayed('')
    let i = 0
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1))
        i++
      } else {
        clearInterval(interval)
      }
    }, speed)
    return () => clearInterval(interval)
  }, [text])

  return <span>{displayed}<span className="animate-pulse">|</span></span>
}

export default function AgentMessage({ event, isNew = false }) {
  const agent = event.agent || 'moderator'
  const config = AGENT_CONFIG[agent] || AGENT_CONFIG.moderator
  const text = extractText(event)
  const isCentered = agent === 'round_evaluator' || agent === 'synthesizer' || agent === 'moderator'

  return (
    <div className={`flex flex-col ${config.align} animate-fade-in`}>
      <div className={`max-w-xl w-full ${isCentered ? 'mx-auto' : ''}`}>
        <div className={`flex items-center gap-2 mb-1 ${isCentered ? 'justify-center' : ''}`}>
          <div className={`w-2 h-2 rounded-full ${config.dot}`} />
          <span className={`text-xs font-bold tracking-widest uppercase ${config.color}`}>
            {config.label}
          </span>
          {event.meta?.round && (
            <span className="text-xs text-white/20">Round {event.meta.round}</span>
          )}
        </div>
        <div className={`px-4 py-3 rounded-xl border text-sm leading-relaxed text-white/80 ${config.bg}`}>
          {isNew ? <TypewriterText text={text} /> : text}
        </div>
      </div>
    </div>
  )
}