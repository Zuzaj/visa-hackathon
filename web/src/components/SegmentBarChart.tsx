import ReactECharts from 'echarts-for-react'
import { LIDL_SEGMENT_LABEL, LIDL_SEGMENT_ORDER, pct, type CustomerSegmentRow } from '../lib/api'
import { SEGMENT_STATUS_COLOR } from '../lib/palette'

export function SegmentBarChart({ data }: { data: CustomerSegmentRow[] }) {
  const rows = LIDL_SEGMENT_ORDER.map((seg) => data.find((r) => r.segment === seg)).filter(
    (r): r is CustomerSegmentRow => !!r,
  )

  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: '#3b4256', fontFamily: 'system-ui, sans-serif' },
    grid: { left: 90, right: 48, top: 8, bottom: 24 },
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
      data: rows.map((r) => LIDL_SEGMENT_LABEL[r.segment] ?? r.segment),
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
          color: (p: { dataIndex: number }) => SEGMENT_STATUS_COLOR[rows[p.dataIndex].segment] ?? '#5b6270',
        },
        data: rows.map((r) => r.share),
      },
    ],
  }

  return <ReactECharts option={option} style={{ height: Math.max(140, rows.length * 44) }} notMerge />
}
