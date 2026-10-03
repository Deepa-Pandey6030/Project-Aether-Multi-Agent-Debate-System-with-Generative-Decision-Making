export default function QualityBadge({ quality }) {
  const styles = {
    High: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    Medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    Low: 'bg-red-500/20 text-red-400 border-red-500/30',
  }
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border uppercase tracking-widest ${styles[quality] || styles.Medium}`}>
      {quality}
    </span>
  )
}