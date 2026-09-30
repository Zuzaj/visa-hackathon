import { ImageOff } from 'lucide-react'
import { useState } from 'react'
import { formatMonth } from '../lib/api'
import { MapLegend } from './MapLegend'

// One static export per month from the ArcGIS layer -- drop each file at
// web/public/maps/<YYYYMM>.png to activate it; until the file actually exists,
// the <img>'s onError below swaps in a clear placeholder instead of the
// browser's broken-image icon.
const MAP_PATH_BY_MONTH: Record<number, string> = {
  202501: '/maps/202501.webp',
  202502: '/maps/202502.webp',
  202503: '/maps/202503.webp',
  202504: '/maps/202504.webp',
}

export function MonthlyChoroplethMap({ month }: { month: number }) {
  const [failed, setFailed] = useState(false)
  const src = MAP_PATH_BY_MONTH[month]

  return (
    <div className="flex flex-col sm:flex-row gap-4 items-start">
      <div className="flex-1 min-w-0 w-full rounded-xl overflow-hidden border border-[var(--border)]">
        {src && !failed ? (
          <img
            key={src}
            src={src}
            alt={`Month-over-month change map — ${formatMonth(month)}`}
            className="w-full block"
            onError={() => setFailed(true)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center gap-2 p-12 text-sm text-[var(--text-muted)] bg-[var(--panel)]">
            <ImageOff size={24} />
            No map exported for {formatMonth(month)} yet.
          </div>
        )}
      </div>
      <MapLegend />
    </div>
  )
}
