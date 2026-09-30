import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, Clock } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'

interface Props {
  onEnter: () => void
}

export function Home({ onEnter }: Props) {
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  const [selected, setSelected] = useState<string | null>(null)

  const activeCity = meta.data?.active_city
  const plannedCities = meta.data?.planned_cities ?? []
  const isSelected = selected === activeCity

  return (
    <div
      className="min-h-full flex flex-col items-center justify-center px-6 py-16"
      style={{ background: `linear-gradient(135deg, var(--hero-from), var(--hero-to))` }}
    >
      <div className="flex items-center gap-2 mb-8">
        <span className="wordmark text-white text-2xl leading-none">VISA</span>
        <span className="text-xs uppercase tracking-[0.2em] text-white/60 border-l border-white/30 pl-2">
          Wanted — Client Radar
        </span>
      </div>

      <h1 className="text-4xl md:text-5xl font-semibold text-white tracking-tight text-center max-w-2xl">
        You know your customer.
        <br />
        We know the whole market.
      </h1>
      <p className="text-sm md:text-base text-white/70 text-center max-w-lg mt-4">
        A proof of concept for Lidl Poland, built on Visa's card-network view of the grocery
        wallet. Designed to scale to every market — starting here.
      </p>

      <div className="w-full max-w-2xl mt-12 rounded-xl bg-white/10 backdrop-blur-sm border border-white/15 p-6">
        <p className="text-xs uppercase tracking-[0.2em] text-white/60 mb-4">Choose a market</p>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {activeCity && (
            <button
              onClick={() => setSelected(activeCity)}
              className={
                'rounded-lg p-4 flex flex-col items-start gap-1 text-left transition-colors border-2 ' +
                (isSelected ? 'bg-white' : 'bg-white/5 hover:bg-white/10 border-transparent')
              }
              style={isSelected ? { borderColor: 'var(--gold)' } : undefined}
            >
              <span className={'text-base font-semibold ' + (isSelected ? 'text-[var(--text-h)]' : 'text-white')}>
                {activeCity}
              </span>
              <span
                className="text-xs flex items-center gap-1"
                style={{ color: isSelected ? 'var(--good)' : 'rgba(255,255,255,0.6)' }}
              >
                <CheckCircle2 size={12} /> Live data
              </span>
            </button>
          )}

          {plannedCities.map((city) => (
            <div
              key={city}
              className="rounded-lg p-4 flex flex-col items-start gap-1 border-2 border-transparent bg-white/5 opacity-50 cursor-not-allowed"
            >
              <span className="text-base font-semibold text-white">{city}</span>
              <span className="text-xs flex items-center gap-1 text-white/60">
                <Clock size={12} /> Coming soon
              </span>
            </div>
          ))}
        </div>

        <button
          onClick={onEnter}
          disabled={!isSelected}
          className={
            'mt-6 w-full rounded-lg py-3 flex items-center justify-center gap-2 font-medium transition-opacity ' +
            (isSelected ? 'opacity-100 cursor-pointer' : 'opacity-40 cursor-not-allowed')
          }
          style={{ background: 'var(--gold)', color: '#3a2f1c' }}
        >
          Enter dashboard
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  )
}
