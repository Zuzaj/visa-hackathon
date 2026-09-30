import { BadgeCheck, Fingerprint } from 'lucide-react'
import { formatMonth, pct, SERIES_LABEL, type TopDestination } from '../lib/api'

interface Props {
  regionName: string
  destination: TopDestination
}

export function WantedPoster({ regionName, destination }: Props) {
  const destinationLabel = SERIES_LABEL[destination.group] ?? destination.group

  return (
    <div
      className="relative mx-auto max-w-sm rounded-sm p-6 flex flex-col items-center gap-4 text-center"
      style={{
        background: '#f4ecd8',
        border: '3px double #4a3a20',
        boxShadow: '0 12px 30px rgba(19, 28, 86, 0.18)',
        transform: 'rotate(-1deg)',
        fontFamily: 'Georgia, "Times New Roman", serif',
        color: '#3a2f1c',
      }}
    >
      <p className="text-xs tracking-[0.3em]">HAVE YOU SEEN THIS SHOPPER?</p>
      <h2 className="text-5xl font-black tracking-wide leading-none" style={{ color: '#7a1f1f' }}>
        WANTED
      </h2>
      <p className="text-xs tracking-[0.2em]">FOR CUTTING LIDL SPEND IN {regionName.toUpperCase()}</p>

      <div
        className="w-28 h-28 flex items-center justify-center rounded-sm"
        style={{ background: '#ddd3ba', border: '2px solid #4a3a20' }}
      >
        <Fingerprint size={64} strokeWidth={1.2} color="#3a2f1c" />
      </div>

      <div className="w-full flex flex-col gap-1.5 text-sm text-left">
        <p><span className="font-bold">ALIAS:</span> The {regionName} Grocery Wallet</p>
        <p>
          <span className="font-bold">LAST SEEN:</span> Lidl, {regionName} — {formatMonth(destination.month_from)}
        </p>
        <p>
          <span className="font-bold">NOW SPOTTED AT:</span> {destinationLabel}, {regionName}
        </p>
        <p>
          <span className="font-bold">CASE SIZE:</span> {destination.n_cards.toLocaleString()} shoppers ·{' '}
          {pct(destination.share_of_decliners)} of the {destination.n_cards_declining_total.toLocaleString()} who cut Lidl spend
        </p>
        <p><span className="font-bold">REWARD:</span> a win-back offer before the switch sticks</p>
      </div>

      <div
        className="w-full flex items-center justify-center gap-1.5 pt-3 mt-1 text-xs tracking-wide"
        style={{ borderTop: '1px dashed #4a3a20' }}
      >
        <BadgeCheck size={14} color="#1434cb" />
        <span>
          IDENTIFIED BY <span className="wordmark" style={{ color: '#1434cb' }}>VISA</span> NETWORK DATA — the
          piece Lidl's own data can't see
        </span>
      </div>
    </div>
  )
}
