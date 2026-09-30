import ReactECharts from 'echarts-for-react'
import {
  CARD_TYPE_LABEL,
  LIDL_SEGMENT_LABEL,
  LIDL_SEGMENT_ORDER,
  PREMIUM_CARD_TYPE_ORDER,
  pct,
  type CustomerProfileRow,
} from '../lib/api'
import { CARD_TYPE_COLOR } from '../lib/palette'

/** Individual non-CLASSIC card types, stacked per segment. Excludes "gone" --
 * card type at the moment a customer left isn't the actionable signal here;
 * the loyal/fading/drifting segments are, since they're still reachable.
 * A segment whose premium types are all below k_min shows an empty bar --
 * too few cards to report safely, not "no premium cards" -- see the caption
 * under the chart. */
export function CardTypeChart({ profile }: { profile: CustomerProfileRow[] }) {
  const rows = profile.filter((r) => r.dimension === 'card_type' && r.value !== 'CLASSIC')
  const segments = LIDL_SEGMENT_ORDER.filter((seg) => seg !== 'gone' && profile.some((r) => r.segment === seg))
  const types = PREMIUM_CARD_TYPE_ORDER.filter((t) => rows.some((r) => r.value === t))

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#3b4256', fontFamily: 'system-ui, sans-serif' },
    grid: { left: 90, right: 16, top: 32, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (v: number) => pct(v),
      backgroundColor: '#ffffff',
      borderColor: '#dbe1ee',
      textStyle: { color: '#3b4256' },
    },
    legend: {
      data: types.map((t) => CARD_TYPE_LABEL[t] ?? t),
      top: 0,
      textStyle: { color: '#3b4256' },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#898781', formatter: (v: number) => pct(v, 0) },
      splitLine: { lineStyle: { color: '#dbe1ee' } },
    },
    yAxis: {
      type: 'category',
      data: segments.map((seg) => LIDL_SEGMENT_LABEL[seg] ?? seg),
      axisLine: { lineStyle: { color: '#c3c2b7' } },
      axisLabel: { color: '#3b4256' },
      inverse: true,
    },
    series: types.map((type) => ({
      name: CARD_TYPE_LABEL[type] ?? type,
      type: 'bar',
      stack: 'total',
      barWidth: '55%',
      itemStyle: { color: CARD_TYPE_COLOR[type] },
      data: segments.map((seg) => rows.find((r) => r.segment === seg && r.value === type)?.share ?? 0),
    })),
  }

  return <ReactECharts option={option} style={{ height: Math.max(160, segments.length * 50) }} notMerge />
}
