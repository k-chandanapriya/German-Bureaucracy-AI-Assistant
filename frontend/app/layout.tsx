import type { Metadata } from "next";
import { Geist_Mono, Silkscreen } from "next/font/google";
import { Suspense } from "react";
import Nav from "@/components/Nav";
import "./globals.css";

const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin", "latin-ext"] });
const silkscreen = Silkscreen({ variable: "--font-silkscreen", weight: ["400", "700"], subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "Amtspost – understand your German letters",
  description:
    "Photograph an official German letter. Get a plain-English explanation, the real deadline, a calendar reminder and a German reply.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistMono.variable} ${silkscreen.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Suspense fallback={<div className="h-14" />}>
          <Nav />
        </Suspense>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">{children}</main>
        <footer className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-5 text-[11px] text-ink/55 sm:px-6">
            <span className="font-pixel text-[12px] text-ink">Amtspost</span>
            <span>Information, not legal or tax advice. Always check against your original letter.</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
