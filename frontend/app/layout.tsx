import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NDIS CRM",
  description: "NDIS Plan Management CRM",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#2563eb" />
      </head>
      <body>{children}</body>
    </html>
  );
}
