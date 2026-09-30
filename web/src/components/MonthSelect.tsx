import { formatMonth } from '../lib/api'

interface Props {
  months: number[]
  value: number
  onChange: (month: number) => void
}

export function MonthSelect({ months, value, onChange }: Props) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="text-sm rounded-md border border-[var(--border)] bg-[var(--panel)] text-[var(--text-h)] px-2 py-1"
    >
      {months.map((m) => (
        <option key={m} value={m}>
          {formatMonth(m)}
        </option>
      ))}
    </select>
  )
}
