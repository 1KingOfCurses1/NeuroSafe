import { render, screen } from '@testing-library/react'
import { DangerScoreGauge } from './DangerScoreGauge'

describe('DangerScoreGauge', () => {
  it('renders the score value', () => {
    render(<DangerScoreGauge score={72} severity="high" />)
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  it('renders the /100 label', () => {
    render(<DangerScoreGauge score={45} severity="medium" />)
    expect(screen.getByText('/ 100')).toBeInTheDocument()
  })

  it.each([
    ['low',      'LOW RISK'],
    ['medium',   'MODERATE RISK'],
    ['high',     'HIGH RISK'],
    ['critical', 'CRITICAL RISK'],
  ] as const)('shows correct label for severity=%s', (severity, label) => {
    render(<DangerScoreGauge score={50} severity={severity} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('renders an SVG gauge element', () => {
    const { container } = render(<DangerScoreGauge score={30} severity="low" />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
