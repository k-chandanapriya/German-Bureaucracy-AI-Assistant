import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import Nav from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Amtspost – understand your German letters",
  description:
    "Photograph an official German letter. Get a plain-English explanation, the real deadline, a calendar reminder and a German reply.",
};

/** Thin vertical blueprint lines behind every page. */
function GridLines() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10">
      <div className="mx-auto grid h-full max-w-6xl grid-cols-4 border-x border-line">
        {[0, 1, 2].map((i) => (
          <div key={i} className="border-r border-line" />
        ))}
      </div>
    </div>
  );
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <GridLines />
        <Suspense fallback={<div className="h-14 border-b border-line" />}>
          <Nav />
        </Suspense>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6">{children}</main>
        <footer className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-5 sm:px-6">
            <span className="mono-label">Amtspost · German Bureaucracy Assistant</span>
            <span className="mono-label normal-case tracking-normal">
              Information, not legal or tax advice. Always check against your original letter.
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
