import type { Metadata, Viewport } from "next";
import { cookies, headers } from "next/headers";

import { pickLang } from "@/lib/i18n";

import "./globals.css";

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
    { media: "(prefers-color-scheme: light)", color: "#f7f8f7" },
    { media: "(prefers-color-scheme: dark)", color: "#141816" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang = pickLang(
    (await cookies()).get("nav_lang")?.value,
    (await headers()).get("accept-language"),
  );
  return (
    <html lang={lang}>
      <body>{children}</body>
    </html>
  );
}
