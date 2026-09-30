export interface GroupInfo {
  members: string[]
  market_share_pct: number
}

export interface Meta {
  groups: string[]
  group_counts: Record<string, number>
  group_info: Record<string, GroupInfo>
  lidl_market_share_pct: number
  total_market_coverage_pct: number
  hero: string
  k_min: number
  months_covered: number[]
  active_city: string
  planned_cities: string[]
  assumptions: string[]
}

export interface WalletShareRow {
  month: number
  series: string
  share: number
  n_cards: number
  total_spend: number | null
  n_customers: number | null
}

export interface CrossShoppingRow {
  month: number
  segment: string
  n_cards_segment: number
  share: number
  n_cards: number
}

export interface OverlapRow {
  group_a: string
  group_b: string
  share_of_shoppers: number
  n_cards: number
}

export interface Overview {
  kpis: {
    lidl_share_latest?: number
    latest_month?: number
    lidl_share_change?: number
    no_lidl_share?: number
  }
  lifecycle_ready: boolean
  wallet_share: WalletShareRow[]
  cross_shopping: CrossShoppingRow[]
}

export interface SwitchSignalRow {
  month_from: number
  month_to: number
  n_cards_declining_total: number
  destination: string
  n_cards: number
  share: number
}

export interface TopDestination {
  group: string
  n_cards: number
  share_of_decliners: number
  n_cards_declining_total: number
  month_from: number
  month_to: number
}

export interface SwitchRateDetail {
  n_switched: number
  lidl_customers_prior: number
  month_from: number
  month_to: number
}

export interface PoznanResponse {
  city: string
  signal: SwitchSignalRow[]
  top_destination: TopDestination | null
  switch_rate: number | null
  switch_rate_detail: SwitchRateDetail | null
}

export interface CustomerSegmentRow {
  month: number
  segment: string
  n_cards: number
  share: number
}

export interface CustomerProfileRow {
  segment: string
  dimension: 'card_type' | 'spend_tier'
  value: string
  n_cards: number
  share: number
}

export interface SpendTiers {
  low_max: number
  medium_max: number
}

export interface CustomerProfileResponse {
  segments: CustomerSegmentRow[]
  profile: CustomerProfileRow[]
  spend_tiers: SpendTiers | null
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`)
  return res.json()
}

export interface AgentMessage {
  role: 'user' | 'assistant'
  content: string
}

export const api = {
  meta: () => getJSON<Meta>('/api/meta'),
  overview: () => getJSON<Overview>('/api/overview'),
  overlap: (month: number) => getJSON<OverlapRow[]>(`/api/overlap?month=${month}`),
  poznan: (month: number) => getJSON<PoznanResponse>(`/api/poznan?month=${month}`),
  customerProfile: () => getJSON<CustomerProfileResponse>('/api/customer_profile'),
  async agentChat(messages: AgentMessage[], month: number | null): Promise<string> {
    const res = await fetch('/api/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, month }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new Error(body?.detail ?? `/api/agent/chat failed: ${res.status}`)
    }
    const data = (await res.json()) as { reply: string }
    return data.reply
  },
}

export function kpisForMonth(walletShare: WalletShareRow[], month: number, hero: string): Overview['kpis'] {
  const months = [...new Set(walletShare.map((r) => r.month))].sort((a, b) => a - b)
  const idx = months.indexOf(month)
  const prior = idx > 0 ? months[idx - 1] : undefined

  const kpis: Overview['kpis'] = { latest_month: month }
  const heroRow = walletShare.find((r) => r.month === month && r.series === hero)
  if (heroRow) kpis.lidl_share_latest = heroRow.share
  if (prior !== undefined) {
    const priorHero = walletShare.find((r) => r.month === prior && r.series === hero)
    if (priorHero && heroRow) kpis.lidl_share_change = heroRow.share - priorHero.share
  }
  // Share of THIS month's active grocery shoppers with zero Lidl spend this
  // month -- single-month, derived from the same cohort wallet_share uses.
  if (heroRow && heroRow.n_customers != null && heroRow.n_cards) {
    kpis.no_lidl_share = 1 - heroRow.n_customers / heroRow.n_cards
  }
  return kpis
}

export function formatMonth(m: number): string {
  const s = String(m)
  const year = s.slice(0, 4)
  const month = s.slice(4, 6)
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${names[Number(month) - 1]} ${year}`
}

export function pct(x: number | undefined, digits = 1): string {
  if (x === undefined || Number.isNaN(x)) return '—'
  return `${(x * 100).toFixed(digits)}%`
}

export function pctPoint(x: number | undefined, digits = 1): string {
  if (x === undefined || Number.isNaN(x)) return '—'
  const sign = x > 0 ? '+' : ''
  return `${sign}${(x * 100).toFixed(digits)} pp`
}

export function formatNumber(x: number | null | undefined): string {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 0 }).format(x)
}

// Only pooled groups -- individual competitor names must never be a label
// option anywhere in this app. See config.yaml's chains.pooled_groups.
export const SERIES_LABEL: Record<string, string> = {
  lidl: 'Lidl',
  discounts: 'Discount chains',
  supermarket: 'Supermarket chains',
  // Not a competitor group -- decliners where neither group showed a clear
  // net gain (spend just shrank, or both groups were flat/down too).
  no_clear_destination: 'No clear destination',
}

// Fixed "healthy -> at-risk -> gone" order, see aggregates_lib.classify_lidl_segment.
export const LIDL_SEGMENT_ORDER = ['loyal', 'fading', 'drifting', 'gone'] as const

export const LIDL_SEGMENT_LABEL: Record<string, string> = {
  loyal: 'Loyal',
  fading: 'Fading',
  drifting: 'Drifting',
  gone: 'Gone',
}

export const LIDL_SEGMENT_DESCRIPTION: Record<string, string> = {
  loyal: 'Bought at Lidl every month loaded, with no declining trend.',
  fading: "Still buying at Lidl this month, but this month's spend is part of a consistent month-over-month decline.",
  drifting: 'Bought at Lidl this month, but with gaps in between (or too new to classify) and no consistent decline.',
  gone: 'Bought at Lidl at some point, but not this month.',
}

export const SPEND_TIER_LABEL: Record<string, string> = {
  low: 'Low spend',
  medium: 'Medium spend',
  high: 'High spend',
}

// Non-CLASSIC card types, fixed display order. CLASSIC itself is deliberately
// excluded from this list -- it's the ~90%+ baseline, shown as its complement
// ("premium share") rather than as its own bar.
export const PREMIUM_CARD_TYPE_ORDER = ['INFINITE', 'BUSINESS', 'PLATINUM', 'PREMIER'] as const

export const CARD_TYPE_LABEL: Record<string, string> = {
  INFINITE: 'Infinite',
  BUSINESS: 'Business',
  PLATINUM: 'Platinum',
  PREMIER: 'Premier',
}
