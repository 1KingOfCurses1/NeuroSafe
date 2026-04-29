import { render, screen } from '@testing-library/react'
import { DangerSegmentList } from './DangerSegmentList'
import type { DangerSegment } from '../types'

const makeSegment = (overrides: Partial<DangerSegment> = {}): DangerSegment => ({
  start_time: 10,
  end_time: 15,
  peak_time: 12,
  roi: 'V1',
  activation_level: 2.5,
  threshold: 2.0,
  severity: 'high',
  reason: 'Activation exceeded threshold.',
  ...overrides,
})

describe('DangerSegmentList', () => {
  it('shows empty state when no segments', () => {
    render(<DangerSegmentList segments={[]} />)
    expect(screen.getByText(/no danger segments detected/i)).toBeInTheDocument()
  })

  it('renders a segment with ROI label', () => {
    render(<DangerSegmentList segments={[makeSegment({ roi: 'MT+' })]} />)
    expect(screen.getByText('MT+')).toBeInTheDocument()
  })

  it('renders severity badge in uppercase', () => {
    render(<DangerSegmentList segments={[makeSegment({ severity: 'critical' })]} />)
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
  })

  it('renders multiple segments', () => {
    const segments = [
      makeSegment({ roi: 'V1', severity: 'high' }),
      makeSegment({ roi: 'V2', severity: 'medium', start_time: 20, end_time: 25, peak_time: 22 }),
    ]
    render(<DangerSegmentList segments={segments} />)
    expect(screen.getByText('V1')).toBeInTheDocument()
    expect(screen.getByText('V2')).toBeInTheDocument()
  })

  it('formats timestamps correctly (m:ss.s)', () => {
    render(<DangerSegmentList segments={[makeSegment({ start_time: 65, end_time: 70, peak_time: 67 })]} />)
    expect(screen.getByText(/1:05\.0/)).toBeInTheDocument()
  })
})
