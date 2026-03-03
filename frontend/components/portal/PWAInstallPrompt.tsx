'use client'

import { useEffect, useState } from 'react'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: string }>
}

export default function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(true) // start hidden; show only after check

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (localStorage.getItem('pwa-install-dismissed')) return

    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setDismissed(false)
    }

    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (dismissed || !deferredPrompt) return null

  async function handleInstall() {
    if (!deferredPrompt) return
    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted' || outcome === 'dismissed') {
      localStorage.setItem('pwa-install-dismissed', '1')
      setDismissed(true)
    }
  }

  function handleDismiss() {
    localStorage.setItem('pwa-install-dismissed', '1')
    setDismissed(true)
  }

  return (
    <div
      role="region"
      aria-label="Install My NDIS app"
      className="fixed bottom-20 left-4 right-4 z-50 flex items-center justify-between rounded-xl bg-blue-600 px-4 py-3 text-white shadow-lg"
    >
      <div className="flex min-w-0 flex-col">
        <span className="text-sm font-semibold">Install My NDIS</span>
        <span className="text-xs text-blue-100">Add to your home screen for quick access</span>
      </div>
      <div className="ml-3 flex gap-2 flex-shrink-0">
        <button
          onClick={handleInstall}
          className="rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-blue-600 focus:outline-none focus:ring-2 focus:ring-white"
        >
          Install
        </button>
        <button
          onClick={handleDismiss}
          aria-label="Dismiss install prompt"
          className="rounded-lg px-2 py-1.5 text-xs font-semibold text-blue-100 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
