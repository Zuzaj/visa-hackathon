// Reproduces the ArcGIS layer's own month-over-month legend (7 diverging
// bands, red = biggest decrease, dark green = biggest increase) -- not the
// app's own color system, since this legend describes someone else's map.
const BANDS = [
  { label: '< -30%', color: '#e8231f' },
  { label: '-29.99% – -20.00%', color: '#f0821e' },
  { label: '-19.99% – -10.00%', color: '#f0c419' },
  { label: '-9.99% – 10.00%', color: '#a8d94a' },
  { label: '10.01% – 20.00%', color: '#7cb342' },
  { label: '20.01% – 30.00%', color: '#4a7c2b' },
  { label: '> 30%', color: '#2d5016' },
]

export function MapLegend() {
  return (
    <div className="flex flex-col gap-1.5 text-xs text-[var(--text)]">
      <span className="font-medium text-[var(--text-h)]">m/m change</span>
      {BANDS.map((b) => (
        <div key={b.label} className="flex items-center gap-2">
          <span className="w-4 h-4 rounded-sm shrink-0 border border-black/10" style={{ background: b.color }} />
          {b.label}
        </div>
      ))}
    </div>
  )
}
