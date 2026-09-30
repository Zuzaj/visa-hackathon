import ReactECharts from 'echarts-for-react'
import { pct, SERIES_LABEL, type SwitchSignalRow } from '../lib/api'
import { SERIES_COLOR } from '../lib/palette'

export function SignalBarChart({ data }: { data: SwitchSignalRow[] }) {
  const rows = [...data].sort((a, b) => b.share - a.share)

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#3b4256', fontFamily: 'system-ui, sans-serif' },
    grid: { left: 100, right: 48, top: 8, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (v: number) => pct(v),
      backgroundColor: '#ffffff',
      borderColor: '#dbe1ee',
      textStyle: { color: '#3b4256' },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#898781', formatter: (v: number) => pct(v, 0) },
      splitLine: { lineStyle: { color: '#dbe1ee' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => SERIES_LABEL[r.destination] ?? r.destination),
      axisLine: { lineStyle: { color: '#c3c2b7' } },
      axisLabel: { color: '#3b4256' },
      inverse: true,
    },
    series: [
      {
        type: 'bar',
        barWidth: '60%',
        label: { show: true, position: 'right', formatter: (p: { value: number }) => pct(p.value), color: '#3b4256' },
        itemStyle: {
          color: (p: { name: string }) => {
            const chain = rows.find((r) => (SERIES_LABEL[r.destination] ?? r.destination) === p.name)?.destination
            return chain ? SERIES_COLOR[chain] ?? '#5b6270' : '#5b6270'
          },
        },
        data: rows.map((r) => r.share),
      },
    ],
  }

  return <ReactECharts option={option} style={{ height: Math.max(140, rows.length * 40) }} notMerge />
}
