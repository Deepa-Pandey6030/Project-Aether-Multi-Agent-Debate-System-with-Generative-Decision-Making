import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listDebates } from '../api/debate'
import QualityBadge from '../components/shared/QualityBadge'

export default function History() {
  const [debates, setDebates] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    listDebates().then(({ data }) => { setDebates(data.debates); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-black text-white pt-20 pb-16">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-8">Debate History</h1>
        {loading ? (
          <div className="flex gap-2">
            {[0,1,2].map(i => <div key={i} className="w-3 h-3 rounded-full bg-blue-500 animate-bounce" style={{animationDelay:`${i*0.2}s`}} />)}
          </div>
        ) : debates.length === 0 ? (
          <div className="text-center py-24 text-white/30">
            <p className="text-lg mb-4">No debates yet</p>
            <button onClick={() => navigate('/')} className="px-6 py-3 bg-blue-600 rounded-xl text-white text-sm">
              Start your first debate
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {debates.map((d) => (
              <div key={d.debate_id} onClick={() => navigate(`/debate/${d.debate_id}/report`)}
                className="flex items-center justify-between px-6 py-4 bg-white/3 hover:bg-white/6 border border-white/10 hover:border-white/20 rounded-xl cursor-pointer transition-all">
                <div className="flex-1 min-w-0 mr-4">
                  <p className="text-white/80 text-sm font-medium truncate">{d.topic}</p>
                  <p className="text-white/30 text-xs mt-1">
                    {d.current_round_number} rounds ·{' '}
                    {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {d.report?.debate_quality && <QualityBadge quality={d.report.debate_quality} />}
                  {d.report?.confidence_score != null && (
                    <span className={`text-sm font-semibold ${d.report.confidence_score > 0.5 ? 'text-blue-400' : d.report.confidence_score < 0.5 ? 'text-red-400' : 'text-amber-400'}`}>
                      {Math.round(d.report.confidence_score * 100)}%
                    </span>
                  )}
                  <span className="text-white/20">→</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}