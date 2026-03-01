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
      <body>{children}</body>
    </html>
  );
}
