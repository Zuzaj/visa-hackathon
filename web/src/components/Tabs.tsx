interface Props {
  tabs: string[]
  active: string
  onChange: (tab: string) => void
}

export function Tabs({ tabs, active, onChange }: Props) {
  return (
    <div className="inline-flex gap-1 p-1 rounded-full bg-[var(--accent-soft)] w-fit">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={
            'px-4 py-1.5 text-sm font-medium rounded-full transition-colors ' +
            (tab === active
              ? 'bg-[var(--accent)] text-white shadow-sm'
              : 'text-[var(--text-muted)] hover:text-[var(--text-h)]')
          }
        >
          {tab}
        </button>
      ))}
    </div>
  )
}
