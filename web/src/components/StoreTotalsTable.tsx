import { formatNumber, SERIES_LABEL, type WalletShareRow } from '../lib/api'
import { SERIES_COLOR } from '../lib/palette'

interface Props {
  data: WalletShareRow[]
  month: number
  groupCounts: Record<string, number>
}

export function StoreTotalsTable({ data, month, groupCounts }: Props) {
  const rows = data.filter((d) => d.month === month).sort((a, b) => (b.total_spend ?? 0) - (a.total_spend ?? 0))

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-[var(--text-muted)] border-b border-[var(--border)]">
            <th className="py-2 font-normal">Where</th>
            <th className="py-2 font-normal text-right">Stores</th>
            <th className="py-2 font-normal text-right">Total spend</th>
            <th className="py-2 font-normal text-right">Customers</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.series} className="border-b border-[var(--border)] last:border-0">
              <td className="py-2 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: SERIES_COLOR[r.series] ?? '#5b6270' }} />
                {SERIES_LABEL[r.series] ?? r.series}
              </td>
              <td className="py-2 text-right tabular-nums">{groupCounts[r.series] ?? '—'}</td>
              <td className="py-2 text-right tabular-nums">{formatNumber(r.total_spend)}</td>
              <td className="py-2 text-right tabular-nums">{formatNumber(r.n_customers)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.some((r) => r.total_spend === null) && (
        <p className="text-xs text-[var(--text-muted)] pt-2">
          Some totals are hidden — fewer than the minimum reportable customer count that month.
        </p>
      )}
    </div>
  )
}
