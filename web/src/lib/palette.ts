// Categorical slots (light column) from the validated default palette --
// re-selected for the light surface now that the app uses a white background.
// Fixed order, assigned by identity -- never cycled, never re-ordered by rank.
const SLOT = {
  blue: '#2409d2',
  orange: '#eb6834',
  aqua: '#1baf7a',
  yellow: '#eda100',
  magenta: '#e87ba4',
  green: '#008300',
  violet: '#4a3aa7',
  red: '#ef0d4d',
}

// Keyed by pooled group only ('lidl' | 'discounts' | 'supermarket') --
// individual competitor identities are never a color key in this app.
export const SERIES_COLOR: Record<string, string> = {
  lidl: SLOT.blue,
  discounts: SLOT.red,
  supermarket: SLOT.yellow,
  no_clear_destination: '#9aa1b4', // muted -- not a competing identity
}

// Sequential blue ramp, light -> dark, for magnitude (the overlap matrix, and
// the spend-tier chart below) -- the app's one sequential hue, reused rather
// than introducing a second ramp.
export const SEQUENTIAL_BLUE = [
  '#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec',
  '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281',
]

// Lidl-lifecycle segments -- status-style colors (traffic-light-like), not
// the categorical identity palette above, since these are health states, not
// competing entities. Every value here reuses a hue that already appears
// elsewhere in the app (SLOT.red/yellow already color 'discounts'/'supermarket'
// on the Overview and Spotlight charts; SLOT.blue is the Lidl series and the
// app's own --accent) -- no new hue is introduced for this feature.
// See aggregates_lib.classify_lidl_segment.
export const SEGMENT_STATUS_COLOR: Record<string, string> = {
  loyal: SLOT.green,
  fading: SLOT.yellow,
  drifting: SLOT.blue,
  gone: SLOT.red,
}

// Low -> high, using the same sequential blue ramp as the overlap matrix.
export const SPEND_TIER_COLOR: Record<string, string> = {
  low: SEQUENTIAL_BLUE[1],
  medium: SEQUENTIAL_BLUE[5],
  high: SEQUENTIAL_BLUE[9],
}

// Non-CLASSIC card types -- the 4 remaining unused slots from the same fixed
// palette above (blue/yellow/green/red are already spoken for by the series
// and segment colors), so this introduces no new hues either.
export const CARD_TYPE_COLOR: Record<string, string> = {
  INFINITE: SLOT.orange,
  BUSINESS: SLOT.aqua,
  PLATINUM: SLOT.magenta,
  PREMIER: SLOT.violet,
}

export function sequentialColor(share: number): string {
  const idx = Math.min(SEQUENTIAL_BLUE.length - 1, Math.max(0, Math.round(share * (SEQUENTIAL_BLUE.length - 1))))
  return SEQUENTIAL_BLUE[idx]
}
