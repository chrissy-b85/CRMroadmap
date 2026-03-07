import '@testing-library/jest-dom'
import React from 'react'
import { render, screen } from '@testing-library/react'
import { ParticipantProfileClient } from '@/components/participants/ParticipantProfileClient'
import type { Participant, Plan, AuditLogEntry } from '@/lib/types/participant'

// Mock Next.js Link
jest.mock('next/link', () => {
  const MockLink = ({
    href,
    children,
    ...props
  }: {
    href: string
    children: React.ReactNode
    [key: string]: unknown
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  )
  MockLink.displayName = 'MockLink'
  return MockLink
})

const mockParticipant: Participant = {
  id: 'p1',
  ndis_number: '430123456',
  legal_name: 'Jane Smith',
  preferred_name: 'Janie',
  date_of_birth: '1990-05-15',
  email: 'jane@example.com',
  phone: '0400000000',
  address: '1 Main St, Sydney NSW 2000',
  status: 'active',
  portal_access: true,
  auth0_sub: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockPlan: Plan = {
  id: 'plan1',
  participant_id: 'p1',
  plan_start_date: '2024-07-01',
  plan_end_date: '2025-06-30',
  total_budget: '50000',
  status: 'active',
  support_categories: [
    {
      id: 'sc1',
      ndis_support_category: 'Daily Activities',
      budget_allocated: '30000',
      budget_spent: '15000',
      budget_remaining: '15000',
      utilisation_percent: 50,
      alert_level: null,
    },
  ],
}

const mockAuditLog: AuditLogEntry[] = [
  {
    id: 'a1',
    action: 'Participant created',
    performed_by: 'admin@example.com',
    timestamp: '2024-01-01T10:00:00Z',
    changes: null,
  },
]

describe('ParticipantProfileClient', () => {
  test('renders without crashing with empty plans and audit log', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('Jane Smith')).toBeInTheDocument()
  })

  test('renders participant legal name and NDIS number', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    expect(screen.getByText(/430123456/)).toBeInTheDocument()
  })

  test('renders preferred name when provided', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('(Janie)')).toBeInTheDocument()
  })

  test('renders active status badge', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  test('renders tab navigation', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={mockPlan ? [mockPlan] : []}
        auditLog={mockAuditLog}
      />
    )
    expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Plans' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Audit Log' })).toBeInTheDocument()
  })

  test('shows active plan summary on overview tab', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[mockPlan]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('Current Active Plan')).toBeInTheDocument()
  })

  test('shows empty state when no active plan on overview tab', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('No active plan found.')).toBeInTheDocument()
  })

  test('shows portal access Yes badge when portal_access is true', () => {
    render(
      <ParticipantProfileClient
        participant={mockParticipant}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })

  test('shows portal access No badge when portal_access is false', () => {
    render(
      <ParticipantProfileClient
        participant={{ ...mockParticipant, portal_access: false }}
        plans={[]}
        auditLog={[]}
      />
    )
    expect(screen.getByText('No')).toBeInTheDocument()
  })
})
