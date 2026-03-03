import '@testing-library/jest-dom'
import React from 'react'
import { render, screen } from '@testing-library/react'
import OCRConfidenceBar from '@/components/invoices/OCRConfidenceBar'

describe('OCRConfidenceBar', () => {
  test('renders green bar for high confidence (>= 0.9)', () => {
    const { container } = render(<OCRConfidenceBar confidence={0.95} />)
    const fill = container.querySelector('.bg-green-500')
    expect(fill).toBeInTheDocument()
    expect(screen.getByText('95%')).toBeInTheDocument()
  })

  test('renders amber/yellow bar for medium confidence (0.75 – 0.89)', () => {
    const { container } = render(<OCRConfidenceBar confidence={0.82} />)
    const fill = container.querySelector('.bg-yellow-500')
    expect(fill).toBeInTheDocument()
    expect(screen.getByText('82%')).toBeInTheDocument()
  })

  test('renders red bar for low confidence (< 0.75)', () => {
    const { container } = render(<OCRConfidenceBar confidence={0.6} />)
    const fill = container.querySelector('.bg-red-500')
    expect(fill).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  test('renders N/A when confidence is null', () => {
    render(<OCRConfidenceBar confidence={null} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  test('includes a screen-reader-only label', () => {
    render(<OCRConfidenceBar confidence={0.92} />)
    expect(screen.getByText('High confidence')).toBeInTheDocument()
  })
})
