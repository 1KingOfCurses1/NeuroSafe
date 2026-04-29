import { render, screen } from '@testing-library/react'
import { ProgressBar } from './ProgressBar'

describe('ProgressBar', () => {
  it('renders the progress percentage', () => {
    render(<ProgressBar progress={42} status="processing" message="" />)
    expect(screen.getByText('42%')).toBeInTheDocument()
  })

  it('renders the human-readable stage label', () => {
    render(<ProgressBar progress={60} status="running_model" message="" />)
    expect(screen.getByText('Running TRIBE v2 cortical model')).toBeInTheDocument()
  })

  it('renders the message when provided', () => {
    render(<ProgressBar progress={80} status="scoring_danger" message="Evaluating segments..." />)
    expect(screen.getByText('Evaluating segments...')).toBeInTheDocument()
  })

  it('shows Queued label for queued status', () => {
    render(<ProgressBar progress={0} status="queued" message="" />)
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('shows Complete label when completed', () => {
    render(<ProgressBar progress={100} status="completed" message="" />)
    expect(screen.getByText('Complete')).toBeInTheDocument()
  })

  it('shows Failed label when failed', () => {
    render(<ProgressBar progress={30} status="failed" message="Something went wrong" />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('sets bar width to match progress', () => {
    const { container } = render(<ProgressBar progress={65} status="processing" message="" />)
    const bar = container.querySelector('[style]') as HTMLElement
    expect(bar.style.width).toBe('65%')
  })
})
