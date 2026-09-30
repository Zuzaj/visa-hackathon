import { pct, SERIES_LABEL, type OverlapRow } from '../lib/api'
import { sequentialColor } from '../lib/palette'

export function OverlapMatrix({ data }: { data: OverlapRow[] }) {
  const groups = [...new Set(data.map((d) => d.group_a))]

  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1 text-sm">
        <thead>
          <tr>
            <th className="text-left text-xs text-[var(--text-muted)] font-normal pr-2">
              also shops at →
            </th>
            {groups.map((g) => (
              <th key={g} className="text-xs text-[var(--text-muted)] font-normal px-2 pb-1">
                {SERIES_LABEL[g] ?? g}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {groups.map((a) => (
            <tr key={a}>
              <th className="text-xs text-[var(--text-h)] font-medium text-right pr-2 whitespace-nowrap">
                {SERIES_LABEL[a] ?? a} shoppers
              </th>
              {groups.map((b) => {
                if (a === b) return <td key={b} className="w-14 h-10 rounded bg-[var(--border)]" />
                const row = data.find((d) => d.group_a === a && d.group_b === b)
                const share = row?.share_of_shoppers ?? 0
                return (
                  <td
                    key={b}
                    title={`${pct(share)} of ${SERIES_LABEL[a] ?? a} shoppers also shop ${SERIES_LABEL[b] ?? b} (n=${row?.n_cards ?? 0})`}
                    className="w-14 h-10 rounded text-center text-xs font-medium tabular-nums"
                    style={{ background: sequentialColor(share), color: share > 0.5 ? '#ffffff' : '#131c56' }}
                  >
                    {pct(share, 0)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
