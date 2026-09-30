import { useQuery } from '@tanstack/react-query'
import {
  Crown,
  ExternalLink,
  Gauge,
  Heart,
  MapPin,
  PieChart,
  Repeat,
  ShieldQuestion,
  ShoppingCart,
  Store,
  TrendingDown,
  UserX,
  Wallet,
} from 'lucide-react'
import { useState } from 'react'
import { Card } from '../components/Card'
import { CardTypeChart } from '../components/CardTypeChart'
import { Hero } from '../components/Hero'
import { JourneyButton } from '../components/JourneyButton'
import { KpiTile } from '../components/KpiTile'
import { MarketSpecialist } from '../components/MarketSpecialist'
import { MonthlyChoroplethMap } from '../components/MonthlyChoroplethMap'
import { MonthSelect } from '../components/MonthSelect'
import { OverlapMatrix } from '../components/OverlapMatrix'
import { SegmentBarChart } from '../components/SegmentBarChart'
import { SignalBarChart } from '../components/SignalBarChart'
import { SoWhat } from '../components/SoWhat'
import { SpendTierChart } from '../components/SpendTierChart'
import { StoreTotalsTable } from '../components/StoreTotalsTable'
import { Tabs } from '../components/Tabs'
import { WalletShareBarChart } from '../components/WalletShareBarChart'
import { WalletShareChart } from '../components/WalletShareChart'
import { WantedPoster } from '../components/WantedPoster'
import { WhyTrustUs } from '../components/WhyTrustUs'
import {
  api,
  formatMonth,
  kpisForMonth,
  LIDL_SEGMENT_DESCRIPTION,
  LIDL_SEGMENT_LABEL,
  LIDL_SEGMENT_ORDER,
  pct,
  pctPoint,
  SERIES_LABEL,
} from '../lib/api'

// Order doubles as the guided story: hook -> where it went -> who it costs -> map.
const TABS = ['Spotlight', 'Overview', 'Profile', 'Map'] as const
type Tab = (typeof TABS)[number]

const SEGMENT_ICON = { loyal: Heart, fading: TrendingDown, drifting: Repeat, gone: UserX } as const

export function Overview({ onBack }: { onBack: () => void }) {
  const [tab, setTab] = useState<Tab>('Spotlight')
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null)
  const [trustOpen, setTrustOpen] = useState(false)
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta })
  const overview = useQuery({ queryKey: ['overview'], queryFn: api.overview })

  // Falls back to 0 only until meta loads; the overlap/poznan queries below
  // are `enabled` on meta being ready, so they never actually fire with it.
  const month = selectedMonth ?? meta.data?.months_covered.at(-1) ?? 0

  const overlap = useQuery({
    queryKey: ['overlap', month],
    queryFn: () => api.overlap(month),
    enabled: !!meta.data,
  })
  const poznan = useQuery({
    queryKey: ['poznan', month],
    queryFn: () => api.poznan(month),
    enabled: !!meta.data,
  })
  // Not month-selectable: a card's segment is defined by its whole trajectory
  // across every loaded month, not a single snapshot.
  const profile = useQuery({ queryKey: ['customerProfile'], queryFn: api.customerProfile, enabled: !!meta.data })

  if (meta.isLoading || overview.isLoading) {
    return <p className="text-[var(--text-muted)] p-8">Loading…</p>
  }
  if (meta.isError || overview.isError || !overview.data || !meta.data) {
    return (
      <p className="text-[var(--bad)] p-8">
        Could not reach the API. Is it running on http://localhost:8000?
      </p>
    )
  }

  const monthsCovered = meta.data.months_covered
  const kpis = kpisForMonth(overview.data.wallet_share, month, meta.data.hero)
  // Flag the wallet-share KPI itself, not just its sub-line, once the drop
  // is big enough to matter for a director skimming the page.
  const bigShareDrop = kpis.lidl_share_change !== undefined && kpis.lidl_share_change <= -0.02
  const coverageLabel =
    monthsCovered.length > 0
      ? `${formatMonth(monthsCovered[0])} – ${formatMonth(monthsCovered[monthsCovered.length - 1])}`
      : ''
  const lidlCustomersAt = (m: number) =>
    overview.data.wallet_share.find((r) => r.month === m && r.series === meta.data.hero)?.n_customers ?? null

  return (
    <div className="min-h-full flex flex-col">
      <Hero
        city={meta.data.active_city}
        subtitle={`Proof of concept for ${meta.data.active_city} · card-network view of how Lidl's regular shoppers split their grocery wallet between Lidl, discount chains, and supermarkets · ${coverageLabel}`}
        onBack={onBack}
      />

      <div className="max-w-5xl mx-auto w-full px-6 md:px-8 pt-6 pb-10 flex flex-col gap-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <Tabs tabs={[...TABS]} active={tab} onChange={(t) => setTab(t as Tab)} />
          {tab !== 'Profile' && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--text-muted)]">Showing figures for</span>
              <MonthSelect months={monthsCovered} value={month} onChange={setSelectedMonth} />
            </div>
          )}
        </div>

        {tab === 'Overview' && (
          <div className="flex flex-col gap-6">
            <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <KpiTile
                icon={Wallet}
                label={`Lidl wallet share (${kpis.latest_month ? formatMonth(kpis.latest_month) : '—'})`}
                value={pct(kpis.lidl_share_latest)}
                sub={kpis.lidl_share_change !== undefined ? `${pctPoint(kpis.lidl_share_change)} vs prior month` : undefined}
                subTone={kpis.lidl_share_change !== undefined && kpis.lidl_share_change >= 0 ? 'good' : 'bad'}
                highlight={bigShareDrop}
                tooltip="Lidl's total spend this month divided by total spend across all tracked chains this month."
              />
              <KpiTile
                icon={ShoppingCart}
                label="Shoppers with no Lidl spend"
                value={pct(kpis.no_lidl_share)}
                sub="of grocery shoppers, this month"
                tooltip="Of this month's active grocery shoppers (spent at any tracked chain), the share with zero Lidl transactions this month."
              />
              {poznan.data?.switch_rate != null && poznan.data.switch_rate_detail ? (
                <KpiTile
                  icon={Gauge}
                  label="Switch rate"
                  value={pct(poznan.data.switch_rate)}
                  sub={`${poznan.data.switch_rate_detail.n_switched.toLocaleString()} of ${poznan.data.switch_rate_detail.lidl_customers_prior.toLocaleString()} prior Lidl customers`}
                  subTone="bad"
                  tooltip={`Of the ${poznan.data.switch_rate_detail.lidl_customers_prior.toLocaleString()} cards that were Lidl customers in ${formatMonth(poznan.data.switch_rate_detail.month_from)}, the share with zero Lidl spend in ${formatMonth(poznan.data.switch_rate_detail.month_to)}.`}
                />
              ) : (
                <KpiTile
                  icon={Gauge}
                  label="Switch rate"
                  value="—"
                  sub="needs a prior month to compare"
                  subTone="muted"
                  tooltip="Share of last month's Lidl customers with zero Lidl spend this month. Not enough history yet, or too few switchers to report safely."
                />
              )}
            </section>

            {poznan.data?.top_destination && (
              <>
                <Card
                  title={`Where the cut Lidl spend went — ${formatMonth(month)}`}
                  subtitle="Among shoppers whose Lidl spend fell month over month, which type of chain picked up the most of it."
                >
                  <SignalBarChart data={poznan.data.signal} />
                </Card>

                <SoWhat
                  insight={`Lidl only sees these shoppers disappear. Visa's network data shows ${poznan.data.top_destination.n_cards.toLocaleString()} of them are already shopping ${SERIES_LABEL[poznan.data.top_destination.group] ?? poznan.data.top_destination.group} in ${poznan.data.city} instead.`}
                  action={`Launch a targeted win-back offer for ${poznan.data.city} shoppers before the switch becomes permanent.`}
                />
              </>
            )}

            <Card title="Wallet share over time">
              <WalletShareChart data={overview.data.wallet_share} />
            </Card>

            <Card title={`Wallet share — ${formatMonth(month)}`}>
              <WalletShareBarChart data={overview.data.wallet_share} month={month} />
            </Card>

            <Card
              title={`Store totals — ${formatMonth(month)}`}
              subtitle="Total spend and distinct customers per group, this month."
            >
              <StoreTotalsTable data={overview.data.wallet_share} month={month} groupCounts={meta.data.group_counts} />
            </Card>

            {overlap.data && (
              <Card
                title={`Who else Lidl's shoppers buy from — ${formatMonth(month)}`}
                subtitle="Of each group's shoppers (rows), the share who also shop the other group (columns)."
              >
                <OverlapMatrix data={overlap.data} />
              </Card>
            )}

            <SoWhat
              insight={
                kpis.lidl_share_change !== undefined
                  ? `Lidl's wallet share ${kpis.lidl_share_change >= 0 ? 'rose' : 'fell'} ${pctPoint(kpis.lidl_share_change)} month over month, and ${pct(kpis.no_lidl_share)} of shoppers still buy no groceries at Lidl at all.`
                  : `${pct(kpis.no_lidl_share)} of shoppers buy no groceries at Lidl at all this month.`
              }
              action="Prioritize win-back offers toward shoppers who cross-shop Lidl's closest competitor group, once enough history exists to target them individually."
            />

            <JourneyButton label="See who this is costing" onClick={() => setTab('Profile')} />
          </div>
        )}

        {tab === 'Spotlight' && poznan.data && (
          <div className="flex flex-col gap-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-[var(--text-muted)] mb-2">
                Market coverage — full {coverageLabel} dataset, not month-specific
              </p>
              <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <KpiTile
                  icon={PieChart}
                  label="Tracked by this dashboard"
                  value={`${meta.data.total_market_coverage_pct}%`}
                  sub={`of ${meta.data.active_city}'s grocery market, ${coverageLabel}`}
                  accent="gold"
                  tooltip={`Share of all grocery spend in the city (any store, tracked or not) captured by Lidl plus the two competitor groups below, aggregated across the whole ${coverageLabel} dataset -- not a single month. See 'Why trust us?' for the full breakdown.`}
                />
                {Object.entries(meta.data.group_info).map(([group, info]) => (
                  <KpiTile
                    key={group}
                    icon={Store}
                    label={SERIES_LABEL[group] ?? group}
                    value={`${info.market_share_pct}%`}
                    sub={info.members.join(', ')}
                    tooltip={`${SERIES_LABEL[group] ?? group} include ${info.members.join(', ')} — ${info.market_share_pct}% of ${meta.data.active_city}'s grocery market across the whole ${coverageLabel} dataset, not a single month.`}
                  />
                ))}
              </section>
            </div>

            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <KpiTile
                icon={Wallet}
                label={`Lidl share in ${poznan.data.city}`}
                value={pct(kpis.lidl_share_latest)}
                sub={kpis.lidl_share_change !== undefined ? `${pctPoint(kpis.lidl_share_change)} vs prior month` : undefined}
                subTone={kpis.lidl_share_change !== undefined && kpis.lidl_share_change >= 0 ? 'good' : 'bad'}
                highlight={bigShareDrop}
                tooltip="Lidl's total spend this month divided by total spend across all tracked chains this month."
              />
              {poznan.data.top_destination && (
                <>
                  {(() => {
                    const priorLidlCustomers = lidlCustomersAt(poznan.data.top_destination.month_from)
                    const decliningShare = priorLidlCustomers
                      ? poznan.data.top_destination.n_cards_declining_total / priorLidlCustomers
                      : undefined
                    return (
                      <KpiTile
                        icon={MapPin}
                        label="Shoppers cutting Lidl spend"
                        value={pct(decliningShare)}
                        sub={
                          priorLidlCustomers
                            ? `${poznan.data.top_destination.n_cards_declining_total.toLocaleString()} of ${priorLidlCustomers.toLocaleString()} prior Lidl customers`
                            : `${formatMonth(poznan.data.top_destination.month_from)} → ${formatMonth(poznan.data.top_destination.month_to)}`
                        }
                        subTone="muted"
                        tooltip="Of the cards with Lidl spend in the prior month, the share whose Lidl spend was lower (not necessarily zero) this month."
                      />
                    )
                  })()}
                  <KpiTile
                    icon={Crown}
                    label="Where the spend went"
                    value={SERIES_LABEL[poznan.data.top_destination.group] ?? poznan.data.top_destination.group}
                    sub={`${pct(poznan.data.top_destination.share_of_decliners)} of decliners' extra spend`}
                    tooltip="Of shoppers whose Lidl spend fell, the group (discount or supermarket chains) whose combined spend grew the most for the largest share of them."
                  />
                </>
              )}
            </section>

            {poznan.data.top_destination ? (
              <>
                <WantedPoster regionName={poznan.data.city} destination={poznan.data.top_destination} />

                <JourneyButton label="See where you lost & gained" onClick={() => setTab('Overview')} />
              </>
            ) : (
              <div
                className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 text-sm text-[var(--text-muted)]"
                style={{ boxShadow: 'var(--shadow-sm)' }}
              >
                No switch signal for {formatMonth(month)} — either it's the first month in the dataset (no prior
                month to compare against) or too few shoppers cut Lidl spend to report safely.
              </div>
            )}
          </div>
        )}

        {tab === 'Profile' && profile.data && (
          <div className="flex flex-col gap-6">
            <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {profile.data.segments.map((s) => {
                const Icon = SEGMENT_ICON[s.segment as keyof typeof SEGMENT_ICON] ?? Wallet
                return (
                  <KpiTile
                    key={s.segment}
                    icon={Icon}
                    label={LIDL_SEGMENT_LABEL[s.segment] ?? s.segment}
                    value={pct(s.share)}
                    sub={`${s.n_cards.toLocaleString()} cards`}
                    subTone={s.segment === 'loyal' ? 'good' : s.segment === 'gone' || s.segment === 'fading' ? 'bad' : 'muted'}
                    tooltip={LIDL_SEGMENT_DESCRIPTION[s.segment]}
                  />
                )
              })}
            </section>

            <Card
              title="Customer segments"
              subtitle={`As of ${formatMonth(monthsCovered[monthsCovered.length - 1])}, based on each card's Lidl activity across all ${monthsCovered.length} loaded months.`}
            >
              <SegmentBarChart data={profile.data.segments} />
            </Card>

            <Card
              title="Premium card mix by segment"
              subtitle="Share of cardholders in each premium card type (CLASSIC, the ~90%+ baseline, is excluded)."
            >
              <CardTypeChart profile={profile.data.profile} />
              {(() => {
                const emptySegments = LIDL_SEGMENT_ORDER.filter(
                  (seg) =>
                    seg !== 'gone' &&
                    profile.data.segments.some((s) => s.segment === seg) &&
                    !profile.data.profile.some((r) => r.segment === seg && r.dimension === 'card_type' && r.value !== 'CLASSIC'),
                )
                if (emptySegments.length === 0) return null
                return (
                  <p className="text-xs text-[var(--text-muted)] pt-2">
                    {emptySegments.map((s) => LIDL_SEGMENT_LABEL[s] ?? s).join(', ')}: too few cards per premium
                    card type to report individually — not necessarily zero.
                  </p>
                )
              })()}
            </Card>

            <Card
              title="Spend tier by segment"
              subtitle={
                profile.data.spend_tiers
                  ? `Based on each card's average transaction value, split into terciles across all classified cards: low up to ${Math.round(profile.data.spend_tiers.low_max)}, medium up to ${Math.round(profile.data.spend_tiers.medium_max)}, high above that.`
                  : 'Based on each card\'s average transaction value, split into terciles across all classified cards.'
              }
            >
              <SpendTierChart profile={profile.data.profile} />
            </Card>

            {(() => {
              const loyalPremium = profile.data.profile.find((p) => p.segment === 'loyal' && p.dimension === 'card_type' && p.value === 'CLASSIC')
              const gonePremium = profile.data.profile.find((p) => p.segment === 'gone' && p.dimension === 'card_type' && p.value === 'CLASSIC')
              const goneLow = profile.data.profile.find((p) => p.segment === 'gone' && p.dimension === 'spend_tier' && p.value === 'low')
              const loyalLow = profile.data.profile.find((p) => p.segment === 'loyal' && p.dimension === 'spend_tier' && p.value === 'low')
              if (!loyalPremium || !gonePremium) return null
              const loyalPremiumShare = 1 - loyalPremium.share
              const gonePremiumShare = 1 - gonePremium.share
              return (
                <SoWhat
                  insight={`Departed customers are ${(gonePremiumShare / Math.max(loyalPremiumShare, 0.001)).toFixed(1)}x more likely to hold a premium card (${pct(gonePremiumShare)}) than loyal customers (${pct(loyalPremiumShare)})${goneLow && loyalLow ? `, and skew toward lower spend (${pct(goneLow.share)} low-tier vs ${pct(loyalLow.share)} among loyal)` : ''}.`}
                  action="Build a dedicated win-back offer for premium-card holders who've gone quiet — they carry more lifetime value than the average departed customer."
                />
              )
            })()}

            <JourneyButton label="See it on the map" onClick={() => setTab('Map')} />
          </div>
        )}

        {tab === 'Map' && (
          <div className="flex flex-col gap-6">
            <Card
              title={`Wallet share change by area — ${formatMonth(month)}`}
              subtitle="Month-over-month change, exported from ArcGIS. Powiat/gmina boundaries around Poznań."
            >
              <MonthlyChoroplethMap month={month} />
              <a
                href="https://immo.maps.arcgis.com/apps/mapviewer/index.html?configurableview=true&webmap=7f18d6df222846be943dbe78f8ff75f1&theme=light&scroll=false&center=17.103735484992647,52.25769292968683&scale=2311162.217155"
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium w-fit"
                style={{ color: 'var(--accent)' }}
              >
                Open in ArcGIS <ExternalLink size={14} />
              </a>
            </Card>

            {/* <Card title={`${meta.data.active_city} — interactive map`} subtitle="Live ArcGIS embed (requires an ArcGIS sign-in for this organization's map).">
              <ArcGisMap
                src="https://immo.maps.arcgis.com/apps/mapviewer/index.html?configurableview=true&webmap=7f18d6df222846be943dbe78f8ff75f1&theme=light&scroll=false&center=17.103735484992647,52.25769292968683&scale=2311162.217155"
                title="Visa_kp"
              />
            </Card> */}

            <JourneyButton label="Restart the story" onClick={() => setTab('Spotlight')} />
          </div>
        )}

        <footer className="text-xs text-[var(--text-muted)] border-t border-[var(--border)] pt-4">
          {meta.data.assumptions.map((a) => (
            <p key={a}>{a}</p>
          ))}
        </footer>
      </div>

      <button
        onClick={() => setTrustOpen(true)}
        className="fixed bottom-24 right-6 z-30 flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold"
        style={{ background: 'var(--gold)', color: '#3a2f1c', boxShadow: 'var(--shadow-md)' }}
      >
        <ShieldQuestion size={16} />
        Why trust us?
      </button>
      <WhyTrustUs open={trustOpen} onClose={() => setTrustOpen(false)} />

      <MarketSpecialist month={selectedMonth ?? monthsCovered.at(-1) ?? null} />
    </div>
  )
}
