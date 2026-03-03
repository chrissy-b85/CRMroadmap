'use client'

import { useEffect, useState } from 'react'
import { subscribeToPushNotifications } from '@/lib/api/portal'

type PermissionState = 'default' | 'granted' | 'denied' | 'unsupported'

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? ''

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)))
}

export default function PushNotificationSetup() {
  const [permission, setPermission] = useState<PermissionState>('default')
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (typeof Notification === 'undefined') {
      setPermission('unsupported')
      return
    }
    setPermission(Notification.permission as PermissionState)
  }, [])

  if (
    dismissed ||
    permission === 'granted' ||
    permission === 'denied' ||
    permission === 'unsupported'
  ) {
    return null
  }

  async function handleEnable() {
    setLoading(true)
    setError(null)
    try {
      const result = await Notification.requestPermission()
      setPermission(result as PermissionState)
      if (result !== 'granted') return

      if (!('serviceWorker' in navigator)) return
      const registration = await navigator.serviceWorker.ready

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        ...(VAPID_PUBLIC_KEY
          ? { applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) }
          : {}),
      })

      await subscribeToPushNotifications(subscription)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not enable notifications'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-4 mb-4 rounded-2xl border border-blue-100 bg-blue-50 p-4">
      <p className="mb-1 text-sm font-semibold text-blue-900">
        Get notified about invoices 🔔
      </p>
      <p className="mb-3 text-xs text-blue-700">
        Allow push notifications so we can alert you when a new invoice needs
        your approval.
      </p>
      {error && (
        <p className="mb-2 text-xs text-red-600">{error}</p>
      )}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleEnable}
          disabled={loading}
          className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Setting up…' : 'Enable'}
        </button>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="rounded-xl px-4 py-2 text-sm text-blue-600 hover:bg-blue-100"
        >
          Not now
        </button>
      </div>
    </div>
  )
}
