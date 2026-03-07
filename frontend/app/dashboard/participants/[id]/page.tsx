import { notFound } from 'next/navigation'
import {
  getParticipant,
  getParticipantAuditLog,
  getParticipantPlans,
} from '@/lib/api/participants'
import { ParticipantProfileClient } from '@/components/participants/ParticipantProfileClient'

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function ParticipantDetailPage({ params }: PageProps) {
  const { id } = await params

  const [participant, plans, auditLog] = await Promise.all([
    getParticipant(id).catch(() => null),
    getParticipantPlans(id).catch(() => []),
    getParticipantAuditLog(id).catch(() => []),
  ])

  if (!participant) {
    notFound()
  }

  return (
    <ParticipantProfileClient
      participant={participant}
      plans={plans}
      auditLog={auditLog}
    />
  )
}
