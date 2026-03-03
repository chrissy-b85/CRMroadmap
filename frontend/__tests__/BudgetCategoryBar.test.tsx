import '@testing-library/jest-dom'
import React from 'react'
import { render, screen } from '@testing-library/react'
import BudgetCategoryBar from '@/components/portal/BudgetCategoryBar'

describe('BudgetCategoryBar', () => {
  test('renders green bar when utilisation is below 75%', () => {
    const { container } = render(
      <BudgetCategoryBar categoryName="Daily Activities" spent={5000} allocated={10000} />
    )
    const bar = container.querySelector('[role="progressbar"] > div')
    expect(bar).not.toBeNull()
    expect(bar!.className).toContain('bg-green-500')
  })

  test('renders amber bar when utilisation is between 75% and 90%', () => {
    const { container } = render(
      <BudgetCategoryBar categoryName="Daily Activities" spent={8000} allocated={10000} />
    )
    const bar = container.querySelector('[role="progressbar"] > div')
    expect(bar).not.toBeNull()
    expect(bar!.className).toContain('bg-amber-400')
  })

  test('renders red bar when utilisation is above 90%', () => {
    const { container } = render(
      <BudgetCategoryBar categoryName="Daily Activities" spent={9500} allocated={10000} />
    )
    const bar = container.querySelector('[role="progressbar"] > div')
    expect(bar).not.toBeNull()
    expect(bar!.className).toContain('bg-red-500')
  })

  test('has correct ARIA attributes on progressbar', () => {
    render(
      <BudgetCategoryBar categoryName="Capacity Building" spent={3000} allocated={10000} />
    )
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toHaveAttribute('aria-valuenow', '30')
    expect(progressbar).toHaveAttribute('aria-valuemin', '0')
    expect(progressbar).toHaveAttribute('aria-valuemax', '100')
    expect(progressbar).toHaveAttribute('aria-label', 'Capacity Building budget usage')
  })
})
