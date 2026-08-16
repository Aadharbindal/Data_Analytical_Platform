import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers";
import { AppLayoutWrapper } from "@/components/layout/AppLayoutWrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// The primary UI font (globals.css points --font-sans at it). Self-hosted by
// next/font so it ships with the app instead of costing a blocking request to
// a third-party origin before first paint.
// No `weight` list: Inter is a variable font, so next/font serves one file
// covering the whole range. Naming discrete weights makes it fetch static
// instances at URLs that don't exist, and every one 404s.
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://numerate-analytics.vercel.app";
const DESCRIPTION =
  "Upload a spreadsheet and ask questions in plain English. Every number is computed by deterministic code and independently verified before you see it.";

export const metadata: Metadata = {
  // Required for the relative opengraph-image path below to resolve to an
  // absolute URL — crawlers reject relative image references.
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Numerate — Smart Analytics. Better Decisions.",
    template: "%s · Numerate",
  },
  description: DESCRIPTION,
  applicationName: "Numerate",
  openGraph: {
    type: "website",
    siteName: "Numerate",
    title: "Numerate — Smart Analytics. Better Decisions.",
    description: DESCRIPTION,
    url: SITE_URL,
  },
  twitter: {
    card: "summary_large_image",
    title: "Numerate — Smart Analytics. Better Decisions.",
    description: DESCRIPTION,
  },
};

// Resource hints — browser pre-resolves backend DNS before first API call
export const viewport = {
  width: "device-width",
  initialScale: 1,
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="flex h-full min-h-full overflow-hidden bg-background text-foreground font-sans">
        <Providers>
          <AppLayoutWrapper>
            {children}
          </AppLayoutWrapper>
        </Providers>
      </body>
    </html>
  );
}
