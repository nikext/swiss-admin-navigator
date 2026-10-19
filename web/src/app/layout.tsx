import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Instrument_Sans, Source_Serif_4 } from "next/font/google";
import { cookies, headers } from "next/headers";

import { pickLang } from "@/lib/i18n";

import "./globals.css";

// Self-hosted at build time by next/font: the browser never calls Google Fonts.
// Instrument Sans for the UI and answers, Source Serif 4 only for law text,
// IBM Plex Mono for refs, chips and timers (design handoff). Only the UI face is
// preloaded: the serif (~450 KB with its opsz axis and italics) and the mono
// aren't on screen before an answer, and preloading them delayed the first
// text's swap (mobile Lighthouse LCP 5.3 s).
const sans = Instrument_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-instrument",
  display: "swap",
});
const serif = Source_Serif_4({
  subsets: ["latin", "latin-ext"],
  style: ["normal", "italic"],
  axes: ["opsz"],
  variable: "--font-serif",
  preload: false,
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: "500",
  variable: "--font-plex-mono",
  preload: false,
  display: "swap",
});

export const metadata: Metadata = {
  title: "Swiss Admin Navigator",
  description:
    "Unofficial assistant for Swiss federal law with quoted, verified citations. Not legal advice.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#161b1a" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang = pickLang(
    (await cookies()).get("nav_lang")?.value,
    (await headers()).get("accept-language"),
  );
  return (
    <html lang={lang} className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
