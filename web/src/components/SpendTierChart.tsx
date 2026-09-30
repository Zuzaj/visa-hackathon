import ReactECharts from 'echarts-for-react'
import { LIDL_SEGMENT_LABEL, LIDL_SEGMENT_ORDER, pct, SPEND_TIER_LABEL, type CustomerProfileRow } from '../lib/api'
import { SPEND_TIER_COLOR } from '../lib/palette'

const TIERS = ['low', 'medium', 'high'] as const

export function SpendTierChart({ profile }: { profile: CustomerProfileRow[] }) {
  const rows = profile.filter((r) => r.dimension === 'spend_tier')
  const segments = LIDL_SEGMENT_ORDER.filter((seg) => rows.some((r) => r.segment === seg))

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
      data: TIERS.map((t) => SPEND_TIER_LABEL[t]),
      top: 0,
      textStyle: { color: '#3b4256' },
    },
    xAxis: {
      type: 'value',
      max: 1,
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
    series: TIERS.map((tier) => ({
      name: SPEND_TIER_LABEL[tier],
      type: 'bar',
      stack: 'total',
      barWidth: '55%',
      itemStyle: { color: SPEND_TIER_COLOR[tier] },
      data: segments.map((seg) => rows.find((r) => r.segment === seg && r.value === tier)?.share ?? 0),
    })),
  }

  return <ReactECharts option={option} style={{ height: Math.max(160, segments.length * 50) }} notMerge />
}
