import { X } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
}

// A lightweight "not built yet" placeholder for CTAs that point at a future
// feature -- lets a button exist in the demo without pretending the feature
// is real.
export function ComingSoonOverlay({ open, onClose }: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6" onClick={onClose}>
      <div
        className="w-full max-w-sm rounded-2xl bg-[var(--panel)] p-6 flex flex-col items-center gap-3 text-center relative"
        style={{ boxShadow: 'var(--shadow-md)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-[var(--text-muted)] hover:text-[var(--text)]"
          aria-label="Close"
        >
          <X size={18} />
        </button>
        <h2 className="text-lg font-semibold text-[var(--text-h)]">Coming soon</h2>
        <p className="text-sm text-[var(--text-muted)]">This deeper breakdown isn't built yet in this proof of concept.</p>
        <button
          onClick={onClose}
          className="mt-1 rounded-lg px-4 py-2 text-sm font-semibold text-white"
          style={{ background: 'var(--accent)' }}
        >
          Got it
        </button>
      </div>
    </div>
  )
}
