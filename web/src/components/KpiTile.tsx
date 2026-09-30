import { Info, type LucideIcon } from 'lucide-react'
import { useState } from 'react'

interface Props {
  label: string
  value: string
  sub?: string
  subTone?: 'good' | 'bad' | 'muted'
  icon: LucideIcon
  tooltip?: string
  // Flags the whole card as an alert (red border/top bar/tint), not just the
  // sub-line -- for a signal worth noticing even at a glance, distinct from
  // subTone which only colors the small metric-direction text.
  highlight?: boolean
  // Top bar / icon color -- 'gold' for a headline card among a set (e.g. a
  // methodology callout), otherwise the usual blue. Ignored if highlight is set.
  accent?: 'blue' | 'gold'
}

export function KpiTile({ label, value, sub, subTone = 'muted', icon: Icon, tooltip, highlight = false, accent = 'blue' }: Props) {
  const [showTooltip, setShowTooltip] = useState(false)
  const tone = { good: 'text-[var(--good)]', bad: 'text-[var(--bad)]', muted: 'text-[var(--text-muted)]' }[subTone]
  const accentColor = highlight ? 'var(--bad)' : accent === 'gold' ? 'var(--gold)' : 'var(--accent)'
  return (
    <div
      className="relative rounded-xl border p-4 pt-5 flex flex-col gap-1.5 min-w-0 transition-shadow hover:shadow-[var(--shadow-md)]"
      style={{
        boxShadow: 'var(--shadow-sm)',
        borderColor: highlight ? 'var(--bad)' : 'var(--border)',
        background: highlight ? 'color-mix(in srgb, var(--bad) 6%, var(--panel))' : 'var(--panel)',
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl" style={{ background: accentColor }} />
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs uppercase tracking-wide text-[var(--text-muted)] flex items-center gap-1">
          {label}
          {tooltip && <Info size={12} className="text-[var(--text-muted)] shrink-0" strokeWidth={2} />}
        </span>
        <Icon size={16} strokeWidth={2} className="shrink-0" style={{ color: accentColor }} />
      </div>
      <span className="text-2xl font-semibold text-[var(--text-h)] tabular-nums">{value}</span>
      {sub && <span className={`text-xs ${tone}`}>{sub}</span>}

      {tooltip && showTooltip && (
        <div
          role="tooltip"
          className="pointer-events-none absolute left-1/2 top-full z-30 mt-2 w-60 -translate-x-1/2 rounded-lg px-3 py-2 text-xs leading-snug shadow-lg"
          style={{ background: '#131c56', color: '#ffffff' }}
        >
          {tooltip}
        </div>
      )}
    </div>
  )
}
