import { useQuery } from '@tanstack/react-query'
import { PieChart, ShieldCheck, Store, Wallet, X } from 'lucide-react'
import { formatMonth, SERIES_LABEL, api } from '../lib/api'
import { Card } from './Card'
import { KpiTile } from './KpiTile'

interface Props {
  open: boolean
  onClose: () => void
}

// The methodology deep-dive: where the data comes from, how much of the
// market it actually covers, and how customer privacy is protected. Lives
// behind an on-demand button rather than a forced landing step, so it's
// available without interrupting the Spotlight/Overview/Profile/Map flow.
export function WhyTrustUs({ open, onClose }: Props) {
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta, enabled: open })

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 p-6"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl my-8 rounded-2xl bg-[var(--panel)] overflow-hidden"
        style={{ boxShadow: 'var(--shadow-md)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="flex items-center justify-between px-6 py-4 text-white"
          style={{ background: 'var(--accent)' }}
        >
          <h2 className="text-lg font-semibold">Why trust this data</h2>
          <button onClick={onClose} className="opacity-80 hover:opacity-100" aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 flex flex-col gap-5">
          {meta.isLoading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
          {meta.isError && <p className="text-sm text-[var(--bad)]">Could not reach the API.</p>}

          {meta.data && (
            <>
              <Card title="Where this data comes from">
                <p className="text-sm text-[var(--text-muted)]">
                  Every number in this dashboard comes from real Visa card-network transactions at grocery stores in{' '}
                  {meta.data.active_city} — not a survey, panel, or estimate. Each card's monthly spend is tracked at
                  Lidl and its main competitors, so this is the one place Lidl can see where a shopper's wallet goes
                  after they stop spending it at Lidl.
                </p>
              </Card>

              {(() => {
                const months = meta.data.months_covered
                const coverageLabel =
                  months.length > 0 ? `${formatMonth(months[0])} – ${formatMonth(months[months.length - 1])}` : ''
                return (
                  <>
                    <p className="text-xs uppercase tracking-wide text-[var(--text-muted)] -mb-2">
                      Market coverage — full {coverageLabel} dataset, not month-specific
                    </p>
                    <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <KpiTile
                        icon={Wallet}
                        label="Lidl"
                        value={`${meta.data.lidl_market_share_pct}%`}
                        sub={`of ${meta.data.active_city}'s grocery market, ${coverageLabel}`}
                        accent="gold"
                      />
                      {Object.entries(meta.data.group_info).map(([group, info]) => (
                        <KpiTile
                          key={group}
                          icon={Store}
                          label={SERIES_LABEL[group] ?? group}
                          value={`${info.market_share_pct}%`}
                          sub={`${info.members.join(', ')}, and others`}
                        />
                      ))}
                      <KpiTile
                        icon={PieChart}
                        label="Total tracked"
                        value={`${meta.data.total_market_coverage_pct}%`}
                        sub={`of the whole grocery market, ${coverageLabel}`}
                        accent="gold"
                      />
                    </section>
                  </>
                )
              })()}

              <Card title="How customer privacy is protected">
                <ul className="text-sm text-[var(--text-muted)] flex flex-col gap-2 list-disc pl-5">
                  <li>
                    Every figure is aggregated across at least {meta.data.k_min} distinct cards — anything smaller is
                    suppressed automatically rather than shown as a misleadingly precise small number.
                  </li>
                  <li>
                    Individual competitor chains are never shown on their own. Every competitor number is reported as
                    one of two pooled groups — "discount chains" or "supermarket chains" — never a single named
                    chain's own spend, share, or customer count.
                  </li>
                  <li>No card-level data ever leaves this system — only the aggregates above.</li>
                </ul>
              </Card>

              <div className="flex items-center gap-3 rounded-xl border border-[var(--border)] p-4">
                <ShieldCheck size={20} className="text-[var(--good)] shrink-0" />
                <p className="text-xs text-[var(--text-muted)]">
                  This proof of concept covers {meta.data.active_city} only; the product is designed to scale to any
                  Lidl market.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
