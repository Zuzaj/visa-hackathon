import { ArrowLeft } from 'lucide-react'

interface Props {
  city: string
  subtitle: string
  onBack?: () => void
  title?: string
}

export function Hero({ city, subtitle, onBack, title }: Props) {
  return (
    <div style={{ background: `linear-gradient(135deg, var(--hero-from), var(--hero-to))` }}>
      <div className="max-w-5xl mx-auto px-6 md:px-8 pt-8 pb-14 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="wordmark text-white text-xl leading-none">VISA</span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-white/60 border-l border-white/30 pl-2">
              Wallet Radar
            </span>
          </div>
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-1 text-xs text-white/70 hover:text-white transition-colors"
            >
              <ArrowLeft size={14} /> Change market
            </button>
          )}
        </div>
        <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
          {title ?? `Lidl ${city} — customer wallet intelligence`}
        </h1>
        <p className="text-sm md:text-base text-white/75 max-w-2xl">{subtitle}</p>
      </div>

      {/* gold accent line */}
      <div className="h-1.5 w-full" style={{ background: 'var(--gold)' }} />
    </div>
  )
}
