import type { ReactNode } from 'react'

export function Card({ title, subtitle, children }: { title?: string; subtitle?: string; children: ReactNode }) {
  return (
    <section
      className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-5 flex flex-col gap-2"
      style={{ boxShadow: 'var(--shadow-sm)' }}
    >
      {title && <h2 className="text-lg font-medium text-[var(--text-h)]">{title}</h2>}
      {subtitle && <p className="text-sm text-[var(--text-muted)] -mt-1">{subtitle}</p>}
      {children}
    </section>
  )
}
