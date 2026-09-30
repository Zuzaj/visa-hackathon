import ReactECharts from 'echarts-for-react'
import { formatMonth, pct, SERIES_LABEL, type WalletShareRow } from '../lib/api'
import { SERIES_COLOR } from '../lib/palette'

export function WalletShareChart({ data }: { data: WalletShareRow[] }) {
  const months = [...new Set(data.map((d) => d.month))].sort()
  const series = [...new Set(data.map((d) => d.series))]
  // Fixed order: hero first, then the rest as they appear in the palette map.
  series.sort((a, b) => (a === 'lidl' ? -1 : b === 'lidl' ? 1 : 0))

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#3b4256', fontFamily: 'system-ui, sans-serif' },
    grid: { left: 48, right: 16, top: 16, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v: number) => pct(v),
      backgroundColor: '#ffffff',
      borderColor: '#dbe1ee',
      textStyle: { color: '#3b4256' },
    },
    legend: {
      data: series.map((s) => SERIES_LABEL[s] ?? s),
      top: 0,
      textStyle: { color: '#3b4256' },
    },
    xAxis: {
      type: 'category',
      data: months.map(formatMonth),
      axisLine: { lineStyle: { color: '#c3c2b7' } },
      axisLabel: { color: '#898781' },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#898781', formatter: (v: number) => pct(v, 0) },
      splitLine: { lineStyle: { color: '#dbe1ee' } },
    },
    series: series.map((s) => ({
      name: SERIES_LABEL[s] ?? s,
      type: 'line',
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: SERIES_COLOR[s] ?? '#5b6270' },
      data: months.map((m) => data.find((d) => d.month === m && d.series === s)?.share ?? 0),
    })),
  }

  return <ReactECharts option={option} style={{ height: 320 }} notMerge />
}
