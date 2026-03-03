import type { Metadata } from 'next'
import Link from 'next/link'
import PWAInstallPrompt from '@/components/portal/PWAInstallPrompt'

export const metadata: Metadata = {
  title: 'My NDIS Portal',
  description: 'View your NDIS budget and invoices',
}

const navItems = [
  { href: '/portal', label: 'Home', icon: '🏠' },
  { href: '/portal/budget', label: 'Budget', icon: '💰' },
  { href: '/portal/invoices', label: 'Invoices', icon: '📄' },
  { href: '/portal/profile', label: 'Profile', icon: '👤' },
]

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top header */}
      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-lg items-center justify-between px-4 py-3">
          <span className="text-lg font-bold text-blue-600">My NDIS</span>
          <Link
            href="/api/auth/logout"
            className="rounded-md px-3 py-1 text-sm text-gray-500 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Sign out
          </Link>
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-lg px-4 pb-24 pt-6">{children}</main>

      {/* Bottom navigation */}
      <nav
        aria-label="Portal navigation"
        className="fixed bottom-0 left-0 right-0 z-40 border-t border-gray-200 bg-white"
      >
        <div className="mx-auto flex max-w-lg">
          {navItems.map(({ href, label, icon }) => (
            <Link
              key={href}
              href={href}
              className="flex flex-1 flex-col items-center py-2 text-xs text-gray-500 hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
            >
              <span className="text-xl" aria-hidden="true">
                {icon}
              </span>
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </nav>

      <PWAInstallPrompt />
    </div>
  )
}
