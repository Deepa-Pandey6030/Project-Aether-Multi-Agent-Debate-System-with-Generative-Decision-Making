export default function RoundBadge({ round, status }) {
  const styles = {
    active: 'bg-blue-500/20 border-blue-500/40 text-blue-300 animate-pulse',
    completed: 'bg-white/5 border-white/10 text-white/40',
    pending: 'bg-transparent border-white/5 text-white/15',
  }
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold uppercase tracking-widest transition-all ${styles[status] || styles.pending}`}>
      <div className={`w-1.5 h-1.5 rounded-full ${
        status === 'active' ? 'bg-blue-400' :
        status === 'completed' ? 'bg-white/30' : 'bg-white/10'
      }`} />
      Round {round}
    </div>
  )
}