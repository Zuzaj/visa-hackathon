import { Lightbulb, MoveRight } from 'lucide-react'

interface Props {
  insight: string
  action: string
}

export function SoWhat({ insight, action }: Props) {
  return (
    <div
      className="rounded-xl border border-[var(--gold)]/50 bg-[var(--gold-soft)] p-4 flex flex-col gap-2"
      style={{ boxShadow: 'var(--shadow-sm)' }}
    >
      <div className="flex items-start gap-2">
        <Lightbulb size={16} className="text-[var(--gold)] mt-0.5 shrink-0" strokeWidth={2} />
        <p className="text-sm text-[var(--text-h)] font-medium">{insight}</p>
      </div>
      <div className="flex items-start gap-2 pl-[24px]">
        <MoveRight size={14} className="text-[var(--accent)] mt-0.5 shrink-0" strokeWidth={2.5} />
        <p className="text-sm text-[var(--accent)] font-medium">{action}</p>
      </div>
    </div>
  )
}
