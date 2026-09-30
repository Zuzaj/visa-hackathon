import { ArrowRight } from 'lucide-react'

interface Props {
  label: string
  onClick: () => void
}

// Matches Home.tsx's primary CTA (gold fill, dark text) so the same "this is
// the next thing to press" affordance carries through from the landing page
// into the guided tab-by-tab story.
export function JourneyButton({ label, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className="self-center inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold transition-opacity hover:opacity-90"
      style={{ background: 'var(--gold)', color: '#3a2f1c', boxShadow: 'var(--shadow-sm)' }}
    >
      {label}
      <ArrowRight size={16} />
    </button>
  )
}
