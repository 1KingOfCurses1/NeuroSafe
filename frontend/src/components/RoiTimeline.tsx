import { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import type { RoiTimeSeries, DangerSegment } from '../types'

interface RoiTimelineProps {
  timeseries: RoiTimeSeries
  dangerSegments: DangerSegment[]
}

const ROI_KEYS = ['V1', 'V2', 'V3', 'V4', 'MT+'] as const
const ROI_COLORS: Record<string, string> = {
  V1: '#3b82f6',
  V2: '#8b5cf6',
  V3: '#10b981',
  V4: '#f59e0b',
  'MT+': '#ef4444',
}
const THRESHOLD = 2.0
const MARGIN = { top: 16, right: 16, bottom: 36, left: 44 }

export function RoiTimeline({ timeseries, dangerSegments }: RoiTimelineProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const svg = svgRef.current
    const container = containerRef.current
    if (!svg || !container) return

    const width = container.clientWidth
    const height = 220
    const innerW = width - MARGIN.left - MARGIN.right
    const innerH = height - MARGIN.top - MARGIN.bottom

    d3.select(svg).selectAll('*').remove()

    const root = d3.select(svg)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`)

    const ts = timeseries.timestamps
    const xScale = d3.scaleLinear().domain([ts[0], ts[ts.length - 1]]).range([0, innerW])

    const allVals = ROI_KEYS.flatMap(k => timeseries[k] as number[])
    const yMax = Math.max(d3.max(allVals) ?? 4, 4)
    const yScale = d3.scaleLinear().domain([0, yMax]).range([innerH, 0])

    // Danger bands
    for (const seg of dangerSegments) {
      root.append('rect')
        .attr('x', xScale(seg.start_time))
        .attr('y', 0)
        .attr('width', xScale(seg.end_time) - xScale(seg.start_time))
        .attr('height', innerH)
        .attr('fill', '#ef444422')
    }

    // Threshold line
    root.append('line')
      .attr('x1', 0).attr('x2', innerW)
      .attr('y1', yScale(THRESHOLD)).attr('y2', yScale(THRESHOLD))
      .attr('stroke', '#64748b')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3')

    // ROI lines
    const line = d3.line<number>()
      .x((_, i) => xScale(ts[i]))
      .y(d => yScale(d))
      .curve(d3.curveMonotoneX)

    for (const key of ROI_KEYS) {
      root.append('path')
        .datum(timeseries[key] as number[])
        .attr('fill', 'none')
        .attr('stroke', ROI_COLORS[key])
        .attr('stroke-width', 1.5)
        .attr('d', line)
    }

    // X axis
    root.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3.axisBottom(xScale)
          .ticks(6)
          .tickFormat(d => `${Number(d).toFixed(0)}s`)
      )
      .call(g => g.select('.domain').attr('stroke', '#334155'))
      .call(g => g.selectAll('.tick line').attr('stroke', '#334155'))
      .call(g => g.selectAll('.tick text').attr('fill', '#94a3b8').attr('font-size', '10'))

    // Y axis
    root.append('g')
      .call(d3.axisLeft(yScale).ticks(4))
      .call(g => g.select('.domain').attr('stroke', '#334155'))
      .call(g => g.selectAll('.tick line').attr('stroke', '#334155'))
      .call(g => g.selectAll('.tick text').attr('fill', '#94a3b8').attr('font-size', '10'))
  }, [timeseries, dangerSegments])

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-4">
        {ROI_KEYS.map(k => (
          <div key={k} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: ROI_COLORS[k] }} />
            <span className="text-xs text-slate-400">{k}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span className="w-6 border-t border-dashed border-slate-500 shrink-0" />
          <span className="text-xs text-slate-500">Threshold</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: '#ef444422', border: '1px solid #ef4444' }} />
          <span className="text-xs text-slate-500">Danger zone</span>
        </div>
      </div>
      <div ref={containerRef} className="w-full">
        <svg ref={svgRef} className="w-full" />
      </div>
    </div>
  )
}
